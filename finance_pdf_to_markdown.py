"""
Finance PDF to Markdown converter using Mistral OCR.
Converts FinanceBench PDFs to markdown format using Mistral's OCR API.
"""

import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from mistralai import Mistral
import json

# Load environment variables
load_dotenv()

try:
    from .finance_pdf_downloader import FinancePDFDownloader
except ImportError:
    from finance_pdf_downloader import FinancePDFDownloader


class FinancePDFToMarkdown:
    def __init__(self):
        """Initialize the PDF to markdown converter using Mistral OCR."""
        self.base_dir = Path(__file__).parent
        self.cache_dir = self.base_dir / ".finance"
        self.markdown_dir = self.cache_dir / "markdown"
        self.images_dir = self.cache_dir / "images"
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Initialize PDF downloader
        self.pdf_downloader = FinancePDFDownloader()

        # Initialize Mistral OCR client
        self._setup_mistral_client()

    def _setup_mistral_client(self):
        """Setup Mistral OCR client."""
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")

        self.client = Mistral(api_key=api_key)

    def _encode_pdf(self, pdf_path: Path) -> str:
        """Encode PDF file to base64 string."""
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')

    def get_markdown_path(self, doc_name: str) -> Path:
        """Get the path where markdown should be cached."""
        return self.markdown_dir / f"{doc_name}.md"

    def get_images_dir(self, doc_name: str) -> Path:
        """Get the directory where images for this document should be stored."""
        return self.images_dir / doc_name

    def _save_page_images(self, doc_name: str, page_num: int, page_data: Any) -> List[str]:
        """Save images from a page and return list of saved image paths."""
        images_dir = self.get_images_dir(doc_name)
        images_dir.mkdir(parents=True, exist_ok=True)

        saved_images = []

        if hasattr(page_data, 'images') and page_data.images:
            for img_idx, image_data in enumerate(page_data.images, 1):
                if hasattr(image_data, 'base64') and image_data.base64:
                    # Save image
                    img_filename = f"page_{page_num:03d}_img_{img_idx:03d}.png"
                    img_path = images_dir / img_filename

                    try:
                        # Decode base64 image
                        image_bytes = base64.b64decode(image_data.base64)

                        # Save to file
                        with open(img_path, 'wb') as f:
                            f.write(image_bytes)

                        saved_images.append(img_filename)
                        print(f"    Saved image: {img_filename}")
                    except Exception as e:
                        print(f"    Warning: Failed to save image {img_filename}: {e}")

        return saved_images

    def is_markdown_cached(self, doc_name: str) -> bool:
        """Check if markdown is already converted and cached."""
        markdown_path = self.get_markdown_path(doc_name)
        return markdown_path.exists() and markdown_path.stat().st_size > 0

    def pdf_to_markdown(self, doc_name: str, force_reconvert: bool = False) -> Optional[Path]:
        """
        Convert PDF to markdown with caching using Mistral OCR.

        Args:
            doc_name: Document name (e.g., "3M_2018_10K")
            force_reconvert: If True, re-convert even if cached

        Returns:
            Path to markdown file or None if failed
        """
        markdown_path = self.get_markdown_path(doc_name)

        # Check if already cached
        if not force_reconvert and self.is_markdown_cached(doc_name):
            print(f"Markdown already cached: {markdown_path}")
            return markdown_path

        # Ensure PDF is downloaded
        pdf_path = self.pdf_downloader.download_pdf(doc_name)
        if not pdf_path:
            print(f"Failed to download PDF for {doc_name}")
            return None

        print(f"Converting {doc_name} to markdown using Mistral OCR...")
        print(f"   PDF: {pdf_path}")
        print(f"   Output: {markdown_path}")

        try:
            # Convert PDF using Mistral OCR
            print("Processing PDF with Mistral OCR...")

            # Encode PDF to base64
            base64_pdf = self._encode_pdf(pdf_path)

            # Call Mistral OCR API - this is a synchronous call
            print("Calling Mistral OCR API...")
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=True  # Enable image extraction
            )

            print("OCR processing completed, extracting markdown...")

            # Extract markdown text from response with page numbers and images
            markdown_text = ""
            total_images_saved = 0

            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                print(f"Processing {len(ocr_response.pages)} pages...")

                for page_idx, page in enumerate(ocr_response.pages, 1):
                    # Add page marker
                    markdown_text += f"\n<!-- Page {page_idx} -->\n\n"

                    # Save images from this page
                    saved_images = self._save_page_images(doc_name, page_idx, page)
                    total_images_saved += len(saved_images)

                    # Add image references to markdown if any images were found
                    if saved_images:
                        markdown_text += f"**Images on this page:** {len(saved_images)}\n\n"
                        for img_file in saved_images:
                            rel_path = f"images/{doc_name}/{img_file}"
                            markdown_text += f"![Page {page_idx} Image]({rel_path})\n\n"

                    # Add page content
                    if hasattr(page, 'markdown'):
                        markdown_text += page.markdown + "\n\n"

                print(f"Extracted {total_images_saved} images across {len(ocr_response.pages)} pages")
            else:
                # Handle case where response format might be different
                print(f"Unexpected OCR response format: {type(ocr_response)}")
                print(f"Response attributes: {dir(ocr_response)}")
                return None

            if not markdown_text.strip():
                print("Warning: OCR produced empty markdown content")
                return None

            print(f"Extracted markdown content: {len(markdown_text):,} characters")

            # Save markdown
            print(f"Saving markdown to: {markdown_path}")
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)

            # Verify file was saved correctly
            if not markdown_path.exists():
                print(f"Error: Failed to save markdown file to {markdown_path}")
                return None

            file_size = markdown_path.stat().st_size
            if file_size == 0:
                print(f"Error: Saved markdown file is empty")
                return None

            print(f"Conversion completed successfully: {file_size:,} characters")
            print(f"   Saved to: {markdown_path}")
            print(f"   Images saved: {total_images_saved}")
            if total_images_saved > 0:
                images_dir = self.get_images_dir(doc_name)
                print(f"   Images directory: {images_dir}")

            return markdown_path

        except Exception as e:
            print(f"Conversion failed: {e}")
            # Clean up partial files
            if markdown_path.exists():
                markdown_path.unlink()
            return None

    def convert_pdf_file(self, pdf_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Convert a specific PDF file to markdown using Mistral OCR.

        Args:
            pdf_path: Path to PDF file
            output_path: Optional output path for markdown

        Returns:
            Path to markdown file or None if failed
        """
        if output_path is None:
            output_path = pdf_path.with_suffix('.md')

        print(f"Converting PDF to markdown using Mistral OCR...")
        print(f"   Input: {pdf_path}")
        print(f"   Output: {output_path}")

        try:
            # Encode PDF to base64
            base64_pdf = self._encode_pdf(pdf_path)

            # Call Mistral OCR API
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=True  # Enable image extraction
            )

            # Extract markdown text from response with page numbers and images
            doc_name_from_path = pdf_path.stem
            markdown_text = ""
            total_images_saved = 0

            for page_idx, page in enumerate(ocr_response.pages, 1):
                # Add page marker
                markdown_text += f"\n<!-- Page {page_idx} -->\n\n"

                # Save images from this page
                saved_images = self._save_page_images(doc_name_from_path, page_idx, page)
                total_images_saved += len(saved_images)

                # Add image references to markdown if any images were found
                if saved_images:
                    markdown_text += f"**Images on this page:** {len(saved_images)}\n\n"
                    for img_file in saved_images:
                        rel_path = f"images/{doc_name_from_path}/{img_file}"
                        markdown_text += f"![Page {page_idx} Image]({rel_path})\n\n"

                # Add page content
                markdown_text += page.markdown + "\n\n"

            # Save markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)

            file_size = output_path.stat().st_size
            print(f"Conversion completed: {file_size:,} characters")

            return output_path

        except Exception as e:
            print(f"Conversion failed: {e}")
            return None

    def get_available_markdowns(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available markdown files with metadata."""
        results = {}

        for markdown_file in self.markdown_dir.glob("*.md"):
            doc_name = markdown_file.stem

            # Get file info
            file_size = markdown_file.stat().st_size
            modified_time = markdown_file.stat().st_mtime

            results[doc_name] = {
                'markdown_path': markdown_file,
                'file_size': file_size,
                'modified_time': modified_time,
                'cached': True
            }

        return results


def main():
    """Demo usage of the PDF to markdown converter."""
    converter = FinancePDFToMarkdown()

    # Example: Convert 3M 2018 10-K
    doc_name = "3M_2018_10K"
    print(f"Testing Mistral OCR conversion for: {doc_name}")

    markdown_path = converter.pdf_to_markdown(doc_name)
    if markdown_path:
        print(f"\nSuccess! Markdown available at: {markdown_path}")

        # Show first few lines
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')[:15]

        print(f"\nFirst 15 lines of markdown:")
        for i, line in enumerate(lines, 1):
            # Handle Unicode characters for Windows console
            try:
                print(f"{i:2}: {line}")
            except UnicodeEncodeError:
                print(f"{i:2}: {line.encode('ascii', 'replace').decode('ascii')}")

        # Show stats
        print(f"\nMarkdown stats:")
        print(f"   Total lines: {len(content.split('\n')):,}")
        print(f"   Total characters: {len(content):,}")
        print(f"   Contains tables: {'|' in content}")
        print(f"   Table count: {content.count('|')}")
    else:
        print(f"\nFailed to convert {doc_name}")

    # Show available markdown files
    print(f"\nAvailable markdown files:")
    markdowns = converter.get_available_markdowns()
    for doc_name, info in markdowns.items():
        size_kb = info['file_size'] // 1024
        print(f"  {doc_name}: {size_kb:,} KB")


if __name__ == "__main__":
    main()