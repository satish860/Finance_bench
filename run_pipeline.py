#!/usr/bin/env python3
"""
Entry point script to run the complete ingestion pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingestion.download.batch_download import main as download_main
from src.ingestion.ocr.batch_ocr import main as ocr_main
from src.ingestion.segmentation.batch_segment import main as segment_main


def main():
    """Run the complete ingestion pipeline."""
    print("=" * 80)
    print("FINANCEBENCH COMPLETE INGESTION PIPELINE")
    print("=" * 80)

    # Step 1: Download PDFs
    print("\n1. DOWNLOADING PDFS...")
    print("-" * 40)
    try:
        download_main()
        print("✅ PDF download completed")
    except Exception as e:
        print(f"❌ PDF download failed: {e}")
        return False

    # Step 2: OCR Processing
    print("\n2. OCR PROCESSING...")
    print("-" * 40)
    try:
        ocr_main()
        print("✅ OCR processing completed")
    except Exception as e:
        print(f"❌ OCR processing failed: {e}")
        return False

    # Step 3: Document Segmentation
    print("\n3. DOCUMENT SEGMENTATION...")
    print("-" * 40)
    try:
        segment_main()
        print("✅ Document segmentation completed")
    except Exception as e:
        print(f"❌ Document segmentation failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("🎉 COMPLETE PIPELINE FINISHED SUCCESSFULLY!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)