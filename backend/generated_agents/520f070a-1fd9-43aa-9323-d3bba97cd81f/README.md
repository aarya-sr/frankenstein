# Loan Underwriting Risk Assessment Pipeline

## Prerequisites
- Python 3.8+
- An OpenRouter API key

## Environment Variables
Create a `.env` file in the root directory with the following content:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python main.py
```

## Expected Input
The input should be a JSON object with the following structure:

```json
{
  "bank_statements": "path/to/bank_statement.pdf",
  "credit_reports": "path/to/credit_report.pdf"
}
```

## Expected Output
The output will be a JSON object containing:

- `recommendation`: A string indicating the loan recommendation (e.g., "approve", "deny", "manual_review").
- `DTI`: The calculated Debt-to-Income ratio.
- `LTV`: The calculated Loan-to-Value ratio.
- `creditScore`: The evaluated credit score.
- `storage_location`: The path where the report is stored.
- `notification_status`: The status of the notification sent to the loan officer.
