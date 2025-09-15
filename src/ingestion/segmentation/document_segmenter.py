"""
Financial Document Segmentation System
Segments FinanceBench markdown documents into structured sections with parallel processing.
"""

import os
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import instructor

# Load environment variables
load_dotenv()


class PageRange(BaseModel):
    """Page range for a document section."""
    start: int = Field(..., description="Starting page number")
    end: int = Field(..., description="Ending page number")


class Segment(BaseModel):
    """Document segment with heading, description and page range."""
    heading: str = Field(..., description="The heading or title of the section")
    description: str = Field(..., description="A brief description or summary of the section")
    page_range: PageRange = Field(..., description="Page range for this section")


class DocumentSegmentation(BaseModel):
    """Complete document segmentation result."""
    document_name: str
    total_pages: int
    segments: List[Segment]


class DocumentSegmenter:
    def __init__(self, max_workers: int = 10, chunk_size: int = 60, overlap: int = 0):
        """
        Initialize the document segmenter.

        Args:
            max_workers: Number of parallel workers for processing
            chunk_size: Number of pages per chunk
            overlap: Overlap between chunks (0 to avoid overlaps)
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Set up directories - go up to project root from src/ingestion/segmentation/
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.markdown_dir = self.base_dir / ".finance" / "markdown"
        self.segments_dir = self.base_dir / ".finance" / "segments"
        self.segments_dir.mkdir(parents=True, exist_ok=True)

        # Set up OpenAI client with instructor
        self._setup_client()

    def _setup_client(self):
        """Setup OpenRouter client with instructor for structured output."""
        try:
            # Use OpenRouter API
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required")

            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            self.client = instructor.from_openai(client)
            print("Successfully initialized OpenRouter client with Instructor")
        except Exception as e:
            print(f"Warning: Could not initialize OpenRouter client: {e}")
            self.client = None

    def parse_markdown_pages(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown content and extract pages with their content.

        Args:
            markdown_content: Full markdown document content

        Returns:
            List of page dictionaries with page_number and content
        """
        pages = []

        # Split by page markers
        page_splits = re.split(r'<!-- Page (\d+) -->', markdown_content)

        if len(page_splits) < 2:
            # No page markers found, treat as single page
            return [{"page_number": 1, "content": markdown_content.strip()}]

        # First split is content before any page marker (usually empty)
        for i in range(1, len(page_splits), 2):
            if i + 1 < len(page_splits):
                page_num = int(page_splits[i])
                page_content = page_splits[i + 1].strip()

                if page_content:  # Only add non-empty pages
                    pages.append({
                        "page_number": page_num,
                        "content": page_content
                    })

        return pages

    def create_chunk_text(self, pages: List[Dict[str, Any]], start_idx: int, end_idx: int) -> str:
        """
        Create text chunk with page markers for processing.

        Args:
            pages: List of page dictionaries
            start_idx: Starting page index
            end_idx: Ending page index

        Returns:
            Formatted text chunk with page markers
        """
        chunk_text = ""

        for i in range(start_idx, min(end_idx, len(pages))):
            page = pages[i]
            chunk_text += f"### Page Number: [PG:{page['page_number']}]\n"
            chunk_text += f"{page['content']}\n\n"

        return chunk_text

    def process_chunk(self, chunk_data: Tuple[int, str, int, int, int]) -> List[Dict[str, Any]]:
        """
        Process a single chunk to extract segments.

        Args:
            chunk_data: Tuple of (chunk_index, text_chunk, step, start_page, end_page)

        Returns:
            List of segment dictionaries
        """
        chunk_index, text_chunk, step, start_page, end_page = chunk_data

        if not self.client:
            # Fallback: create basic segments based on content analysis
            return self._fallback_segmentation(text_chunk, start_page, end_page)

        SYSTEM_PROMPT = """
        You are a financial document analysis expert specializing in SEC filings (10-K, 10-Q, 8-K forms).
        Your task is to segment financial documents into logical sections based on standard SEC filing structure.

        Focus on identifying major sections such as:
        - Business Overview/Description
        - Risk Factors
        - Legal Proceedings
        - Management's Discussion and Analysis (MD&A)
        - Financial Statements (Income Statement, Balance Sheet, Cash Flows)
        - Notes to Financial Statements
        - Controls and Procedures
        - Executive Compensation
        - Corporate Governance

        Instructions:
        1. Analyze the document content carefully
        2. Identify logical sections based on headings and content structure
        3. Provide accurate page ranges using the [PG:X] markers
        4. Ensure complete coverage of all pages with no gaps
        5. Create meaningful section titles and descriptions
        """

        USER_PROMPT = f"""
        Segment this financial document section covering pages {start_page} to {end_page}.

        CRITICAL REQUIREMENTS:
        - Account for EVERY SINGLE page from {start_page} to {end_page} with NO GAPS
        - Use CONSECUTIVE page ranges that cover ALL pages
        - DO NOT create overlapping segments - each page should belong to only ONE segment
        - Extract page numbers from "### Page Number: [PG:X]" markers
        - Create segments that together cover pages {start_page} through {end_page} completely
        - If a page has minimal content, include it in the nearest logical section

        <Document>
        {text_chunk}
        </Document>
        """

        try:
            response = self.client.chat.completions.create(
                model="moonshotai/kimi-k2-0905",  # Back to Kimi - proven to work well
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT}
                ],
                response_model=List[Segment],
                max_tokens=8000
            )

            # Convert to dictionary format
            segments = []
            for segment in response:
                segments.append({
                    "heading": segment.heading,
                    "description": segment.description,
                    "page_range": {
                        "start": segment.page_range.start,
                        "end": segment.page_range.end
                    }
                })

            return segments

        except Exception as e:
            print(f"Error processing chunk {chunk_index//10 + 1}: {str(e)}")
            return self._fallback_segmentation(text_chunk, start_page, end_page)

    def _fallback_segmentation(self, text_chunk: str, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """
        Fallback segmentation using rule-based approach.

        Args:
            text_chunk: Text content to segment
            start_page: Starting page number
            end_page: Ending page number

        Returns:
            List of basic segments
        """
        # Extract headers and create basic segments
        headers = re.findall(r'^#+\s+(.+)$', text_chunk, re.MULTILINE)

        if not headers:
            # No headers found, create single segment
            return [{
                "heading": f"Document Section (Pages {start_page}-{end_page})",
                "description": "Document content without clear section headers",
                "page_range": {"start": start_page, "end": end_page}
            }]

        # Create segments based on headers
        segments = []
        pages_per_header = max(1, (end_page - start_page + 1) // len(headers))

        for i, header in enumerate(headers):
            seg_start = start_page + (i * pages_per_header)
            seg_end = min(start_page + ((i + 1) * pages_per_header) - 1, end_page)

            segments.append({
                "heading": header,
                "description": f"Section containing {header}",
                "page_range": {"start": seg_start, "end": seg_end}
            })

        return segments

    def segment_document(self, doc_name: str, force_resegment: bool = False) -> DocumentSegmentation:
        """
        Segment a single markdown document.

        Args:
            doc_name: Document name (e.g., "APPLE_2022_10K")
            force_resegment: If True, re-segment even if cached

        Returns:
            DocumentSegmentation object
        """
        # Check cache first
        cache_file = self.segments_dir / f"{doc_name}_segments.json"

        if not force_resegment and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                segments = [Segment.model_validate(s) for s in cache_data['segments']]
                return DocumentSegmentation(
                    document_name=cache_data['document_name'],
                    total_pages=cache_data['total_pages'],
                    segments=segments
                )
            except Exception:
                pass  # Cache invalid, regenerate

        # Load markdown file
        markdown_file = self.markdown_dir / f"{doc_name}.md"

        if not markdown_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

        print(f"Segmenting document: {doc_name}")

        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Parse pages
        pages = self.parse_markdown_pages(markdown_content)
        total_pages = len(pages)

        print(f"  Found {total_pages} pages")

        if total_pages == 0:
            return DocumentSegmentation(
                document_name=doc_name,
                total_pages=0,
                segments=[]
            )

        # Create non-overlapping chunks for processing
        chunks = []
        step = self.chunk_size  # No overlap

        for i in range(0, total_pages, step):
            chunk_end = min(i + self.chunk_size, total_pages)
            text_chunk = self.create_chunk_text(pages, i, chunk_end)

            start_page = pages[i]['page_number']
            end_page = pages[chunk_end - 1]['page_number']

            chunks.append((i, text_chunk, step, start_page, end_page))

        print(f"  Processing {len(chunks)} chunks")

        # Process chunks in parallel
        all_segments = []
        ordered_results = {}

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(chunks))) as executor:
            futures = {executor.submit(self.process_chunk, chunk_data): chunk_data[0] for chunk_data in chunks}

            for future in tqdm(as_completed(futures), total=len(chunks), desc=f"Segmenting {doc_name}"):
                chunk_index = futures[future]
                chunk_segments = future.result()
                ordered_results[chunk_index] = chunk_segments

        # Collect results in order and post-process to ensure complete coverage
        for i in range(0, total_pages, step):
            if i in ordered_results:
                all_segments.extend(ordered_results[i])

        # Post-process to fix gaps and overlaps
        all_segments = self._post_process_segments(all_segments, total_pages, pages)

        # Create segments objects
        segments = []
        for seg_data in all_segments:
            segments.append(Segment(
                heading=seg_data['heading'],
                description=seg_data['description'],
                page_range=PageRange(
                    start=seg_data['page_range']['start'],
                    end=seg_data['page_range']['end']
                )
            ))

        # Create final segmentation
        segmentation = DocumentSegmentation(
            document_name=doc_name,
            total_pages=total_pages,
            segments=segments
        )

        # Cache the result
        cache_data = {
            'document_name': doc_name,
            'total_pages': total_pages,
            'segments': [s.model_dump() for s in segments]
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

        print(f"  Segmented into {len(segments)} sections")
        return segmentation

    def _post_process_segments(self, segments: List[Dict[str, Any]], total_pages: int, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Post-process segments to ensure complete coverage and no overlaps.

        Args:
            segments: List of segment dictionaries
            total_pages: Total number of pages in document
            pages: List of page data

        Returns:
            Post-processed segments with complete coverage
        """
        if not segments:
            return []

        # Sort segments by start page
        segments.sort(key=lambda x: x['page_range']['start'])

        # Remove exact duplicates
        unique_segments = []
        seen = set()
        for seg in segments:
            key = (seg['page_range']['start'], seg['page_range']['end'], seg['heading'])
            if key not in seen:
                unique_segments.append(seg)
                seen.add(key)

        segments = unique_segments

        # Merge overlapping segments with similar headings
        merged_segments = []
        i = 0
        while i < len(segments):
            current = segments[i]

            # Look for overlapping segments with similar content
            j = i + 1
            while j < len(segments):
                next_seg = segments[j]

                # Check if they overlap
                if (current['page_range']['end'] >= next_seg['page_range']['start'] and
                    next_seg['page_range']['end'] >= current['page_range']['start']):

                    # Merge them
                    merged_start = min(current['page_range']['start'], next_seg['page_range']['start'])
                    merged_end = max(current['page_range']['end'], next_seg['page_range']['end'])

                    # Choose the better heading (longer one usually has more detail)
                    better_heading = current['heading'] if len(current['heading']) >= len(next_seg['heading']) else next_seg['heading']
                    better_desc = current['description'] if len(current['description']) >= len(next_seg['description']) else next_seg['description']

                    current = {
                        'heading': better_heading,
                        'description': better_desc,
                        'page_range': {'start': merged_start, 'end': merged_end}
                    }

                    # Remove the merged segment
                    segments.pop(j)
                else:
                    j += 1

            merged_segments.append(current)
            i += 1

        # Sort again after merging
        merged_segments.sort(key=lambda x: x['page_range']['start'])

        # Fill gaps between segments
        final_segments = []

        for i, segment in enumerate(merged_segments):
            # Add current segment
            final_segments.append(segment)

            # Check for gap after this segment
            current_end = segment['page_range']['end']

            if i + 1 < len(merged_segments):
                next_start = merged_segments[i + 1]['page_range']['start']

                # Fill gap if exists
                if current_end + 1 < next_start:
                    gap_start = current_end + 1
                    gap_end = next_start - 1

                    final_segments.append({
                        'heading': f"Document Section (Pages {gap_start}-{gap_end})",
                        'description': "Additional document content",
                        'page_range': {'start': gap_start, 'end': gap_end}
                    })

        # Handle missing pages at the beginning and end
        if final_segments:
            first_start = final_segments[0]['page_range']['start']
            last_end = final_segments[-1]['page_range']['end']

            # Add segment for missing pages at beginning
            if first_start > 1:
                final_segments.insert(0, {
                    'heading': "Document Header (Cover, TOC, etc.)",
                    'description': "Document header pages including cover page and table of contents",
                    'page_range': {'start': 1, 'end': first_start - 1}
                })

            # Add segment for missing pages at end
            if last_end < total_pages:
                final_segments.append({
                    'heading': "Document Appendix",
                    'description': "Additional document content and appendices",
                    'page_range': {'start': last_end + 1, 'end': total_pages}
                })

        return final_segments

    def get_available_documents(self) -> List[str]:
        """Get list of available markdown documents for segmentation."""
        if not self.markdown_dir.exists():
            return []

        docs = []
        for md_file in self.markdown_dir.glob("*.md"):
            docs.append(md_file.stem)

        return sorted(docs)

    def segment_all_documents(self, force_resegment: bool = False) -> Dict[str, DocumentSegmentation]:
        """
        Segment all available documents.

        Args:
            force_resegment: If True, re-segment all documents

        Returns:
            Dictionary of document_name -> DocumentSegmentation
        """
        available_docs = self.get_available_documents()

        if not available_docs:
            print("No markdown documents found for segmentation")
            return {}

        print(f"Segmenting {len(available_docs)} documents...")

        results = {}

        for doc_name in tqdm(available_docs, desc="Processing documents"):
            try:
                segmentation = self.segment_document(doc_name, force_resegment)
                results[doc_name] = segmentation
            except Exception as e:
                print(f"Failed to segment {doc_name}: {e}")

        return results


def main():
    """Test the document segmentation system."""
    segmenter = DocumentSegmenter(max_workers=5, chunk_size=60, overlap=0)

    # Get available documents
    available_docs = segmenter.get_available_documents()
    print(f"Found {len(available_docs)} documents available for segmentation")

    if available_docs:
        # Test with first document
        test_doc = available_docs[0]
        print(f"\nTesting segmentation with: {test_doc}")

        try:
            segmentation = segmenter.segment_document(test_doc)

            print(f"\nSegmentation Results for {test_doc}:")
            print(f"Total pages: {segmentation.total_pages}")
            print(f"Number of segments: {len(segmentation.segments)}")
            print("\nSegments:")

            for i, segment in enumerate(segmentation.segments, 1):
                print(f"{i:2}. {segment.heading}")
                print(f"    Pages: {segment.page_range.start}-{segment.page_range.end}")
                print(f"    Description: {segment.description[:100]}...")
                print()

        except Exception as e:
            print(f"Error during segmentation: {e}")


if __name__ == "__main__":
    main()