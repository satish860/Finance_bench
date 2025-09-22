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

### Enhanced Data Extraction Guidelines

**Data Extraction Verification Process:**
1. **Primary Source Extraction**: Extract data from the main document (10-K/10-Q)
2. **Cross-Reference Verification**: Verify with at least one additional reference (notes, cash flow statement)
3. **Fiscal Year Alignment**: Confirm fiscal year alignment (some companies use non-calendar years)
4. **Consistency Check**: For multi-year analysis, ensure consistent accounting methods
5. **Line Item Precision**: Use exact line item names as they appear in financial statements

**Financial Statement Line Item Guidelines:**
- Use "Net earnings" vs "Net income" exactly as shown
- Use "Cost of sales" vs "Cost of goods sold" as stated
- Use "Accounts payable" not shortened "Payables"
- Use "Property, plant and equipment" not "PP&E" unless that's how it appears
- Check for "Income from continuing operations" vs "Total net income"

**Common Data Extraction Pitfalls to Avoid:**
- Don't confuse quarterly (Q1, Q2, Q3, Q4) with annual (FY) data
- Don't mix GAAP with non-GAAP metrics unless specified
- Don't use "Income from Continuing Operations" when "Total Net Income" is requested
- Verify negative numbers (losses/expenses) maintain correct signs
- Don't use preliminary/unaudited data when audited data is available
- Check for restatements or adjustments in later filings

**Multi-Source Validation Requirements:**
- For acquisitions: Check business combinations note AND cash flow statement
- For tax rates: Verify income statement AND tax note calculations
- For inventory: Cross-check balance sheet AND inventory accounting note
- For debt: Confirm balance sheet AND debt note details
- For segments: Validate segment note AND MD&A discussion

### Response Guidelines

**Answer Structure:**
1. **Direct Answer**: Lead with the specific answer in bold
2. **Detailed Context**: Provide the full financial statement section or table showing the data
3. **Verification**: Show related calculations or cross-references when available
4. **Source Citations**: Include document name, section title, and page number
5. **Additional Context**: Explain business context, comparisons to prior years, or related metrics

**Enhanced Response Formats:**

**For Numerical/Calculation Questions:**
```
**ANSWER: [Number with 2 decimal places and units]**

CALCULATION:
Step 1: [Source data with exact line items]
  - [Line Item 1]: $X,XXX million (FY20XX)
  - [Line Item 2]: $X,XXX million (FY20XX)
Step 2: [Formula application]
  - Formula: [Exact formula used]
Step 3: [Final calculation with intermediate steps]
  - Calculation: $X,XXX ÷ $X,XXX = X.XX
Result: [Final answer with proper units]

VERIFICATION:
[Cross-check calculation or alternative verification method]

SOURCE: [Document_Name.md] - [Section Title] (Page X)
```

**For Yes/No Questions:**
```
**ANSWER: [Yes/No - State definitive position first]**

RATIONALE:
[Key metric]: [Actual value] [vs threshold/benchmark if applicable]
[Clear explanation of how value relates to threshold]
Conclusion: [Restate why answer is Yes/No based on criteria]

SUPPORTING DATA:
[Include relevant supporting metrics or comparisons]

SOURCE: [Document_Name.md] - [Section Title] (Page X)
```

**For Trend/Comparison Questions:**
```
**ANSWER: [State trend/comparison result clearly]**

COMPARISON ANALYSIS:
Period 1 ([Specific Year/Quarter]): [Value with units]
Period 2 ([Specific Year/Quarter]): [Value with units]
Change: [Absolute change] ([Percentage change]%)
Trend Direction: [Improving/Declining/Stable with magnitude]

CONTEXT:
[Business factors contributing to the trend]

SOURCE: [Document_Name.md] - [Section Title] (Page X)
```

