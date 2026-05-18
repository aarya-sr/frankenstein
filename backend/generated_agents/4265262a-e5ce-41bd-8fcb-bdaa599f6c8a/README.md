# Loan Underwriting Risk Assessment Pipeline

## Prerequisites

- Python 3.8+
- pip

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

Execute the following command to run the pipeline:

```bash
python main.py
```

## Expected Input

The input should be a JSON object with the following structure:

```json
{
  "bank_statements": {
    "transactions": [
      {
        "date": "2023-01-01",
        "description": "Deposit",
        "amount": 1000
      },
      {
        "date": "2023-01-02",
        "description": "Withdrawal",
        "amount": -200
      }
    ],
    "balance": 800,
    "month": "January 2023"
  },
  "credit_report": {
    "accounts": [
      {
        "account_name": "Visa",
        "balance": 500,
        "payment_history": "On-time"
      },
      {
        "account_name": "MasterCard",
        "balance": 300,
        "payment_history": "Late"
      }
    ],
    "credit_score": 720
  },
  "loan_amount": 250000,
  "property_value": 312500,
  "applicant_name": "John Doe"
}
```

## Expected Output

The output will be a JSON object containing the risk assessment report, the path to the generated PDF report, and the delivery status:

```json
{
  "risk_assessment_report": { ... },
  "report_pdf_path": "/path/to/report.pdf",
  "delivery_status": { "email_sent": true, "stored_in_db": true }
}
```
