# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FinanceBench document processing system that downloads, converts, and segments financial documents (SEC filings like 10-K, 10-Q) from the FinanceBench dataset. The system provides a complete pipeline from PDF acquisition to structured document analysis.

## Core Architecture

The system follows a modular pipeline architecture organized in `src/ingestion/` with three main processing stages:

### 1. PDF Download (`src/ingestion/download/`)
- **`pdf_downloader.py`**: Core PDF downloader class for managing documents
- **`batch_download.py`**: Parallel batch downloading of 360 financial PDFs from FinanceBench GitHub
- Uses `financebench_document_information.jsonl` as the source of truth for document metadata
- Stores PDFs in `data/` directory (gitignored)
- Parallel download with 10 workers for efficiency

### 2. OCR Processing (`src/ingestion/ocr/`)
- **`pdf_to_markdown.py`**: Core OCR processing using Mistral OCR API
- **`batch_ocr.py`**: Parallel batch OCR processing across documents
- Converts PDFs to markdown preserving page numbers with `<!-- Page X -->` markers
- Includes image extraction framework (though financial docs typically contain few raster images)
- Outputs to `.finance/markdown/` with automatic caching

### 3. Document Segmentation (`src/ingestion/segmentation/`)
- **`document_segmenter.py`**: Core segmentation using Kimi model via OpenRouter
- **`batch_segment.py`**: Parallel batch segmentation with coverage verification
- Uses Instructor library for structured output with Pydantic models
- Implements coverage verification ensuring 100% page coverage with auto-retry
- Post-processes to eliminate overlaps and fill gaps
- Outputs structured segments to `.finance/segments/`

### 4. Utilities (`src/ingestion/utils/`)
- **`coverage_checker.py`**: Page coverage analysis and verification tools

### 5. Query System (`src/query/`)
- **Placeholder for future query and history functionality**

## Environment Setup

Required API keys in `.env`:
```
MISTRAL_API_KEY=your_mistral_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

Python environment managed with `uv`:
```bash
uv sync  # Install all dependencies from pyproject.toml
```

## Common Development Commands

### Entry Point Scripts (Recommended)
```bash
uv run run_download.py      # Download all 360 PDFs in parallel
uv run run_ocr.py          # Process all documents with OCR
uv run run_segmentation.py # Segment all documents with coverage verification
uv run run_pipeline.py     # Run complete pipeline (download → OCR → segmentation)
```

### Individual Module Testing
```bash
uv run src/ingestion/download/pdf_downloader.py     # Test single document download
uv run src/ingestion/ocr/pdf_to_markdown.py         # Test single document OCR
uv run src/ingestion/segmentation/document_segmenter.py # Test single document segmentation
```

### Analysis and Debugging
```bash
uv run src/ingestion/utils/coverage_checker.py  # Analyze page coverage for segmented documents
```

### Package Installation
```bash
uv sync                    # Install all dependencies from pyproject.toml
```

## Key Data Structures

### Pydantic Models (in `src/ingestion/segmentation/`)
- `PageRange`: Represents start/end page numbers for document sections
- `Segment`: Document section with heading, description, and page range
- `DocumentSegmentation`: Complete segmentation result for a document

### Cache Structure
```
.finance/
├── markdown/          # OCR results (markdown files with page markers)
├── images/           # Extracted images (organized by document)
└── segments/         # Segmentation results (JSON files)
```

## Processing Pipeline Configuration

### OCR Settings
- Uses Mistral OCR API with image extraction enabled
- Processes full documents (no chunking at OCR level)
- Caches results to avoid reprocessing

### Segmentation Settings
- Kimi model via OpenRouter (`moonshotai/kimi-k2-0905`)
- 60-page chunks with 0 overlap to prevent duplicate segments
- 5 parallel workers for document chunks
- 3 parallel workers for batch processing
- Auto-retry up to 3 times for coverage issues

## Development Notes

### Parallel Processing Strategy
- Downloads: 10 workers for network I/O optimization
- OCR: Single document processing (API limitations)
- Segmentation: 5 workers for chunks, 3 workers for documents

### Error Handling
- All operations include automatic retry mechanisms
- Caching prevents loss of work on interruption
- Coverage verification ensures data integrity

### Resume Capability
All scripts support interruption and resume:
- Check existing cache files
- Skip completed work automatically
- Process only remaining items

The system is designed for robustness with large-scale document processing (360 financial documents totaling ~669MB of PDFs, ~183MB of markdown).