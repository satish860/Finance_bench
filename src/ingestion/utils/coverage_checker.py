"""
Check page coverage in document segmentation results.
"""

import json
from pathlib import Path


def analyze_page_coverage(segments_file: str):
    """Analyze page coverage from segmentation results."""

    with open(segments_file, 'r') as f:
        data = json.load(f)

    doc_name = data['document_name']
    total_pages = data['total_pages']
    segments = data['segments']

    print(f"Document: {doc_name}")
    print(f"Total pages: {total_pages}")
    print(f"Total segments: {len(segments)}")
    print("-" * 60)

    # Create a set of all covered pages
    covered_pages = set()

    for segment in segments:
        start = segment['page_range']['start']
        end = segment['page_range']['end']

        # Add all pages in this range
        for page in range(start, end + 1):
            covered_pages.add(page)

    # Find missing pages
    all_pages = set(range(1, total_pages + 1))
    missing_pages = all_pages - covered_pages

    print(f"Pages covered: {len(covered_pages)} / {total_pages}")
    print(f"Coverage: {len(covered_pages) / total_pages * 100:.1f}%")

    if missing_pages:
        print(f"Missing pages: {sorted(missing_pages)}")
        print(f"Missing count: {len(missing_pages)}")
    else:
        print("[OK] All pages are covered!")

    print("-" * 60)

    # Show segments with page ranges
    print("Segments:")
    for i, segment in enumerate(segments, 1):
        start = segment['page_range']['start']
        end = segment['page_range']['end']
        heading = segment['heading'][:50] + "..." if len(segment['heading']) > 50 else segment['heading']
        print(f"{i:2}. Pages {start:3}-{end:3}: {heading}")

    # Check for overlaps
    print("\nChecking for overlaps...")
    overlaps = []
    for i, seg1 in enumerate(segments):
        for j, seg2 in enumerate(segments[i+1:], i+1):
            start1, end1 = seg1['page_range']['start'], seg1['page_range']['end']
            start2, end2 = seg2['page_range']['start'], seg2['page_range']['end']

            # Check if ranges overlap
            if start1 <= end2 and start2 <= end1:
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                overlaps.append({
                    'segments': (i, j),
                    'pages': list(range(overlap_start, overlap_end + 1)),
                    'titles': (seg1['heading'][:30], seg2['heading'][:30])
                })

    if overlaps:
        print(f"Found {len(overlaps)} overlaps:")
        for overlap in overlaps:
            print(f"  Segments {overlap['segments'][0]+1} & {overlap['segments'][1]+1}: pages {overlap['pages']}")
            print(f"    '{overlap['titles'][0]}' vs '{overlap['titles'][1]}'")
    else:
        print("[OK] No overlaps found")


def main():
    """Main function to check coverage for example document."""
    # Go up to project root from src/ingestion/utils/
    project_root = Path(__file__).parent.parent.parent.parent
    segments_file = project_root / ".finance" / "segments" / "3M_2015_10K_segments.json"

    if segments_file.exists():
        analyze_page_coverage(str(segments_file))
    else:
        print(f"Segments file not found: {segments_file}")

        # List available segment files
        segments_dir = project_root / ".finance" / "segments"
        if segments_dir.exists():
            segment_files = list(segments_dir.glob("*_segments.json"))
            if segment_files:
                print(f"\nAvailable segment files ({len(segment_files)}):")
                for f in sorted(segment_files)[:5]:  # Show first 5
                    print(f"  {f.name}")
                if len(segment_files) > 5:
                    print(f"  ... and {len(segment_files) - 5} more")
            else:
                print("\nNo segment files found in .finance/segments/")
        else:
            print("\nSegments directory does not exist")


if __name__ == "__main__":
    main()