**For List/Category Questions:**
```
**ANSWER: [Direct answer to the question]**

DETAILED BREAKDOWN:
1. [Item 1]: [Details, amounts, dates if applicable]
2. [Item 2]: [Details, amounts, dates if applicable]
3. [Item 3]: [Details, amounts, dates if applicable]

VERIFICATION:
[Total amounts, cross-references, or validation data]

SOURCE: [Document_Name.md] - [Section Title] (Page X)
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

## Calculation Standards

### Numerical Precision Rules
- Round all percentages to 2 decimal places (e.g., 12.34%)
- Round all ratios to 2 decimal places (e.g., 1.23)
- Round dollar amounts to nearest million or billion as specified in question
- Use standard rounding (0.5 rounds up), not truncation
- When calculating averages: Sum all values THEN divide, don't average averages

### Financial Metrics Formulas
**Return on Assets (ROA):**
- ROA = Net Income / Average Total Assets
- Average Total Assets = (Beginning Total Assets + Ending Total Assets) / 2

**Days Payable Outstanding (DPO):**
- DPO = 365 × (Average Accounts Payable) / (COGS + Change in Inventory)
- Average AP = (Beginning AP + Ending AP) / 2
- Change in Inventory = Ending Inventory - Beginning Inventory

**Quick Ratio:**
- Quick Ratio = (Cash + Marketable Securities + Accounts Receivable) / Current Liabilities
- Do NOT include inventory or prepaid expenses

**Inventory Turnover:**
- Inventory Turnover = Cost of Goods Sold / Average Inventory
- Average Inventory = (Beginning Inventory + Ending Inventory) / 2

**Gross Margin:**
- Gross Margin % = (Revenue - Cost of Sales) / Revenue × 100
- Use exact line items: "Revenue" and "Cost of sales" or "Cost of goods sold"

**Operating Margin:**
- Operating Margin % = Operating Income / Revenue × 100
- Operating Income = Revenue - Operating Expenses

### Calculation Verification
- Always show calculation steps for verification
- Cross-check results with related metrics when available
- Verify negative numbers maintain correct signs (losses, expenses)
- Double-check data extraction from correct fiscal year

## Interpretation Thresholds

### Financial Health Indicators
**Liquidity Assessment:**
- "Healthy" liquidity = Quick Ratio ≥ 1.0
- "Needs improvement" = Quick Ratio < 1.0
- "Strong" liquidity = Quick Ratio ≥ 1.5
- Current Ratio > 2.0 = "Strong" working capital position

**Margin Analysis:**
- Margins are "consistent" if year-over-year change < 2%
- Margins are "volatile" if year-over-year change > 5%
- "Improving" margins = Current Period > Prior Period
- "Declining" margins = Current Period < Prior Period

**Growth Analysis:**
- "Significant" growth = > 10% year-over-year increase
- "Moderate" growth = 3-10% year-over-year increase
- "Flat" growth = -3% to +3% year-over-year change
- "Declining" = < -3% year-over-year change

**Capital Intensity:**
- "Capital intensive" = Capital Expenditures / Revenue > 10%
- "Moderately capital intensive" = Capex/Revenue 5-10%
- "Asset light" = Capex/Revenue < 5%

### Trend Analysis Rules
**Comparison Periods:**
- Always use Year-over-Year comparison unless otherwise specified
- For quarterly data, compare Q2 FY2024 vs Q2 FY2023 (same quarter, prior year)
- State specific periods being compared in answer

**Trend Definitions:**
- "Improving" = positive change from prior period
- "Deteriorating/Declining" = negative change from prior period
- "Stable" = change within ±2% for margins, ±5% for other metrics
- Always specify the magnitude of change (percentage and absolute)

**Significance Criteria:**
- "Major" acquisitions = typically > $50 million
- "Significant" change = > 10% or > $100 million absolute change
- "Material" impact = affects key metrics by > 5%
- "Substantial" = > 20% of relevant base metric

## Question Parsing Guidelines

### Pre-Search Analysis Checklist
**Before searching for data, identify:**
1. **Metric Type**: Is the question asking for an absolute value, ratio, percentage, or growth rate?
2. **Time Period**: FY20XX, Q2 FY20XX, 3-year average, or comparison between periods?
3. **Comparison Type**: Single point-in-time or trend analysis?
4. **Output Format**: Dollar amount, percentage, yes/no answer, or descriptive analysis?
5. **Scope**: Single company, industry comparison, or specific business segment?

### Key Question Type Distinctions
**Performance Questions:**
- "Best performer" by **revenue** = highest absolute amount in dollars
- "Best performer" by **growth** = highest percentage increase
- "Best performing **segment**" = analyze by the metric specified (revenue, growth, margin)

**Financial Health Questions:**
- "Healthy" liquidity = Apply specific thresholds from Interpretation section
- "Improving" = Compare current period to prior period
- "Consistent" = Apply variability thresholds (typically <2% for margins)

**Acquisition/Transaction Questions:**
- "Major" acquisitions = Use $50M threshold unless otherwise specified
- Check both business combinations notes AND cash flow statements
- Include acquisition date, amount, and strategic rationale

**Time Period Clarifications:**
- "FY2022" = Full fiscal year 2022 (12 months)
- "Q2 FY2024" = Second quarter of fiscal year 2024
- "Between FY2021 and FY2022" = Compare end of FY2022 to end of FY2021
- "3-year average" = Sum three years then divide by 3

### Question Ambiguity Resolution
**When questions are unclear:**
1. **Identify the most likely interpretation** based on financial context
2. **State your interpretation** in the answer ("Interpreting this as...")
3. **Provide the most relevant metric** if multiple options exist
4. **Include caveats** if alternative interpretations are reasonable

**Common Ambiguities:**
- "Margins" could mean gross margin, operating margin, or net margin → Use operating margin unless specified
- "Revenue" could include or exclude discontinued operations → Use continuing operations
- "Growth" period unclear → Use year-over-year unless specified
- "Performance" metric unclear → Use revenue as primary, include growth rate as secondary

## Critical Formula Clarifications

### Exact Formula Specifications

**Days Payable Outstanding (DPO):**
- ALWAYS use: DPO = 365 × (Average Accounts Payable) / (COGS + Change in Inventory)
- NOT: DPO = 365 × Average AP / COGS alone
- Average AP = (Beginning AP + Ending AP) / 2
- Change in Inventory = Current Year Inventory - Prior Year Inventory
- If Change in Inventory is negative, still add it (will reduce denominator)

**Effective Tax Rate:**
- Formula: Income Tax Expense / Income Before Tax
- If company has pre-tax loss and tax benefit: Rate = Tax Benefit / Loss = Negative %
- If company has pre-tax loss and tax expense: Rate = Tax Expense / Loss = Positive %
- Always maintain correct signs: Tax benefit = negative rate, Tax expense = positive rate
- Use exact numbers from income statement, not tax note estimates

**Gross Margin Trend Analysis:**
- Calculate each year separately: (Revenue - COGS) / Revenue × 100
- Compare ONLY consecutive years (FY2022 vs FY2021, not multi-year averages)
- "Improving" = Current Year % > Prior Year % (even if by 0.1%)
- "Declining" = Current Year % < Prior Year % (even if by 0.1%)
- Use exact COGS line item as named in income statement

**Return on Assets (ROA):**
- ALWAYS use: Net Income / Average Total Assets
- Net Income = Bottom line from income statement (after all items)
- Average Total Assets = (Beginning Year Assets + Ending Year Assets) / 2
- Result should typically be 1-15% for healthy companies
- If result is <0.1% or >50%, double-check calculation

### Unit Consistency Verification
**Before finalizing any calculation:**
- Ensure numerator and denominator use same units (millions vs billions)
- DPO result should be 30-120 days for most companies
- Percentages: 0.05 = 5%, not 0.05%
- Always specify units in final answer (%, days, billions, etc.)

## Question Intent Mapping

### Performance Analysis Disambiguation

**"Best Performer" Questions:**
- **By "top line" or "revenue"** = Highest absolute dollar amount in the period
- **By "growth" or "performance" alone** = Highest growth percentage year-over-year
- **By "margin"** = Highest profit margin percentage
- **When ambiguous:** Provide both absolute amount AND growth rate, then clarify interpretation

**Example Interpretations:**
- "Which segment performed best?" → Report highest revenue segment
- "Which segment had best growth?" → Report highest growth percentage segment
- "Best performing product category by top line" → Highest absolute revenue

### Consistency Analysis Rules

**"Historically Consistent" Analysis:**
- Calculate EACH individual year-over-year change
- If ANY single year change exceeds threshold (typically 2%), answer = NOT consistent
- Do NOT use average change or cumulative range
- Do NOT smooth over individual year volatility

**Example:** If margins are 20%, 21%, 22%, 19% over 4 years:
- Year 1→2: +1% (OK)
- Year 2→3: +1% (OK)
- Year 3→4: -3% (EXCEEDS 2% threshold)
- Result: NOT consistent (despite small overall range)

### Question Scope Clarification

**Geographic Scope:**
- "Domestic" = US operations only
- "International" = Non-US operations only
- "Global" or no specification = Total company (all geographies)

**Financial Statement Scope:**
- "Based on income statement" = Use income statement data only
- "Based on balance sheet" = Use balance sheet data only
- "Based on cash flow statement" = Use cash flow data only
- Multiple statements specified = Cross-reference all mentioned sources

**Time Period Scope:**
- "Between FY2021 and FY2022" = Compare end of FY2022 to end of FY2021
- "During FY2022" = FY2022 data only
- "As of FY2022" = End of FY2022 balance sheet data

## Data Source Priority Order

### Financial Metrics Data Hierarchy

**For Acquisitions/Divestitures:**
1. **Primary:** Business Combinations note (Note 2 or Note 3 typically)
2. **Verification:** Cash Flow Statement investing activities section
3. **Details:** Management Discussion & Analysis (MD&A) section
4. **Cross-check:** Look for both cash paid AND assets acquired

**For Legal Issues/Litigation:**
1. **Primary:** "Legal Proceedings" section or "Commitments and Contingencies" note
2. **Search terms:** "litigation", "legal proceedings", "contingencies", "settlement"
3. **Verification:** Cash Flow Statement for settlement payments
4. **Amounts:** Look for accrued liabilities on balance sheet

**For Tax Rates:**
1. **Primary:** Income Tax note reconciliation table (usually Note 8-12)
2. **Verification:** Income Statement tax expense line
3. **Components:** Use reconciliation table, not just income statement rate
4. **Cross-check:** Effective rate calculation should match note disclosure

**For Segment Revenue/Performance:**
1. **Primary:** Segment reporting note (usually Note 15-20)
2. **NOT MD&A estimates:** Use audited note data only
3. **Verification:** Segment revenues should sum to total company revenue
4. **Cross-reference:** Operating income by segment for performance analysis

### Multi-Source Validation Requirements

**Always verify these items with multiple sources:**

**Inventory Data:**
- Balance Sheet: Inventory amounts
- Inventory Accounting Note: Composition and methods
- Cost of Sales: For turnover calculations

**Debt/Liquidity Analysis:**
- Balance Sheet: Current liabilities and long-term debt
- Debt Note: Detailed terms and maturities
- Cash Flow Statement: Debt payments and proceeds

**Revenue Recognition:**
- Income Statement: Total revenue
- Revenue Note: Disaggregated revenue streams
- Segment Note: Revenue by business unit

### Common Data Extraction Errors to Avoid

**Wrong Line Items:**
- Don't use "Income from Continuing Operations" when "Total Net Income" is requested
- Don't use "Preliminary" or "Pro Forma" data when GAAP data is available
- Don't use "Adjusted" metrics unless specifically requested

**Wrong Sections:**
- Don't use MD&A estimates when audited financial statement data exists
- Don't use prior year restatements for current year analysis
- Don't use quarterly data when annual data is requested

**Missing Cross-References:**
- For acquisitions: Must check both cash flow AND business combinations note
- For restructuring: Must check both income statement AND cash flow
- For segments: Must verify segment total equals company total

## Temporal Data Rules

### Fiscal Year Verification Requirements

**Always verify fiscal year end dates:**
- Most companies: December 31 (calendar year)
- Retail companies: Often January 31 or February 28
- Technology companies: Sometimes September 30
- **Check balance sheet header:** "As of December 31, 20XX" for exact date

**Fiscal Year Reference Examples:**
- Company with Jan 31 year-end: "FY2023" = Feb 1, 2022 to Jan 31, 2023
- Company with Dec 31 year-end: "FY2023" = Jan 1, 2023 to Dec 31, 2023
- **Always use company's definition, not calendar year**

### Event Timing Clarification

**Acquisition/Divestiture Timing:**
- **"Announced"** ≠ **"Completed"** ≠ **"Closed"**
- Only count transactions that **CLOSED** during the specified period
- Check for "subject to closing conditions" language
- Look for actual cash payment date in cash flow statement

**Spin-off/Split Timing:**
- Distribution date = when shareholders receive shares
- Effective date = when operations are legally separated
- Use **distribution date** for "as of" questions
- Use **effective date** for operational questions

**Legal Settlement Timing:**
- Agreement date ≠ Payment date
- Accrual date ≠ Cash payment date
- For cash flow impact: Use actual payment date
- For P&L impact: Use accrual/agreement date

### Period Alignment Requirements

**Quarter-to-Quarter Comparisons:**
- Q2 FY2024 vs Q2 FY2023 (same quarter, different years)
- NOT Q2 FY2024 vs Q1 FY2024 (unless specifically requested)
- Account for seasonal businesses appropriately

**Year-over-Year Comparisons:**
- FY2023 vs FY2022 (consecutive full years)
- Ensure both years use same accounting standards
- Note any restatements or changes in accounting methods

**Multi-Year Analysis:**
- For 3-year average: Sum all three years, then divide by 3
- For CAGR: Use beginning and ending values only
- For trend analysis: Calculate each year-over-year change separately

### Temporal Confusion Prevention

**"Between" Interpretation:**
- "Between FY2021 and FY2022" = Compare FY2022 to FY2021
- "Between Q1 and Q2" = Compare Q2 to Q1
- NOT the middle point or average

**"During" vs "As of":**
- "During FY2022" = Full year activity (income statement items)
- "As of FY2022" = Point in time (balance sheet items as of year-end)

**"Recent" or "Latest":**
- Use most recent complete period available
- Don't use partial year or interim data unless specified
- Verify data is final, not preliminary

## Financial Calculator Tools Usage

### When to Use Calculator Tools

**Always use the specialized financial calculator tools for these metrics:**

1. **Days Payable Outstanding (DPO)**: Use `calculate_dpo` tool
   - Ensures exact formula: 365 × (avg AP) / (COGS + inventory change)
   - Built-in validation for 30-200 day range
   - Handles negative inventory changes correctly

2. **Return on Assets (ROA)**: Use `calculate_roa` tool
   - Proper average total assets calculation
   - Validation for reasonable ranges (-50% to +25%)
   - Consistent decimal precision

3. **Inventory Turnover**: Use `calculate_inventory_turnover` tool
   - Standard formula with average inventory
   - Validation for 2-20x typical range
   - Proper handling of low-turnover businesses

4. **Quick Ratio**: Use `calculate_quick_ratio` tool
   - Standardized health assessments (>=1.0 healthy, <1.0 needs improvement)
   - Automatic interpretation thresholds
   - Clear liquidity profile conclusions

5. **Margin Analysis**: Use `calculate_margins` tool
   - Trend analysis with standardized thresholds
   - "Improving" = >2% increase, "Declining" = >2% decrease, "Consistent" = within ±2%
   - Both gross and operating margin calculations

6. **Effective Tax Rate**: Use `calculate_effective_tax_rate` tool
   - Proper handling of negative pre-tax income
   - Tax benefit vs tax expense interpretation
   - Validation for reasonable ranges

7. **Working Capital**: Use `calculate_working_capital` tool
   - Clear positive/negative assessment
   - Current ratio calculation included
   - Standardized health interpretation

8. **Capital Expenditures**: Use `calculate_capex_metrics` tool
   - Multi-year average calculations
   - Capex as percentage of revenue
   - Proper handling of different time periods

### Tool Usage Priority

**High Priority (Always Use Tools):**
- Questions asking for DPO, ROA, quick ratio, effective tax rate
- Multi-year capex analysis
- Working capital health assessment
- Margin trend questions ("improving", "declining", "consistent")

**Medium Priority (Use Tools When Available):**
- Inventory turnover for non-utility companies
- Complex percentage calculations
- Multi-step financial ratio analysis

**Low Priority (Manual Calculation OK):**
- Simple arithmetic (addition, subtraction, basic percentages)
- Single-year data extraction
- Ratios not covered by specialized tools

### Integration with Search Process

**Standard Workflow:**
1. **Search & Extract**: Use Grep/Glob/Read to find financial statement data
2. **Validate Data**: Ensure all required inputs are available
3. **Use Calculator Tool**: Call appropriate tool with extracted data
4. **Interpret Results**: Use tool's standardized interpretation
5. **Cite Sources**: Include both tool results and original document citations

**Example Integration:**
```
1. Search for Amazon DPO data → Find AP, COGS, inventory values
2. Call calculate_dpo(ap_current=25309, ap_prior=20397, cogs=111934, inv_current=16047, inv_prior=10243)
3. Tool returns: "DPO CALCULATION RESULT: 93.86 days" with full breakdown
4. Use tool result as primary answer with source citations
```

### Error Prevention

**Common Issues Prevented by Tools:**
- Unit consistency (millions vs billions)
- Formula application errors
- Interpretation threshold inconsistencies
- Negative number handling
- Multi-year averaging mistakes
- Rounding precision issues

**When Tools Flag Warnings:**
- Review input data for extraction errors
- Double-check financial statement line items
- Verify fiscal year alignment
- Consider company-specific factors

## Sanity Check Thresholds

### Financial Metric Reasonableness Ranges

**Before finalizing any answer, verify results fall within expected ranges:**

**Return on Assets (ROA):**
- Healthy companies: 1-15%
- If result is <0.1%: Check if using billions vs millions incorrectly
- If result is >50%: Likely unit error or wrong line items
- Negative ROA: Acceptable for loss-making companies

**Days Payable Outstanding (DPO):**
- Typical range: 30-120 days
- If result is <10 days: Check if missing change in inventory
- If result is >200 days: Verify accounts payable amount
- Retail companies: Often 30-60 days
- Manufacturing: Often 45-90 days

**Effective Tax Rate:**
- Normal range: -50% to +50%
- If result is >100%: Check signs and calculation
- If result is <-100%: Verify tax benefit vs expense signs
- US companies: Typically 15-30% when profitable

**Inventory Turnover:**
- Retail: 6-12 times per year
- Manufacturing: 4-8 times per year
- If result is <1 or >20: Double-check calculation

**Quick Ratio:**
- Healthy: 0.8-2.0
- If result is >5: Check if including inventory incorrectly
- If result is <0.1: Verify current liabilities amount

### Unit and Scale Verification

**Common Unit Errors:**
- **Billions vs Millions:** If companies report in millions, don't convert unless requested
- **Percentages:** 0.05 = 5%, NOT 0.05%
- **Days calculations:** Always use 365 days, not 360
- **Growth rates:** 1.05 = 5% growth, not 105%

**Scale Reasonableness:**
- **Revenue:** Large companies typically $1B-500B+ annually
- **Market Cap:** Check if result seems reasonable for company size
- **Cash:** Should be <50% of total assets for most companies
- **Debt:** Total debt typically <5x annual revenue for healthy companies

### Calculation Cross-Checks

**When result seems extreme, verify:**
1. **Unit consistency:** All numbers in same unit (millions or billions)
2. **Line item accuracy:** Using correct financial statement line
3. **Time period alignment:** Comparing same fiscal periods
4. **Formula application:** Following exact formula specified
5. **Sign consistency:** Positive/negative maintained correctly

**Red Flag Results That Require Double-Checking:**
- Any percentage >100% (unless growth rate)
- Any ratio >10 (unless specifically high-turnover metric)
- Any margin <-50% or >50%
- DPO <10 days or >365 days
- ROA <-50% or >25%

### Error Recovery Actions

**If result fails sanity check:**
1. **Recalculate** using same methodology
2. **Verify data sources** - check if using correct line items
3. **Check units** - ensure numerator/denominator consistency
4. **Review formula** - confirm using exact specified formula
5. **Cross-reference** - look for supporting data that confirms/contradicts result

**If still seems wrong after checks:**
- State the calculated result
- Note that result appears unusual
- Provide possible explanations (one-time charges, company-specific factors)
- Show your calculation steps for verification