#!/usr/bin/env python3
"""
Custom MCP tools for FinanceBench document analysis.

This module provides custom tools that Claude can use to:
- Load document information and metadata
- Load document segments and structure
- Search for specific content within documents
- Extract content from specific page ranges
"""

from claude_agent_sdk import tool
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

# Import our document reader utilities
try:
    from .document_reader import DocumentReader
except ImportError:
    # For standalone execution
    from document_reader import DocumentReader


# Initialize document reader
_doc_reader = DocumentReader()


@tool("load_document_info", "Get document metadata and company information", {
    "doc_name": str
})
async def load_document_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load document metadata and company information.

    Args:
        doc_name: Name of the document (e.g., "3M_2018_10K")

    Returns:
        Dictionary containing document metadata including company, sector, document type
    """
    doc_name = args.get("doc_name", "").strip()

    if not doc_name:
        return {
            "content": [
                {"type": "text", "text": "Error: doc_name parameter is required"}
            ],
            "isError": True
        }

    doc_info = _doc_reader.get_document_info(doc_name)

    if not doc_info:
        return {
            "content": [
                {"type": "text", "text": f"Document '{doc_name}' not found in FinanceBench dataset"}
            ],
            "isError": True
        }

    # Format the response with useful information
    response_text = f"""Document Information for {doc_name}:

Company: {doc_info.get('company', 'N/A')}
GICS Sector: {doc_info.get('gics_sector', 'N/A')}
Document Type: {doc_info.get('doc_type', 'N/A')}
Document Period: {doc_info.get('doc_period', 'N/A')}

This document is available for analysis in the FinanceBench dataset.
Use load_document_segments to see the document structure.
Use search_document_content to find specific information."""

    return {
        "content": [
            {"type": "text", "text": response_text}
        ]
    }


@tool("load_document_segments", "Load document structure and segment information", {
    "doc_name": str
})
async def load_document_segments(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load document segments showing the structure and organization.

    Args:
        doc_name: Name of the document (e.g., "3M_2018_10K")

    Returns:
        Dictionary containing document segments with headings, descriptions, and page ranges
    """
    doc_name = args.get("doc_name", "").strip()

    if not doc_name:
        return {
            "content": [
                {"type": "text", "text": "Error: doc_name parameter is required"}
            ],
            "isError": True
        }

    segments_data = _doc_reader.load_document_segments(doc_name)

    if not segments_data:
        return {
            "content": [
                {"type": "text", "text": f"Segments not found for document '{doc_name}'"}
            ],
            "isError": True
        }

    # Format the segments information
    total_pages = segments_data.get("total_pages", "Unknown")
    segments = segments_data.get("segments", [])

    response_lines = [
        f"Document Structure for {doc_name}",
        f"Total Pages: {total_pages}",
        f"Number of Segments: {len(segments)}",
        "",
        "Document Segments:"
    ]

    for i, segment in enumerate(segments, 1):
        heading = segment.get("heading", "N/A")
        description = segment.get("description", "N/A")
        page_range = segment.get("page_range", {})
        start_page = page_range.get("start", "N/A")
        end_page = page_range.get("end", "N/A")

        response_lines.extend([
            f"{i}. {heading}",
            f"   Pages: {start_page}-{end_page}",
            f"   Description: {description}",
            ""
        ])

    response_text = "\n".join(response_lines)

    return {
        "content": [
            {"type": "text", "text": response_text}
        ]
    }


