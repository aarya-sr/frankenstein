#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


SPEC_SAMPLE_INPUT = {
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


def load_inputs():
    p = Path(__file__).parent / "sample_data.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            # Validate required fields
            required = ["bank_statements", "credit_reports", "loan_amount", "property_value"]
            if all(k in data for k in required):
                return data
        except (json.JSONDecodeError, Exception):
            pass
    return SPEC_SAMPLE_INPUT


def main():
    load_dotenv()
    if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")

    inputs = load_inputs()

    # Ensure all required pipeline input fields are present
    assert "bank_statements" in inputs, "Missing bank_statements in inputs"
    assert "credit_reports" in inputs, "Missing credit_reports in inputs"
    assert "loan_amount" in inputs, "Missing loan_amount in inputs"
    assert "property_value" in inputs, "Missing property_value in inputs"

    from orchestration import create_crew
    crew = create_crew()
    result = crew.kickoff(inputs=inputs)
    print(json.dumps({"result": str(result.raw if hasattr(result, "raw") else result)}, indent=2))


if __name__ == "__main__":
    main()
