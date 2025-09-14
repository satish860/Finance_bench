import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
from typing import List, Tuple

def load_document_info(jsonl_file: str) -> List[str]:
    """Load document names from JSONL file."""
    pdf_names = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            pdf_names.append(data['doc_name'] + '.pdf')
    return pdf_names

def download_pdf(pdf_name: str, base_url: str, data_folder: Path) -> Tuple[str, bool, str]:
    """Download a single PDF file."""
    url = base_url + pdf_name
    output_path = data_folder / pdf_name

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        return pdf_name, True, f"Downloaded successfully ({len(response.content) / 1024 / 1024:.2f} MB)"
    except requests.exceptions.RequestException as e:
        return pdf_name, False, f"Failed: {str(e)}"
    except Exception as e:
        return pdf_name, False, f"Unexpected error: {str(e)}"

def main():
    # Configuration
    jsonl_file = "financebench_document_information.jsonl"
    data_folder = Path("data")
    base_url = "https://raw.githubusercontent.com/patronus-ai/financebench/main/pdfs/"
    max_workers = 10  # Number of parallel downloads

    # Create data folder if it doesn't exist
    data_folder.mkdir(exist_ok=True)

    # Load PDF names
    print("Loading document information...")
    pdf_names = load_document_info(jsonl_file)
    print(f"Found {len(pdf_names)} PDF files to download")

    # Download PDFs in parallel
    start_time = time.time()
    successful = 0
    failed = 0

    print(f"\nStarting parallel download with {max_workers} workers...")
    print("-" * 60)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        futures = {
            executor.submit(download_pdf, pdf_name, base_url, data_folder): pdf_name
            for pdf_name in pdf_names
        }

        # Process completed downloads
        for i, future in enumerate(as_completed(futures), 1):
            pdf_name, success, message = future.result()

            if success:
                successful += 1
                status = "[OK]"
                print(f"[{i}/{len(pdf_names)}] {status} {pdf_name}: {message}")
            else:
                failed += 1
                status = "[FAIL]"
                print(f"[{i}/{len(pdf_names)}] {status} {pdf_name}: {message}")

    # Print summary
    elapsed_time = time.time() - start_time
    print("-" * 60)
    print(f"\nDownload completed in {elapsed_time:.2f} seconds")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Average speed: {len(pdf_names) / elapsed_time:.2f} files/second")

    # List failed downloads if any
    if failed > 0:
        print("\nTo retry failed downloads, run the script again.")

if __name__ == "__main__":
    main()