#!/usr/bin/env python3
"""
Document reader utilities for extracting content from FinanceBench documents.

This module provides utilities to:
- Extract specific page ranges from markdown files
- Parse page markers in document content
- Load document segments and metadata efficiently
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class DocumentReader:
    """Helper class for reading and extracting content from FinanceBench documents."""

    def __init__(self, data_dir: str = ".finance"):
        """
        Initialize document reader.

        Args:
            data_dir: Path to the .finance directory containing processed documents
        """
        # Handle relative paths when running from src/query
        if data_dir == ".finance":
            self.data_dir = Path("../../.finance")
        else:
            self.data_dir = Path(data_dir)
        self.segments_dir = self.data_dir / "segments"
        self.markdown_dir = self.data_dir / "markdown"
        # Document info file is in the root directory
        self.doc_info_file = Path("../../financebench_document_information.jsonl")

        # Load document information mapping
        self._doc_info_cache = self._load_document_info()

    def _load_document_info(self) -> Dict[str, Dict[str, Any]]:
        """Load document information mapping from JSONL file."""
        doc_info = {}

        if not self.doc_info_file.exists():
            print(f"Warning: Document info file not found at {self.doc_info_file}")
            return doc_info

        try:
            with open(self.doc_info_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        doc_data = json.loads(line.strip())
                        doc_info[doc_data["doc_name"]] = doc_data
        except Exception as e:
            print(f"Error loading document info: {e}")

        return doc_info

    def get_document_info(self, doc_name: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata for a specific document.

        Args:
            doc_name: Name of the document (e.g., "3M_2018_10K")

        Returns:
            Dictionary containing document metadata or None if not found
        """
        return self._doc_info_cache.get(doc_name)

    def load_document_segments(self, doc_name: str) -> Optional[Dict[str, Any]]:
        """
        Load document segments for a specific document.

        Args:
            doc_name: Name of the document (e.g., "3M_2018_10K")

        Returns:
            Dictionary containing document segments or None if not found
        """
        segment_file = self.segments_dir / f"{doc_name}_segments.json"

        if not segment_file.exists():
            print(f"Segment file not found: {segment_file}")
            return None

        try:
            with open(segment_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading segments for {doc_name}: {e}")
            return None

    def extract_page_range(self, doc_name: str, start_page: int, end_page: int) -> Optional[str]:
        """
        Extract content for a specific page range from a document.

        Args:
            doc_name: Name of the document
            start_page: Starting page number (inclusive)
            end_page: Ending page number (inclusive)

        Returns:
            Extracted content as string or None if not found
        """
        markdown_file = self.markdown_dir / f"{doc_name}.md"

        if not markdown_file.exists():
            print(f"Markdown file not found: {markdown_file}")
            return None

        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._extract_pages_from_content(content, start_page, end_page)

        except Exception as e:
            print(f"Error reading markdown file for {doc_name}: {e}")
            return None

    def _extract_pages_from_content(self, content: str, start_page: int, end_page: int) -> str:
        """
        Extract specific page range from markdown content.

        Args:
            content: Full markdown content
            start_page: Starting page number
            end_page: Ending page number

        Returns:
            Extracted content for the specified page range
        """
        # Split content by page markers
        page_pattern = r'<!-- Page (\d+) -->'
        pages = re.split(page_pattern, content)

        # Pages list will be: [before_page_1, "1", page_1_content, "2", page_2_content, ...]
        # So we need to extract the right sections

        extracted_content = []
        current_page = 1

        # Skip the first element (content before page 1)
        for i in range(1, len(pages), 2):
            if i + 1 < len(pages):
                page_num = int(pages[i])
                page_content = pages[i + 1]

                if start_page <= page_num <= end_page:
                    extracted_content.append(f"<!-- Page {page_num} -->")
                    extracted_content.append(page_content)

                # Stop if we've passed the end page
                if page_num > end_page:
                    break

        return '\n'.join(extracted_content)

    def search_in_segments(self, doc_name: str, search_terms: List[str]) -> List[Dict[str, Any]]:
        """
        Search for terms within document segments.

        Args:
            doc_name: Name of the document
            search_terms: List of terms to search for

        Returns:
            List of matching segments with relevance information
        """
        segments_data = self.load_document_segments(doc_name)
        if not segments_data:
            return []

        matching_segments = []
        search_terms_lower = [term.lower() for term in search_terms]

        for segment in segments_data.get("segments", []):
            heading = segment.get("heading", "").lower()
            description = segment.get("description", "").lower()

            # Check if any search term matches
            matches = []
            for term in search_terms_lower:
                if term in heading or term in description:
                    matches.append(term)

            if matches:
                segment_with_matches = segment.copy()
                segment_with_matches["matched_terms"] = matches
                segment_with_matches["relevance_score"] = len(matches) / len(search_terms_lower)
                matching_segments.append(segment_with_matches)

        # Sort by relevance score (highest first)
        matching_segments.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matching_segments

    def get_segment_content(self, doc_name: str, segment_heading: str) -> Optional[str]:
        """
        Get content for a specific segment by heading.

        Args:
            doc_name: Name of the document
            segment_heading: Heading of the segment to extract

        Returns:
            Content of the segment or None if not found
        """
        segments_data = self.load_document_segments(doc_name)
        if not segments_data:
            return None

        # Find the segment with matching heading
        for segment in segments_data.get("segments", []):
            if segment.get("heading", "").lower() == segment_heading.lower():
                page_range = segment.get("page_range", {})
                start_page = page_range.get("start")
                end_page = page_range.get("end")

                if start_page and end_page:
                    return self.extract_page_range(doc_name, start_page, end_page)

        return None

    def search_document_content(self, doc_name: str, search_terms: List[str],
                              max_segments: int = 5) -> Dict[str, Any]:
        """
        Search for content within a document and return relevant segments with content.

        Args:
            doc_name: Name of the document
            search_terms: List of terms to search for
            max_segments: Maximum number of segments to return

        Returns:
            Dictionary containing search results and extracted content
        """
        # Get document info for context
        doc_info = self.get_document_info(doc_name)

        # Search in segments
        matching_segments = self.search_in_segments(doc_name, search_terms)

        # Limit results
        top_segments = matching_segments[:max_segments]

        # Extract content for top segments
        results = {
            "doc_name": doc_name,
            "doc_info": doc_info,
            "search_terms": search_terms,
            "total_matches": len(matching_segments),
            "returned_segments": len(top_segments),
            "segments": []
        }

        for segment in top_segments:
            page_range = segment.get("page_range", {})
            start_page = page_range.get("start")
            end_page = page_range.get("end")

            content = None
            if start_page and end_page:
                content = self.extract_page_range(doc_name, start_page, end_page)

            segment_result = {
                "heading": segment.get("heading"),
                "description": segment.get("description"),
                "page_range": page_range,
                "matched_terms": segment.get("matched_terms", []),
                "relevance_score": segment.get("relevance_score", 0),
                "content_preview": content[:500] + "..." if content and len(content) > 500 else content
            }

            results["segments"].append(segment_result)

        return results


# Utility functions for standalone use
def extract_pages(doc_name: str, start_page: int, end_page: int,
                 data_dir: str = ".finance") -> Optional[str]:
    """
    Standalone function to extract page range from a document.

    Args:
        doc_name: Name of the document
        start_page: Starting page number
        end_page: Ending page number
        data_dir: Path to data directory

    Returns:
        Extracted content or None
    """
    reader = DocumentReader(data_dir)
    return reader.extract_page_range(doc_name, start_page, end_page)


def search_document(doc_name: str, search_terms: List[str],
                   data_dir: str = ".finance") -> Dict[str, Any]:
    """
    Standalone function to search within a document.

    Args:
        doc_name: Name of the document
        search_terms: List of search terms
        data_dir: Path to data directory

    Returns:
        Search results dictionary
    """
    reader = DocumentReader(data_dir)
    return reader.search_document_content(doc_name, search_terms)


if __name__ == "__main__":
    # Test the document reader
    reader = DocumentReader()

    # Test with a sample document
    test_doc = "3M_2018_10K"

    print(f"Testing document reader with {test_doc}")

    # Test document info loading
    doc_info = reader.get_document_info(test_doc)
    if doc_info:
        print(f"Document info: {doc_info['company']} - {doc_info['doc_type']} - {doc_info['doc_period']}")

    # Test segment loading
    segments = reader.load_document_segments(test_doc)
    if segments:
        print(f"Found {len(segments.get('segments', []))} segments")

    # Test search
    search_results = reader.search_document_content(test_doc, ["capital expenditure", "cash flow"])
    print(f"Search results: {search_results['total_matches']} matches found")

    for segment in search_results['segments'][:2]:
        print(f"- {segment['heading']} (relevance: {segment['relevance_score']:.2f})")