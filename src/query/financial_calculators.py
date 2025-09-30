"""
Financial Calculator Tools for FinanceBench RAG Agent

This module provides specialized financial calculation tools using Claude Code SDK
to ensure accuracy and consistency in financial metric calculations.
"""

import json
import os
from claude_agent_sdk import tool


@tool("calculate_dpo", "Calculate Days Payable Outstanding with validation", {
    "accounts_payable_current": float,
    "accounts_payable_prior": float,
    "cogs": float,
    "inventory_current": float,
    "inventory_prior": float
})
async def calculate_dpo(args):
    """Calculate Days Payable Outstanding (DPO) using the exact formula with validation."""

    ap_current = args["accounts_payable_current"]
    ap_prior = args["accounts_payable_prior"]
    cogs = args["cogs"]
    inv_current = args["inventory_current"]
    inv_prior = args["inventory_prior"]

    # Calculate components
    avg_accounts_payable = (ap_current + ap_prior) / 2
    inventory_change = inv_current - inv_prior
    denominator = cogs + inventory_change

    # Apply DPO formula
    dpo = 365 * avg_accounts_payable / denominator

    # Validation
    validation_msg = ""
    if dpo < 10 or dpo > 365:
        validation_msg = f" [WARNING: DPO of {dpo:.2f} days is outside typical range of 30-200 days]"

    result_text = f"""DPO CALCULATION RESULT: {dpo:.2f} days{validation_msg}

CALCULATION BREAKDOWN:
- Average Accounts Payable = (${ap_current:,.0f}M + ${ap_prior:,.0f}M) / 2 = ${avg_accounts_payable:,.0f}M
- Change in Inventory = ${inv_current:,.0f}M - ${inv_prior:,.0f}M = ${inventory_change:,.0f}M
- Denominator = COGS + Inventory Change = ${cogs:,.0f}M + ${inventory_change:,.0f}M = ${denominator:,.0f}M
- DPO = 365 × ${avg_accounts_payable:,.0f}M / ${denominator:,.0f}M = {dpo:.2f} days"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_roa", "Calculate Return on Assets with validation", {
    "net_income": float,
    "total_assets_current": float,
    "total_assets_prior": float
})
async def calculate_roa(args):
    """Calculate Return on Assets (ROA) with proper averaging and validation."""

    net_income = args["net_income"]
    assets_current = args["total_assets_current"]
    assets_prior = args["total_assets_prior"]

    # Calculate average total assets
    avg_total_assets = (assets_current + assets_prior) / 2

    # Calculate ROA
    roa = net_income / avg_total_assets
    roa_percent = roa * 100

    # Validation
    validation_msg = ""
    if abs(roa_percent) > 25:
        validation_msg = f" [WARNING: ROA of {roa_percent:.2f}% is unusually high - verify inputs]"

    result_text = f"""ROA CALCULATION RESULT: {roa:.4f} ({roa_percent:.2f}%){validation_msg}

