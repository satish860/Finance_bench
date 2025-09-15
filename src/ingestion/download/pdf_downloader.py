"""
PDF downloader for FinanceBench dataset.
Downloads and manages PDF files from the FinanceBench repository.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class PDFDownloader:
    def __init__(self):
        """Initialize the PDF downloader."""
        # Go up to project root from src/ingestion/download/
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.jsonl_file = self.base_dir / "financebench_document_information.jsonl"

        # Load document information
        self._load_document_info()

    def _load_document_info(self) -> None:
        """Load document information from JSONL file."""
        self.documents = {}

        if not self.jsonl_file.exists():
            print(f"Warning: Document info file not found: {self.jsonl_file}")
            return

        try:
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        doc_info = json.loads(line)
                        doc_name = doc_info['doc_name']
                        self.documents[doc_name] = doc_info

            print(f"Loaded {len(self.documents)} document records")
        except Exception as e:
            print(f"Error loading document info: {e}")
            self.documents = {}

    def get_pdf_path(self, doc_name: str) -> Path:
        """Get the expected path for a PDF file."""
        return self.data_dir / f"{doc_name}.pdf"

    def is_pdf_available(self, doc_name: str) -> bool:
        """Check if PDF is already downloaded."""
        pdf_path = self.get_pdf_path(doc_name)
        return pdf_path.exists() and pdf_path.stat().st_size > 0

    def get_document_info(self, doc_name: str) -> Optional[Dict[str, Any]]:
        """Get document information for a given document name."""
        return self.documents.get(doc_name)

    def download_pdf(self, doc_name: str) -> Optional[Path]:
        """
        Download PDF if not already available.

        Args:
            doc_name: Document name (e.g., "3M_2018_10K")

        Returns:
            Path to PDF file or None if failed
        """
        pdf_path = self.get_pdf_path(doc_name)

        # Check if already downloaded
        if self.is_pdf_available(doc_name):
            return pdf_path

        # Check if document exists in our dataset
        if doc_name not in self.documents:
            print(f"Document not found in dataset: {doc_name}")
            return None

        print(f"PDF not found locally: {pdf_path}")
        print(f"Note: All PDFs should already be downloaded in the data folder.")
        print(f"If missing, run the download_pdfs.py script to download all PDFs.")

        return None

    def get_available_pdfs(self) -> List[str]:
        """Get list of available PDF document names."""
        available = []

        if not self.data_dir.exists():
            return available

        for pdf_file in self.data_dir.glob("*.pdf"):
            doc_name = pdf_file.stem
            if doc_name in self.documents:
                available.append(doc_name)

        return sorted(available)

    def get_pdf_stats(self) -> Dict[str, Any]:
        """Get statistics about available PDFs."""
        available_pdfs = self.get_available_pdfs()
        total_size = 0

        for doc_name in available_pdfs:
            pdf_path = self.get_pdf_path(doc_name)
            if pdf_path.exists():
                total_size += pdf_path.stat().st_size

        return {
            'total_documents': len(self.documents),
            'available_pdfs': len(available_pdfs),
            'missing_pdfs': len(self.documents) - len(available_pdfs),
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }


def main():
    """Demo usage of the PDF downloader."""
    downloader = PDFDownloader()

    # Show stats
    stats = downloader.get_pdf_stats()
    print(f"PDF Statistics:")
    print(f"  Total documents in dataset: {stats['total_documents']}")
    print(f"  Available PDFs: {stats['available_pdfs']}")
    print(f"  Missing PDFs: {stats['missing_pdfs']}")
    print(f"  Total size: {stats['total_size_mb']} MB")

    # Show first few available PDFs
    available = downloader.get_available_pdfs()[:5]
    print(f"\nFirst few available PDFs:")
    for doc_name in available:
        doc_info = downloader.get_document_info(doc_name)
        print(f"  {doc_name}: {doc_info['company']} {doc_info['doc_type'].upper()} {doc_info['doc_period']}")


if __name__ == "__main__":
    main()