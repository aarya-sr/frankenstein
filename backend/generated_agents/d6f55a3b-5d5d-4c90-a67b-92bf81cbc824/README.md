# Loan Underwriting Risk Assessment Pipeline

## Prerequisites
- Python 3.8+
- `pip` package manager

## Environment Variables
- `OPENROUTER_API_KEY`: Your API key for OpenRouter.

## Installation
1. Clone the repository.
2. Navigate to the project directory.
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline
1. Ensure your environment variables are set. You can copy `.env.example` to `.env` and fill in your API key.
2. Run the pipeline:
   ```bash
   python main.py
   ```

## Expected Input
The input should be a JSON object with the following structure:
```json
{
  "bank_statements_path": "/path/to/bank_statements.pdf",
  "credit_reports_path": "/path/to/credit_report.pdf"
}
```

## Expected Output
The output will be a JSON object containing the risk assessment report:
```json
{
  "risk_assessment_report": {
    "dti_ratio": 0.3,
    "ltv_ratio": 0.7,
    "underwriting_decision": "Approved",
    "decision_rationale": "DTI and LTV within acceptable limits",
    "risk_metrics": {}
  },
  "report_format": "json"
}
```
