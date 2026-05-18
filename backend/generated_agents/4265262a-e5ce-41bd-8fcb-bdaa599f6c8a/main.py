import json, os
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

SPEC_SAMPLE_INPUT = {
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