CALCULATION BREAKDOWN:
- Net Income = ${net_income:,.0f}M
- Average Total Assets = (${assets_current:,.0f}M + ${assets_prior:,.0f}M) / 2 = ${avg_total_assets:,.0f}M
- ROA = Net Income / Average Total Assets = ${net_income:,.0f}M / ${avg_total_assets:,.0f}M = {roa:.4f}"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_inventory_turnover", "Calculate inventory turnover ratio", {
    "cogs": float,
    "inventory_current": float,
    "inventory_prior": float
})
async def calculate_inventory_turnover(args):
    """Calculate inventory turnover ratio with validation."""

    cogs = args["cogs"]
    inv_current = args["inventory_current"]
    inv_prior = args["inventory_prior"]

    # Calculate average inventory
    avg_inventory = (inv_current + inv_prior) / 2

    # Calculate turnover
    turnover = cogs / avg_inventory

    # Validation
    validation_msg = ""
    if turnover < 1 or turnover > 50:
        validation_msg = f" [WARNING: Turnover of {turnover:.2f}x is outside typical range of 2-20x]"

    result_text = f"""INVENTORY TURNOVER RESULT: {turnover:.2f} times{validation_msg}

CALCULATION BREAKDOWN:
- Cost of Goods Sold = ${cogs:,.0f}M
- Average Inventory = (${inv_current:,.0f}M + ${inv_prior:,.0f}M) / 2 = ${avg_inventory:,.0f}M
- Inventory Turnover = COGS / Average Inventory = ${cogs:,.0f}M / ${avg_inventory:,.0f}M = {turnover:.2f}x"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_quick_ratio", "Calculate quick ratio with health assessment", {
    "cash": float,
    "marketable_securities": float,
    "accounts_receivable": float,
    "current_liabilities": float
})
async def calculate_quick_ratio(args):
    """Calculate quick ratio with standardized health assessment."""

    cash = args["cash"]
    marketable_securities = args["marketable_securities"]
    accounts_receivable = args["accounts_receivable"]
    current_liabilities = args["current_liabilities"]

    # Calculate quick assets
    quick_assets = cash + marketable_securities + accounts_receivable

    # Calculate quick ratio
    quick_ratio = quick_assets / current_liabilities

    # Health assessment
    if quick_ratio >= 1.5:
        health_status = "STRONG - Excellent liquidity position"
    elif quick_ratio >= 1.0:
        health_status = "HEALTHY - Adequate liquidity to meet obligations"
    elif quick_ratio >= 0.8:
        health_status = "ACCEPTABLE - Reasonable liquidity but could improve"
    else:
        health_status = "NEEDS IMPROVEMENT - Below healthy liquidity threshold"

    result_text = f"""QUICK RATIO RESULT: {quick_ratio:.2f} - {health_status}

CALCULATION BREAKDOWN:
- Cash and Cash Equivalents = ${cash:,.0f}M
- Marketable Securities = ${marketable_securities:,.0f}M
- Accounts Receivable = ${accounts_receivable:,.0f}M
- Total Quick Assets = ${quick_assets:,.0f}M
- Current Liabilities = ${current_liabilities:,.0f}M
- Quick Ratio = ${quick_assets:,.0f}M / ${current_liabilities:,.0f}M = {quick_ratio:.2f}

INTERPRETATION:
- Quick ratio >= 1.0 = Healthy liquidity
- Quick ratio < 1.0 = Needs improvement
- Current ratio of {quick_ratio:.2f} indicates company can cover {quick_ratio*100:.0f}% of current liabilities with liquid assets"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_margins", "Calculate and analyze margin trends", {
    "revenue_current": float,
    "revenue_prior": float,
    "cogs_current": float,
    "cogs_prior": float,
    "operating_income_current": float,
    "operating_income_prior": float
})
async def calculate_margins(args):
    """Calculate margin trends with standardized interpretation."""

    rev_curr = args["revenue_current"]
    rev_prior = args["revenue_prior"]
    cogs_curr = args["cogs_current"]
    cogs_prior = args["cogs_prior"]
    op_inc_curr = args["operating_income_current"]
    op_inc_prior = args["operating_income_prior"]

    # Calculate margins
    gross_margin_curr = ((rev_curr - cogs_curr) / rev_curr) * 100
    gross_margin_prior = ((rev_prior - cogs_prior) / rev_prior) * 100

    op_margin_curr = (op_inc_curr / rev_curr) * 100
    op_margin_prior = (op_inc_prior / rev_prior) * 100

    # Calculate changes
    gross_margin_change = gross_margin_curr - gross_margin_prior
    op_margin_change = op_margin_curr - op_margin_prior

    # Trend analysis
    def analyze_trend(change):
        if abs(change) <= 2.0:
            return "CONSISTENT"
        elif change > 2.0:
            return "IMPROVING"
        else:
            return "DECLINING"

    gross_trend = analyze_trend(gross_margin_change)
    op_trend = analyze_trend(op_margin_change)

    result_text = f"""MARGIN ANALYSIS RESULT:

GROSS MARGIN TREND: {gross_trend}
- Current Period: {gross_margin_curr:.2f}%
- Prior Period: {gross_margin_prior:.2f}%
- Change: {gross_margin_change:+.2f} percentage points

OPERATING MARGIN TREND: {op_trend}
- Current Period: {op_margin_curr:.2f}%
- Prior Period: {op_margin_prior:.2f}%
- Change: {op_margin_change:+.2f} percentage points

INTERPRETATION CRITERIA:
- CONSISTENT: Change within ±2.0 percentage points
- IMPROVING: Increase > 2.0 percentage points
- DECLINING: Decrease > 2.0 percentage points"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_effective_tax_rate", "Calculate effective tax rate handling negative income", {
    "income_tax_expense": float,
    "income_before_tax": float
})
async def calculate_effective_tax_rate(args):
    """Calculate effective tax rate with proper handling of negative income and tax benefits."""

    tax_expense = args["income_tax_expense"]
    income_before_tax = args["income_before_tax"]

    # Calculate effective tax rate
    if income_before_tax == 0:
        return {
            "content": [{"type": "text", "text": "ERROR: Cannot calculate effective tax rate with zero pre-tax income"}],
            "isError": True
        }

    effective_rate = (tax_expense / income_before_tax) * 100

    # Interpretation
    if income_before_tax > 0 and tax_expense > 0:
        interpretation = "Normal tax expense on positive income"
    elif income_before_tax > 0 and tax_expense < 0:
        interpretation = "Tax benefit on positive income (unusual - check for credits/refunds)"
    elif income_before_tax < 0 and tax_expense > 0:
        interpretation = "Tax expense on loss (unusual - check for non-deductible items)"
    else:  # income < 0 and tax < 0
        interpretation = "Tax benefit on loss (normal)"

    result_text = f"""EFFECTIVE TAX RATE RESULT: {effective_rate:.2f}%

