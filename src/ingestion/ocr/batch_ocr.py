"""
Batch PDF to Markdown converter using Mistral OCR with parallel processing.
Efficiently converts all FinanceBench PDFs to markdown format using concurrent workers.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Optional
import threading

try:
    from .pdf_to_markdown import PDFToMarkdown
except ImportError:
    from src.ingestion.ocr.pdf_to_markdown import PDFToMarkdown


class BatchOCR:
    def __init__(self, max_workers: int = 5):
        """
        Initialize batch converter with parallel processing.

        Args:
            max_workers: Number of concurrent API calls (be mindful of rate limits)
        """
        self.max_workers = max_workers
        self.converter = PDFToMarkdown()
        self.lock = threading.Lock()

        # Stats tracking
        self.completed = 0
        self.failed = 0
        self.skipped = 0
        self.total_images = 0

    def convert_single_pdf(self, doc_name: str, force_reconvert: bool = False) -> Tuple[str, bool, str, Optional[float]]:
        """
        Convert a single PDF to markdown.

        Returns:
            Tuple of (doc_name, success, message, processing_time_seconds)
        """
        def count_images_in_folder(doc_name: str) -> int:
            """Count images in the document's image folder."""
            images_dir = self.converter.get_images_dir(doc_name)
            if images_dir.exists():
                return len(list(images_dir.glob('*.png')))
            return 0
        start_time = time.time()

        try:
            # Check if already cached
            if not force_reconvert and self.converter.is_markdown_cached(doc_name):
                image_count = count_images_in_folder(doc_name)
                with self.lock:
                    self.skipped += 1
                    self.total_images += image_count

                message = "Already cached"
                if image_count > 0:
                    message += f" ({image_count} images)"

                return doc_name, True, message, time.time() - start_time

            # Convert PDF
            markdown_path = self.converter.pdf_to_markdown(doc_name, force_reconvert=force_reconvert)

            processing_time = time.time() - start_time

            if markdown_path:
                file_size = markdown_path.stat().st_size
                image_count = count_images_in_folder(doc_name)
                with self.lock:
                    self.completed += 1
                    self.total_images += image_count

                message = f"Converted successfully ({file_size//1024}KB"
                if image_count > 0:
                    message += f", {image_count} images)"
                else:
                    message += ")"

                return doc_name, True, message, processing_time
            else:
                with self.lock:
                    self.failed += 1
                return doc_name, False, "Conversion failed", processing_time

        except Exception as e:
            processing_time = time.time() - start_time
            with self.lock:
                self.failed += 1
            return doc_name, False, f"Error: {str(e)}", processing_time

    def convert_all_pdfs(self, force_reconvert: bool = False, doc_filter: Optional[str] = None) -> None:
        """
        Convert all available PDFs to markdown using parallel processing.

        Args:
            force_reconvert: If True, re-convert even if cached
            doc_filter: Optional filter string (e.g., "APPLE" to only convert Apple docs)
        """
        # Get list of available PDFs
        available_pdfs = self.converter.pdf_downloader.get_available_pdfs()

        # Apply filter if specified
        if doc_filter:
            available_pdfs = [doc for doc in available_pdfs if doc_filter.upper() in doc.upper()]

        print(f"Starting batch conversion of {len(available_pdfs)} PDFs...")
        print(f"Using {self.max_workers} parallel workers")
        print(f"Force reconvert: {force_reconvert}")
        if doc_filter:
            print(f"Filter: {doc_filter}")
        print("-" * 80)

        # Reset stats
        self.completed = 0
        self.failed = 0
        self.skipped = 0
        self.total_images = 0
        start_time = time.time()

        # Process PDFs in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.convert_single_pdf, doc_name, force_reconvert): doc_name
                for doc_name in available_pdfs
            }

            # Process completed tasks
            for i, future in enumerate(as_completed(futures), 1):
                doc_name, success, message, proc_time = future.result()

                # Print progress
                status = "[OK]" if success else "[FAIL]"
                progress = f"[{i}/{len(available_pdfs)}]"
                time_str = f"({proc_time:.1f}s)" if proc_time else ""

                print(f"{progress} {status} {doc_name}: {message} {time_str}")

                # Print intermediate stats every 50 conversions
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"  Progress: {i}/{len(available_pdfs)} - Rate: {rate:.1f} docs/sec")

        # Final statistics
        total_time = time.time() - start_time
        self._print_final_stats(len(available_pdfs), total_time)

    def convert_sample(self, count: int = 10) -> None:
        """Convert a sample of PDFs for testing."""
        available_pdfs = self.converter.pdf_downloader.get_available_pdfs()[:count]

        print(f"Converting sample of {len(available_pdfs)} PDFs for testing...")
        print("-" * 60)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(available_pdfs))) as executor:
            futures = {
                executor.submit(self.convert_single_pdf, doc_name): doc_name
                for doc_name in available_pdfs
            }

            for i, future in enumerate(as_completed(futures), 1):
                doc_name, success, message, proc_time = future.result()
                status = "[OK]" if success else "[FAIL]"
                time_str = f"({proc_time:.1f}s)" if proc_time else ""
                print(f"[{i}/{len(available_pdfs)}] {status} {doc_name}: {message} {time_str}")

        total_time = time.time() - start_time
        self._print_final_stats(len(available_pdfs), total_time)

    def _print_final_stats(self, total_docs: int, total_time: float) -> None:
        """Print final conversion statistics."""
        print("-" * 80)
        print(f"Batch conversion completed in {total_time:.1f} seconds")
        print(f"")
        print(f"Results:")
        print(f"  Total documents: {total_docs}")
        print(f"  Completed: {self.completed}")
        print(f"  Skipped (cached): {self.skipped}")
        print(f"  Failed: {self.failed}")
        print(f"  Success rate: {((self.completed + self.skipped) / total_docs * 100):.1f}%")
        print(f"  Average rate: {total_docs / total_time:.1f} documents/second")

        # Show cache statistics
        markdowns = self.converter.get_available_markdowns()
        total_size_mb = sum(info['file_size'] for info in markdowns.values()) / (1024 * 1024)

        # Calculate image statistics
        total_image_folders = 0
        total_cached_images = 0
        images_size_mb = 0

        if self.converter.images_dir.exists():
            for doc_folder in self.converter.images_dir.iterdir():
                if doc_folder.is_dir():
                    total_image_folders += 1
                    images = list(doc_folder.glob('*.png'))
                    total_cached_images += len(images)
                    images_size_mb += sum(img.stat().st_size for img in images) / (1024 * 1024)

        print(f"")
        print(f"Cache statistics:")
        print(f"  Total markdown files: {len(markdowns)}")
        print(f"  Total markdown size: {total_size_mb:.1f} MB")
        print(f"  Total images extracted: {self.total_images} (this session)")
        print(f"  Total cached images: {total_cached_images}")
        print(f"  Total images size: {images_size_mb:.1f} MB")
        print(f"  Documents with images: {total_image_folders}")

        if self.failed > 0:
            print(f"")
            print(f"Note: {self.failed} documents failed to convert. Check logs above for details.")

    def get_conversion_status(self) -> dict:
        """Get current conversion status for all documents."""
        available_pdfs = self.converter.pdf_downloader.get_available_pdfs()
        markdowns = self.converter.get_available_markdowns()

        converted = set(markdowns.keys())
        not_converted = set(available_pdfs) - converted

        # Count total images
        total_images = 0
        docs_with_images = 0
        if self.converter.images_dir.exists():
            for doc_folder in self.converter.images_dir.iterdir():
                if doc_folder.is_dir():
                    image_count = len(list(doc_folder.glob('*.png')))
                    if image_count > 0:
                        docs_with_images += 1
                        total_images += image_count

        return {
            'total_pdfs': len(available_pdfs),
            'converted': len(converted),
            'not_converted': len(not_converted),
            'conversion_rate': len(converted) / len(available_pdfs) * 100 if available_pdfs else 0,
            'total_images': total_images,
            'docs_with_images': docs_with_images,
            'converted_docs': sorted(converted),
            'not_converted_docs': sorted(not_converted)
        }


