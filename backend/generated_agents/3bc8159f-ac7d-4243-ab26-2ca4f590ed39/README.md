# Loan Underwriting Risk Assessment

An AI-powered loan underwriting pipeline built with CrewAI that automates the risk assessment process for mortgage applications.

## Overview

This pipeline processes bank statements and credit reports through a sequential chain of specialized AI agents:

1. **Data Extraction Agent** — Parses and normalizes financial documents into a unified JSON structure
2. **Financial Calculation Agent** — Computes DTI, LTV, and income stability metrics
3. **Underwriting Rules Agent** — Evaluates metrics against lending criteria and produces a composite risk score
4. **Report Generation Agent** — Compiles a comprehensive risk assessment report
5. **Report Delivery Agent** — Sends the report via email and stores it in a database (simulated)

## Prerequisites

- Python 3.10+
- An API key for OpenRouter (or OpenAI directly)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

## Running

### Command Line

```bash
python main.py
```

This loads input from `sample_data.json` and runs the full pipeline.

### Web UI (Streamlit)

```bash
streamlit run app.py
```

This opens a browser-based interface where you can edit inputs and run the pipeline interactively.

## Input Format

```json
{
  "bank_statements": [
    {
      "account_holder_name": "John Doe",
      "account_number": "123456789",
      "transaction_date": "2023-01-15",
      "transaction_description": "Deposit",
      "transaction_amount": 1500.0,
      "balance": 5000.0,
      "monthly_income": 4500.0
    }
  ],
  "credit_reports": [
    {
      "credit_score": 720,
      "total_outstanding_debt": 15000.0,
      "payment_history": [
        {"date": "2022-12-01", "status": "on-time"},
        {"date": "2023-01-01", "status": "late"}
      ],
      "credit_utilization_ratio": 30,
      "number_of_open_accounts": 5,
      "public_records": []
    }
  ],
  "loan_amount": 200000.0,
  "property_value": 250000.0
}
```

## Output Format

The pipeline produces a JSON report with the following structure:

```json
{
  "applicant_information": {
    "name": "John Doe",
    "monthly_income": 4500.0
  },
  "financial_data_summary": {
    "DTI": 27.78,
    "LTV": 80.0,
    "monthly_income": 4500.0,
    "income_stability": "insufficient_data"
  },
  "credit_score_analysis": {
    "credit_score": 720,
    "risk_score": 0.35,
    "risk_level": "Medium",
    "risk_factors": []
  },
  "underwriting_rules_applied": [
    {"rule": "DTI_threshold", "passed": true, "value": 27.78, "threshold": 36},
    {"rule": "LTV_threshold", "passed": false, "value": 80.0, "threshold": 80},
    {"rule": "credit_score_minimum", "passed": true, "value": 720, "threshold": 620},
    {"rule": "income_verification", "passed": true, "value": 4500.0, "threshold": 0}
  ],
  "recommendation": "refer",
  "notes": "Risk assessment completed for John Doe. Overall risk level: Medium (score: 0.35). Failed rules: LTV_threshold."
}
```

## Architecture

- `tools.py` — All tool functions (parsers, calculators, engines, report generator, delivery)
- `agents.py` — CrewAI Agent definitions with assigned tools
- `tasks.py` — Task definitions with description templates and context chains
- `orchestration.py` — Crew assembly with sequential process
- `main.py` — CLI entry point
- `app.py` — Streamlit web UI
