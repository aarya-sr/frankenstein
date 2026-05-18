import json, os
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

SPEC_SAMPLE_INPUT = {
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

def load_inputs():
    p = Path(__file__).parent / "sample_data.json"
    if p.exists():
        return json.loads(p.read_text())
    return SPEC_SAMPLE_INPUT

def main():
    load_dotenv()
    if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")

    inputs = load_inputs()
    crew = create_crew()
    result = crew.kickoff(inputs=inputs)
    print(json.dumps({"result": str(result.raw if hasattr(result, "raw") else result)}, indent=2))

if __name__ == "__main__":
    main()
