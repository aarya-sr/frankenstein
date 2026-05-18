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
  "bank_statements": "/path/to/bank_statement.pdf",
  "credit_reports": "/path/to/credit_report.csv"
}
```

## Expected Output
The output will be a JSON object containing:

- `risk_assessment_report`: A string representing the PDF content of the risk assessment report.
- `recommendation`: A string with the loan recommendation.
- `risk_score`: A numerical risk score.