CALCULATION BREAKDOWN:
- Income Tax Expense: ${tax_expense:,.0f}M
- Income Before Tax: ${income_before_tax:,.0f}M
- Effective Tax Rate = ${tax_expense:,.0f}M / ${income_before_tax:,.0f}M × 100 = {effective_rate:.2f}%

INTERPRETATION: {interpretation}

NOTE: Negative rates indicate tax benefits; positive rates indicate tax expense"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_working_capital", "Calculate working capital with health assessment", {
    "current_assets": float,
    "current_liabilities": float
})
async def calculate_working_capital(args):
    """Calculate working capital with standardized health assessment."""

    current_assets = args["current_assets"]
    current_liabilities = args["current_liabilities"]

    # Calculate working capital
    working_capital = current_assets - current_liabilities
    current_ratio = current_assets / current_liabilities if current_liabilities != 0 else 0

    # Health assessment
    if working_capital > 0:
        health_status = "POSITIVE - Company has adequate short-term liquidity"
        answer = "Yes, the company has positive working capital"
    else:
        health_status = "NEGATIVE - Company may face short-term liquidity challenges"
        answer = "No, the company has negative working capital"

    result_text = f"""WORKING CAPITAL RESULT: {answer}

CALCULATION BREAKDOWN:
- Current Assets: ${current_assets:,.0f}M
- Current Liabilities: ${current_liabilities:,.0f}M
- Working Capital = ${current_assets:,.0f}M - ${current_liabilities:,.0f}M = ${working_capital:,.0f}M
- Current Ratio = {current_ratio:.2f}

HEALTH ASSESSMENT: {health_status}

INTERPRETATION:
- Positive working capital indicates company can meet short-term obligations
- Current ratio > 1.0 generally indicates healthy liquidity position"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("calculate_capex_metrics", "Calculate capital expenditure metrics and averages", {
    "capex_values": list,
    "revenue_values": list,
    "years": list
})
async def calculate_capex_metrics(args):
    """Calculate capex as percentage of revenue and multi-year averages."""

    capex_values = args["capex_values"]
    revenue_values = args["revenue_values"]
    years = args["years"]

    if len(capex_values) != len(revenue_values) or len(capex_values) != len(years):
        return {
            "content": [{"type": "text", "text": "ERROR: Capex values, revenue values, and years must have same length"}],
            "isError": True
        }

    # Calculate capex as % of revenue for each year
    capex_percentages = []
    for i, (capex, revenue) in enumerate(zip(capex_values, revenue_values)):
        if revenue == 0:
            return {
                "content": [{"type": "text", "text": f"ERROR: Zero revenue in year {years[i]}"}],
                "isError": True
            }
        pct = (capex / revenue) * 100
        capex_percentages.append(pct)

    # Calculate average
    avg_percentage = sum(capex_percentages) / len(capex_percentages)

    # Build result
    breakdown_lines = []
    for i, (year, capex, revenue, pct) in enumerate(zip(years, capex_values, revenue_values, capex_percentages)):
        breakdown_lines.append(f"- {year}: ${capex:,.0f}M / ${revenue:,.0f}M = {pct:.2f}%")

    result_text = f"""CAPEX METRICS RESULT: {avg_percentage:.1f}% average

