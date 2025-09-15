"""
Batch segmentation for all FinanceBench documents with coverage verification and auto-retry.
Ensures 100% page coverage for every document.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading

try:
    from .document_segmenter import DocumentSegmenter, DocumentSegmentation
except ImportError:
    from src.ingestion.segmentation.document_segmenter import DocumentSegmenter, DocumentSegmentation


class BatchSegment:
    def __init__(self, max_workers: int = 3, max_retries: int = 3):
        """
        Initialize batch segmentation processor.

        Args:
            max_workers: Number of documents to process in parallel
            max_retries: Maximum retry attempts for failed coverage
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.segmenter = DocumentSegmenter(max_workers=5, chunk_size=60, overlap=0)

        # Thread-safe statistics
        self.lock = threading.Lock()
        self.stats = {
            'total_documents': 0,
            'completed': 0,
            'failed': 0,
            'retries_needed': 0,
            'perfect_coverage': 0,
            'partial_coverage': 0,
            'processing_times': []
        }

    def verify_coverage(self, segmentation: DocumentSegmentation) -> Tuple[float, List[int]]:
        """
        Verify page coverage for a document segmentation.

        Args:
            segmentation: DocumentSegmentation object

        Returns:
            Tuple of (coverage_percentage, missing_pages)
        """
        total_pages = segmentation.total_pages
        if total_pages == 0:
            return 100.0, []

        # Create set of covered pages
        covered_pages = set()
        for segment in segmentation.segments:
            start = segment.page_range.start
            end = segment.page_range.end
            for page in range(start, end + 1):
                covered_pages.add(page)

        # Find missing pages
        all_pages = set(range(1, total_pages + 1))
        missing_pages = sorted(list(all_pages - covered_pages))

        coverage = len(covered_pages) / total_pages * 100
        return coverage, missing_pages

    def process_single_document(self, doc_name: str) -> Dict:
        """
        Process a single document with retry logic for coverage issues.

        Args:
            doc_name: Document name to process

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        result = {
            'document': doc_name,
            'success': False,
            'coverage': 0.0,
            'retries': 0,
            'missing_pages': [],
            'segments_count': 0,
            'processing_time': 0.0,
            'error': None
        }

        try:
            for attempt in range(self.max_retries + 1):
                try:
                    # Clear cache on retries
                    if attempt > 0:
                        cache_file = self.segmenter.segments_dir / f"{doc_name}_segments.json"
                        if cache_file.exists():
                            cache_file.unlink()

                        print(f"  Retry {attempt} for {doc_name} (coverage was {result['coverage']:.1f}%)")

                    # Perform segmentation
                    segmentation = self.segmenter.segment_document(doc_name, force_resegment=(attempt > 0))

                    # Verify coverage
                    coverage, missing_pages = self.verify_coverage(segmentation)

                    result.update({
                        'coverage': coverage,
                        'missing_pages': missing_pages,
                        'segments_count': len(segmentation.segments),
                        'retries': attempt
                    })

                    # Check if coverage is acceptable
                    if coverage >= 100.0:
                        result['success'] = True
                        break
                    elif attempt == self.max_retries:
                        # Final attempt failed
                        result['error'] = f"Coverage only {coverage:.1f}% after {self.max_retries} retries"
                        break

                except Exception as e:
                    if attempt == self.max_retries:
                        result['error'] = str(e)
                        break
                    continue

        except Exception as e:
            result['error'] = f"Fatal error: {str(e)}"

        result['processing_time'] = time.time() - start_time

        # Update statistics
        with self.lock:
            if result['success']:
                self.stats['completed'] += 1
                if result['coverage'] >= 100.0:
                    self.stats['perfect_coverage'] += 1
                else:
                    self.stats['partial_coverage'] += 1
            else:
                self.stats['failed'] += 1

            if result['retries'] > 0:
                self.stats['retries_needed'] += 1

            self.stats['processing_times'].append(result['processing_time'])

        return result

    def process_all_documents(self) -> Dict:
        """
        Process all available documents with coverage verification.

        Returns:
            Dictionary with comprehensive results
        """
        # Get all available documents
        available_docs = self.segmenter.get_available_documents()

        if not available_docs:
            print("No documents found for segmentation!")
            return {'results': [], 'summary': self.stats}

        print(f"Starting batch segmentation of {len(available_docs)} documents...")
        print(f"Using {self.max_workers} parallel workers")
        print(f"Maximum {self.max_retries} retries per document for coverage issues")
        print("-" * 80)

        self.stats['total_documents'] = len(available_docs)

        # Process documents in parallel
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.process_single_document, doc_name): doc_name
                for doc_name in available_docs
            }

            # Process completed tasks with progress bar
            for future in tqdm(as_completed(futures), total=len(available_docs), desc="Processing documents"):
                result = future.result()
                results.append(result)

                # Print immediate feedback for failures
                if not result['success']:
                    print(f"\n[FAILED] {result['document']}: {result['error']}")
                elif result['retries'] > 0:
                    print(f"\n[RETRY] {result['document']}: Required {result['retries']} retries, final coverage {result['coverage']:.1f}%")

        return {
            'results': results,
            'summary': self._generate_summary(results)
        }

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate comprehensive summary statistics."""

        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        needed_retries = [r for r in results if r['retries'] > 0]

        perfect_coverage = [r for r in successful if r['coverage'] >= 100.0]

        total_time = sum(self.stats['processing_times'])
        avg_time = total_time / len(results) if results else 0

        return {
            'total_documents': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) * 100 if results else 0,
            'needed_retries': len(needed_retries),
            'retry_rate': len(needed_retries) / len(results) * 100 if results else 0,
            'perfect_coverage': len(perfect_coverage),
            'perfect_coverage_rate': len(perfect_coverage) / len(results) * 100 if results else 0,
            'total_processing_time': total_time,
            'average_processing_time': avg_time,
            'total_segments': sum(r['segments_count'] for r in successful),
            'failed_documents': [r['document'] for r in failed],
            'retry_documents': [r['document'] for r in needed_retries]
        }

    def save_results(self, results: Dict, filename: str = "batch_segmentation_results.json"):
        """Save detailed results to JSON file."""
        output_file = Path(filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Detailed results saved to: {output_file}")

    def print_summary(self, summary: Dict):
        """Print comprehensive summary."""
        print("\n" + "="*80)
        print("BATCH SEGMENTATION SUMMARY")
        print("="*80)

        print(f"Total Documents:           {summary['total_documents']}")
        print(f"Successful:               {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed:                   {summary['failed']}")
        print(f"")
        print(f"Documents Needing Retries: {summary['needed_retries']} ({summary['retry_rate']:.1f}%)")
        print(f"Perfect Coverage (100%):   {summary['perfect_coverage']} ({summary['perfect_coverage_rate']:.1f}%)")
        print(f"")
        print(f"Total Processing Time:     {summary['total_processing_time']:.1f} seconds")
        print(f"Average Time per Doc:      {summary['average_processing_time']:.1f} seconds")
        print(f"Total Segments Created:    {summary['total_segments']:,}")

        if summary['failed_documents']:
            print(f"\nFailed Documents ({len(summary['failed_documents'])}):")
            for doc in summary['failed_documents']:
                print(f"  - {doc}")

        if summary['retry_documents']:
            print(f"\nDocuments That Needed Retries ({len(summary['retry_documents'])}):")
            for doc in summary['retry_documents']:
                print(f"  - {doc}")

        print("="*80)


def main():
    """Main function to run batch segmentation."""
    processor = BatchSegment(max_workers=3, max_retries=3)

    print("FinanceBench Batch Document Segmentation")
    print("=" * 60)

    # Process all documents
    results = processor.process_all_documents()

    # Print summary
    processor.print_summary(results['summary'])

    # Save detailed results
    processor.save_results(results)

    # Final status
    success_rate = results['summary']['success_rate']
    perfect_coverage_rate = results['summary']['perfect_coverage_rate']

    if success_rate >= 95 and perfect_coverage_rate >= 95:
        print("\n🎉 Batch segmentation completed successfully!")
    elif success_rate >= 90:
        print("\n✅ Batch segmentation mostly successful with some issues.")
    else:
        print("\n⚠️ Batch segmentation completed with significant issues.")


if __name__ == "__main__":
    main()