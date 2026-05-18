# Loan Underwriting Risk Assessment

Automated loan underwriting pipeline powered by CrewAI. This system extracts financial data from documents, calculates risk ratios, evaluates against underwriting rules, generates a comprehensive risk assessment report, and stores results securely.

## Architecture

The pipeline follows a strict sequential flow with 5 specialized agents:

1. **Data Extraction Agent** — Parses bank statements (PDF), credit reports (PDF), and structured financial data (CSV)
2. **Risk Calculation Agent** — Computes DTI, LTV, income stability, overdraft frequency, and statistical analysis
3. **Underwriting Rules Agent** — Evaluates compliance against underwriting rules and produces composite risk scores
4. **Report Generation Agent** — Generates a comprehensive risk assessment report
5. **Storage Agent** — Persists the report to a database with full audit metadata

## Prerequisites

- Python 3.10+
- An API key for OpenRouter or OpenAI

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

```bash
cp .env.example .env
# Edit .env and add your API key
```

Set one of:
- `OPENROUTER_API_KEY` — for OpenRouter (recommended)
- `OPENAI_API_KEY` — for direct OpenAI access

Optionally set:
- `DATABASE_URL` — database connection string (defaults to `sqlite:///output.db`)

## Running

### Command Line

```bash
python main.py
```

### Streamlit Web UI

```bash
streamlit run app.py
```

## Input Format

The pipeline expects three file paths:

```json
{
  "bank_statements": "bank_statement.pdf",
  "credit_reports": "credit_report.pdf",
  "structured_financial_data": "financial_data.csv"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bank_statements` | string | Yes | Path to bank statement PDF file |
| `credit_reports` | string | Yes | Path to credit report PDF file |
| `structured_financial_data` | string | Yes | Path to structured financial CSV file |

## Output Format

```json
{
  "result": "<string containing risk_assessment_report path and storage_confirmation>"
}
```

The pipeline produces:
- `risk_assessment_report` — File path to the generated risk assessment report (Markdown format)
- `storage_confirmation` — Confirmation message with record ID and timestamp

## Tools

| Tool | Description |
|------|-------------|
| PDF Parser Bank Statement | Extracts text/tables from bank statement PDFs (PyMuPDF) |
| PDF Parser Credit Report | Extracts text/tables from credit report PDFs (PyMuPDF) |
| CSV Parser Financial | Parses structured financial CSV into JSON records |
| Financial Calculator | Computes DTI, LTV, income stability, overdraft frequency |
| Statistical Analyzer | Computes mean, median, std dev, outliers, trends |
| Rule Engine | Evaluates against underwriting rules (DTI≤43%, LTV≤80%, credit≥620, stability≥70%) |
| Scoring Engine | Produces weighted composite risk score |
| Report Generator | Generates structured risk assessment report |
| Database Writer | Persists report with audit metadata to SQL database |

## Underwriting Rules

| Rule | Condition | Severity |
|------|-----------|----------|
| DTI Check | DTI ≤ 0.43 | High |
| LTV Check | LTV ≤ 0.80 | High |
| Credit Score Check | Credit Score ≥ 620 | High |
| Income Stability Check | Income Stability ≥ 0.70 | Medium |

## Composite Score Weights

| Metric | Weight |
|--------|--------|
| DTI Score | 30% |
| LTV Score | 25% |
| Credit Score (normalized) | 25% |
| Income Stability Score | 20% |
