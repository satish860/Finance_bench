"""
Test script to debug Mistral OCR image extraction.
"""

import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral
import json

# Load environment variables
load_dotenv()

def test_ocr_with_images():
    """Test OCR with image extraction to see what's returned."""

    # Setup client
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is required")

    client = Mistral(api_key=api_key)

    # Test with an earnings report (more likely to have charts/images)
    pdf_path = Path("data/BESTBUY_2023Q4_EARNINGS.pdf")

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return

    print(f"Testing OCR with: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")

    # Read and encode PDF (just first 5MB for testing)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read(5 * 1024 * 1024)  # Read first 5MB only for testing

    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

    print("\nCalling Mistral OCR API with include_image_base64=True...")

    try:
        # Call OCR with image extraction enabled
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            include_image_base64=True
        )

        print(f"\nResponse type: {type(response)}")
        print(f"Response attributes: {dir(response)}")

        if hasattr(response, 'pages'):
            print(f"Number of pages: {len(response.pages)}")

            # Check first page in detail
            if response.pages:
                first_page = response.pages[0]
                print(f"\nFirst page type: {type(first_page)}")
                print(f"First page attributes: {dir(first_page)}")

                # Check for images
                if hasattr(first_page, 'images'):
                    print(f"Images attribute exists: {first_page.images}")
                    if first_page.images:
                        print(f"Number of images on first page: {len(first_page.images)}")

                        # Check first image
                        first_image = first_page.images[0]
                        print(f"First image type: {type(first_image)}")
                        print(f"First image attributes: {dir(first_image)}")

                        if hasattr(first_image, 'base64'):
                            print(f"Image has base64 data: {len(first_image.base64) if first_image.base64 else 0} chars")
                    else:
                        print("Images list is empty")
                else:
                    print("No 'images' attribute found on page")

                # Check for other image-related attributes
                for attr in dir(first_page):
                    if 'image' in attr.lower() or 'img' in attr.lower() or 'figure' in attr.lower():
                        print(f"Found image-related attribute: {attr}")
                        value = getattr(first_page, attr)
                        print(f"  Value type: {type(value)}")
                        if value:
                            print(f"  Value: {str(value)[:100]}...")

        # Try to access raw response data
        if hasattr(response, '_raw_response'):
            print(f"\nRaw response available: {response._raw_response}")

        # Check model capabilities
        print("\n" + "="*60)
        print("Note: Some PDFs may not contain extractable images.")
        print("Financial documents often use embedded text rather than images.")

    except Exception as e:
        print(f"\nError during OCR: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_with_images()