@tool("search_document_content", "Search for specific content within a document", {
    "doc_name": str,
    "search_terms": list
})
async def search_document_content(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for specific terms within a document and return relevant segments.

    Args:
        doc_name: Name of the document (e.g., "3M_2018_10K")
        search_terms: List of terms to search for

    Returns:
        Dictionary containing matching segments with content previews
    """
    doc_name = args.get("doc_name", "").strip()
    search_terms = args.get("search_terms", [])

    if not doc_name:
        return {
            "content": [
                {"type": "text", "text": "Error: doc_name parameter is required"}
            ],
            "isError": True
        }

    if not search_terms:
        return {
            "content": [
                {"type": "text", "text": "Error: search_terms parameter is required"}
            ],
            "isError": True
        }

    # Ensure search_terms is a list of strings
    if isinstance(search_terms, str):
        search_terms = [search_terms]

    try:
        search_results = _doc_reader.search_document_content(doc_name, search_terms, max_segments=5)

        if search_results["total_matches"] == 0:
            return {
                "content": [
                    {"type": "text", "text": f"No matches found for search terms: {', '.join(search_terms)}"}
                ]
            }

        # Format the search results
        doc_info = search_results.get("doc_info", {})
        company = doc_info.get("company", "Unknown") if doc_info else "Unknown"

        response_lines = [
            f"Search Results for {doc_name} ({company})",
            f"Search Terms: {', '.join(search_terms)}",
            f"Total Matches: {search_results['total_matches']}",
            f"Showing Top {search_results['returned_segments']} Segments:",
            ""
        ]

        for i, segment in enumerate(search_results["segments"], 1):
            heading = segment.get("heading", "N/A")
            description = segment.get("description", "N/A")
            page_range = segment.get("page_range", {})
            start_page = page_range.get("start", "N/A")
            end_page = page_range.get("end", "N/A")
            matched_terms = segment.get("matched_terms", [])
            relevance = segment.get("relevance_score", 0)

            response_lines.extend([
                f"{i}. {heading}",
                f"   Pages: {start_page}-{end_page}",
                f"   Matched Terms: {', '.join(matched_terms)}",
                f"   Relevance: {relevance:.2f}",
                f"   Description: {description}",
                ""
            ])

        response_lines.append("Use the Read tool to examine specific page ranges:")
        response_lines.append(f"- Full document: .finance/markdown/{doc_name}.md")
        response_lines.append(f"- Segments file: .finance/segments/{doc_name}_segments.json")

        response_text = "\n".join(response_lines)

        return {
            "content": [
                {"type": "text", "text": response_text}
            ]
        }

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error searching document: {str(e)}"}
            ],
            "isError": True
        }


@tool("extract_page_range", "Extract content from specific page range", {
    "doc_name": str,
    "start_page": int,
    "end_page": int
})
async def extract_page_range(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract content from a specific page range in a document.

    Args:
        doc_name: Name of the document (e.g., "3M_2018_10K")
        start_page: Starting page number (inclusive)
        end_page: Ending page number (inclusive)

    Returns:
        Dictionary containing the extracted content
    """
    doc_name = args.get("doc_name", "").strip()
    start_page = args.get("start_page")
    end_page = args.get("end_page")

    if not doc_name:
        return {
            "content": [
                {"type": "text", "text": "Error: doc_name parameter is required"}
            ],
            "isError": True
        }

    if start_page is None or end_page is None:
        return {
            "content": [
                {"type": "text", "text": "Error: start_page and end_page parameters are required"}
            ],
            "isError": True
        }

    try:
        content = _doc_reader.extract_page_range(doc_name, start_page, end_page)

        if not content:
            return {
                "content": [
                    {"type": "text", "text": f"No content found for pages {start_page}-{end_page} in {doc_name}"}
                ],
                "isError": True
            }

        response_text = f"Content from {doc_name}, Pages {start_page}-{end_page}:\n\n{content}"

        return {
            "content": [
                {"type": "text", "text": response_text}
            ]
        }

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error extracting page range: {str(e)}"}
            ],
            "isError": True
        }


# Tool list for easy import
FINANCEBENCH_TOOLS = [
    load_document_info,
    load_document_segments,
    search_document_content,
    extract_page_range
]


def get_tools_list():
    """Return list of all FinanceBench tools."""
    return FINANCEBENCH_TOOLS


if __name__ == "__main__":
    # Test the tools functionality
    import anyio

    async def test_tools():
        print("Testing FinanceBench tools...")

        # Test document reader directly
        print("\n1. Testing document reader directly:")
        doc_info = _doc_reader.get_document_info("3M_2018_10K")
        print(f"Document info: {doc_info}")

        segments = _doc_reader.load_document_segments("3M_2018_10K")
        if segments:
            print(f"Found {len(segments.get('segments', []))} segments")

        # Test search functionality
        search_results = _doc_reader.search_document_content("3M_2018_10K", ["cash flow", "statement"])
        print(f"Search found {search_results['total_matches']} matches")

        # Test page extraction
        print("\n2. Testing page extraction:")
        content = _doc_reader.extract_page_range("3M_2018_10K", 59, 60)
        if content:
            print(f"Extracted content length: {len(content)} characters")
            print("First 200 characters:")
            print(content[:200] + "...")
        else:
            print("No content extracted")

    anyio.run(test_tools)