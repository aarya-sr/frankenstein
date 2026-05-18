import json, os
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

SPEC_SAMPLE_INPUT = {
    "bank_statements": "/data/uploads/bank_statement_2024.pdf",
    "credit_reports": "/data/uploads/credit_report_2024.csv"
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
