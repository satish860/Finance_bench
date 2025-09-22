# FinanceBench RAG Agent - CLAUDE.md

This file provides instructions for Claude Code when working as a RAG (Retrieval-Augmented Generation) agent for the FinanceBench financial document processing system.

## Project Purpose

Answer questions about financial documents (SEC filings like 10-K, 10-Q) by retrieving relevant information from processed markdown documents.

## RAG System Overview

### Data Sources
- **Markdown Documents**: Located in `.finance/markdown/` directory
- **Document Format**: Markdown files with full text content from SEC filings
- **Source Documents**: 360+ SEC financial filings from FinanceBench dataset
- **Page Markers**: Documents include `<!-- Page X -->` markers for citation

### Query Processing Workflow

1. **Question Analysis**: Understand the user's financial question and identify key concepts
2. **Document Retrieval**: Use Glob to find relevant company documents
3. **Content Search**: Use Grep to search for specific financial terms within markdown files
4. **Answer Generation**: Extract and synthesize information to provide comprehensive answers
5. **Citation**: Always include document sources and page references

### Search Strategy

**Primary Tools:**
- **Glob**: Find company documents in `.finance/markdown/` (e.g., `*3M*2018*`)
- **Grep**: Search for financial terms, numbers, and concepts within markdown files
- **Read**: Examine specific sections of documents for detailed information

**Search Approach:**
1. Use Glob to find relevant company documents by name and year
2. Use Grep to search for specific financial terms across the identified documents
3. Extract relevant content and page numbers from search results
4. Cross-reference information when needed

### Response Guidelines

**Answer Structure:**
1. **Direct Answer**: Lead with the specific answer in bold
2. **Detailed Context**: Provide the full financial statement section or table showing the data
3. **Verification**: Show related calculations or cross-references when available
4. **Source Citations**: Include document name, section title, and page number
5. **Additional Context**: Explain business context, comparisons to prior years, or related metrics

**Response Format:**
```
**ANSWER: [Specific answer with units]**

CONTEXT:
[Include relevant table, calculation, or financial statement excerpt]

VERIFICATION:
[Show any related data that confirms the answer]

SOURCE: [Document_Name.md] - [Section Title] (Page X)

ADDITIONAL NOTES:
[Business context, year-over-year changes, etc.]
```

**Quality Standards:**
- Always include the actual data table or financial statement excerpt
- Show calculations when relevant (e.g., free cash flow = operating cash flow - capex)
- Compare to prior years when data is available
- Provide specific dollar amounts with proper units (millions, billions)
- Use exact page numbers from `<!-- Page X -->` markers

### Search Optimization
- Use financial terminology: "revenue", "cash flow", "capital expenditures", "EBITDA"
- Search for financial statement sections: "income statement", "balance sheet", "cash flow"
- Look for specific metrics: "$", "million", "billion", percentages
- Use company names and years to narrow searches

### Limitations
- **Document Scope**: Limited to documents in `.finance/markdown/`
- **Built-in Tools Only**: Use Grep, Glob, Read tools
- **No Real-time Data**: Information is from processed SEC filings only