def main():
    """Main function with different batch processing options."""
    print("FinanceBench PDF to Markdown Batch Converter")
    print("=" * 60)

    # Initialize batch converter with 5 parallel workers
    # Note: Adjust max_workers based on API rate limits and system capabilities
    batch_converter = BatchOCR(max_workers=5)

    # Show current status
    status = batch_converter.get_conversion_status()
    print(f"Current status:")
    print(f"  Total PDFs available: {status['total_pdfs']}")
    print(f"  Already converted: {status['converted']} ({status['conversion_rate']:.1f}%)")
    print(f"  Not converted: {status['not_converted']}")
    print(f"  Total images extracted: {status['total_images']}")
    print(f"  Documents with images: {status['docs_with_images']}")
    print()

    # Demo options - uncomment the one you want to run:

    # Option 1: Convert a small sample for testing (recommended first)
    # print("Running sample conversion (10 documents)...")
    # batch_converter.convert_sample(count=10)

    # Option 2: Convert all PDFs (NOW RUNNING!)
    print("Converting all 360 PDFs...")
    batch_converter.convert_all_pdfs(force_reconvert=False)

    # Option 3: Convert only Apple documents (example filter)
    # print("Converting Apple documents only...")
    # batch_converter.convert_all_pdfs(doc_filter="APPLE")

    # Option 4: Re-convert everything (force reconvert)
    # print("Re-converting all PDFs...")
    # batch_converter.convert_all_pdfs(force_reconvert=True)


if __name__ == "__main__":
    main()