YEAR-BY-YEAR BREAKDOWN:
{chr(10).join(breakdown_lines)}

MULTI-YEAR AVERAGE: {avg_percentage:.1f}%

CALCULATION:
- Sum of percentages: {sum(capex_percentages):.2f}%
- Number of years: {len(capex_percentages)}
- Average: {avg_percentage:.1f}%"""

    return {
        "content": [{"type": "text", "text": result_text}]
    }


@tool("find_company_documents", "Find available documents for a company", {
    "company": str,
    "year": int,
    "doc_type": str  # "10k", "10q", or "any"
})
async def find_company_documents(args):
    """Find available financial documents for a company using the document information index."""

    company = args["company"].lower()
    year = args.get("year")
    doc_type = args.get("doc_type", "any").lower()

    # Load document information
    doc_info_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "financebench_document_information.jsonl"
    )

    try:
        with open(doc_info_file, 'r', encoding='utf-8') as f:
            documents = []
            for line in f:
                doc = json.loads(line.strip())

                # Filter by company (case-insensitive partial match)
                if company not in doc.get("company", "").lower():
                    continue

                # Filter by year if specified
                if year and doc.get("doc_period") != year:
                    continue

                # Filter by document type if specified
                if doc_type != "any" and doc.get("doc_type", "").lower() != doc_type:
                    continue

                documents.append(doc)

        if not documents:
            result_text = f"No documents found for company '{args['company']}'"
            if year:
                result_text += f" in year {year}"
            if doc_type != "any":
                result_text += f" with document type {doc_type}"
        else:
            result_text = f"FOUND {len(documents)} DOCUMENTS FOR {args['company'].upper()}:\n\n"

            # Group by year for better organization
            by_year = {}
            for doc in documents:
                year_key = doc.get("doc_period", "Unknown")
                if year_key not in by_year:
                    by_year[year_key] = []
                by_year[year_key].append(doc)

            for year_key in sorted(by_year.keys(), reverse=True):
                year_docs = by_year[year_key]
                result_text += f"**{year_key}:**\n"
                for doc in year_docs:
                    doc_name = doc.get("doc_name", "Unknown")
                    doc_type_info = doc.get("doc_type", "").upper()
                    result_text += f"  - {doc_name} ({doc_type_info})\n"
                result_text += "\n"

            # Build markdown file paths
            markdown_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                ".finance", "markdown"
            )

            result_text += "**MARKDOWN FILE PATHS:**\n"
            for year_key in sorted(by_year.keys(), reverse=True):
                year_docs = by_year[year_key]
                result_text += f"\n{year_key}:\n"
                for doc in year_docs:
                    doc_name = doc.get("doc_name", "Unknown")
                    md_path = f".finance/markdown/{doc_name}.md"
                    # Check if file exists
                    full_path = os.path.join(markdown_dir, f"{doc_name}.md")
                    if os.path.exists(full_path):
                        result_text += f"  - {md_path} [EXISTS]\n"
                    else:
                        result_text += f"  - {md_path} [NOT FOUND]\n"

            result_text += f"\n**GLOB PATTERN:** .finance/markdown/*{args['company'].replace(' ', '*')}*{year if year else '*'}*.md\n"

        return {
            "content": [{"type": "text", "text": result_text}]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error accessing document information: {str(e)}"}],
            "isError": True
        }