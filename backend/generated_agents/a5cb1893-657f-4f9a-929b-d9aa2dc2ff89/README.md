# Loan Underwriting Risk Assessment Pipeline

A multi-agent pipeline built with CrewAI that automates loan underwriting risk assessment. The pipeline extracts financial data from bank statements and credit reports, calculates key financial ratios (DTI, LTV), evaluates underwriting rules, generates a comprehensive risk assessment report, and distributes it via email and database archival.

## Architecture

The pipeline consists of 5 sequential agents:

1. **Data Extraction Agent** — Parses bank statements and credit reports (PDF, CSV, XML, or inline JSON)
2. **Financial Ratio Agent** — Calculates DTI, LTV, and supplementary financial metrics
3. **Underwriting Rules Agent** — Evaluates rules (DTI ≤ 43%, LTV ≤ 80%, credit score ≥ 620, income > 0) and produces approve/deny/manual_review decision
4. **Report Generation Agent** — Generates a formatted risk assessment report
5. **Distribution Agent** — Emails the report and archives it to a database

## Prerequisites

- Python 3.10+
- An OpenRouter API key (or OpenAI API key)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Set your API key in `.env`:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

3. (Optional) Configure SMTP settings for actual email delivery. Without SMTP configuration, email sending is simulated.

4. (Optional) Configure `DATABASE_URL` for a production database. Defaults to `sqlite:///output.db`.

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

The pipeline accepts 4 inputs:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bank_statements` | string | Yes | JSON string or file path to bank statement data |
| `credit_reports` | string | Yes | JSON string or file path to credit report data |
| `loan_amount` | number | Yes | Requested loan amount in dollars |
| `property_value` | number | Yes | Appraised property value in dollars |

### Sample Input
```json
{
  "bank_statements": "{\"account_holder_name\": \"John Doe\", \"monthly_income\": 3000.0}",
  "credit_reports": "{\"applicant_name\": \"John Doe\", \"credit_score\": 720}",
  "loan_amount": 250000.0,
  "property_value": 312500.0
}
```

## Output Format

The pipeline produces:

| Field | Type | Description |
|-------|------|-------------|
| `risk_assessment_report` | string | The full risk assessment report content |
| `email_status` | string | Status of email delivery (success/failure) |
| `database_status` | string | Status of database archival (success/failure) |

## Underwriting Rules

- **DTI Ratio** ≤ 43% (severity: high, weight: 0.30)
- **LTV Ratio** ≤ 80% (severity: high, weight: 0.25)
- **Credit Score** ≥ 620 (severity: high, weight: 0.30)
- **Income Verification** > $0 (severity: critical, weight: 0.15)

## Decision Logic

- **Approve**: All rules pass and composite risk score is favorable
- **Deny**: Critical rules fail
- **Manual Review**: Borderline cases where some rules fail but overall profile has merit
