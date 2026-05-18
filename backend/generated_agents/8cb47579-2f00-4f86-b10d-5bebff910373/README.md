# Loan Underwriting Risk Assessment Pipeline

## Prerequisites

- Python 3.8+
- pip
- An OpenRouter API key

## Environment Variables

Create a `.env` file in the root directory with the following content:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Installation

1. Clone the repository.
2. Navigate to the project directory.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Pipeline

To execute the pipeline, run the following command:

```bash
python main.py
```

## Expected Input

The pipeline expects input in the following JSON format:

```json
{
  "bank_statements": {
    "transactions": [
      {
        "transaction_date": "2023-01-01",
        "transaction_description": "Deposit",
        "transaction_amount": 1000.0,
        "account_balance": 5000.0,
        "account_type": "Checking"
      },
      {
        "transaction_date": "2023-01-15",
        "transaction_description": "Mortgage Payment",
        "transaction_amount": -1200.0,
        "account_balance": 3800.0,
        "account_type": "Checking"
      }
    ]
  },
  "credit_reports": {
    "credit_accounts": [
      {
        "account_name": "Visa",
        "payment_history": "On-time",
        "credit_limit": 5000,
        "current_balance": 1500,
        "credit_score": 720
      },
      {
        "account_name": "Mortgage",
        "payment_history": "On-time",
        "credit_limit": 250000,
        "current_balance": 200000,
        "credit_score": 720
      }
    ]
  }
}
```

## Output

The pipeline will output a JSON object containing the risk assessment report and a PDF report:

```json
{
  "risk_assessment_report": { ... },
  "report_pdf": "PDF content"
}
```
