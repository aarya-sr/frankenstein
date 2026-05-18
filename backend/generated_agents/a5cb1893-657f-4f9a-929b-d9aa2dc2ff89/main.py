import json
import os
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

SPEC_SAMPLE_INPUT = {
    "bank_statements": "{\"account_holder_name\": \"John Doe\", \"account_number\": \"123456789\", \"transaction_date\": \"2023-01-01\", \"transaction_description\": \"Deposit\", \"transaction_amount\": 1000.0, \"balance\": 5000.0, \"monthly_income\": 3000.0}",
    "credit_reports": "{\"applicant_name\": \"John Doe\", \"credit_accounts\": [{\"account_type\": \"Credit Card\", \"balance\": 2000.0, \"credit_limit\": 5000.0, \"payment_status\": \"On Time\"}], \"inquiries\": [{\"date\": \"2023-01-01\", \"type\": \"Hard Inquiry\"}], \"credit_score\": 720}",
    "loan_amount": 250000.0,
    "property_value": 312500.0
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
