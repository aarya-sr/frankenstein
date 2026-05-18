import json
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

load_dotenv()
if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
    os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    os.environ.setdefault("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")

st.set_page_config(page_title="Loan Underwriting Risk Assessment Pipeline", layout="wide")
st.title("Loan Underwriting Risk Assessment Pipeline")
st.caption("A sequential agent pipeline that extracts financial data, calculates ratios, evaluates underwriting rules, generates a risk assessment report, and distributes it via email and database archival.")

# Load sample data for defaults
sample_path = Path(__file__).parent / "sample_data.json"
defaults = {}
if sample_path.exists():
    defaults = json.loads(sample_path.read_text())

with st.form("input_form"):
    st.subheader("Pipeline Inputs")

    bank_statements = st.text_area(
        "Bank Statements (JSON string or file path)",
        value=defaults.get("bank_statements", ""),
        height=150
    )
    credit_reports = st.text_area(
        "Credit Reports (JSON string or file path)",
        value=defaults.get("credit_reports", ""),
        height=150
    )
    loan_amount = st.number_input(
        "Loan Amount ($)",
        value=float(defaults.get("loan_amount", 250000.0)),
        min_value=0.0,
        step=1000.0
    )
    property_value = st.number_input(
        "Property Value ($)",
        value=float(defaults.get("property_value", 312500.0)),
        min_value=0.0,
        step=1000.0
    )

    submitted = st.form_submit_button("Run Pipeline")

if submitted:
    inputs = {
        "bank_statements": bank_statements,
        "credit_reports": credit_reports,
        "loan_amount": loan_amount,
        "property_value": property_value
    }

    with st.spinner("Running loan underwriting risk assessment pipeline..."):
        try:
            crew = create_crew()
            result = crew.kickoff(inputs=inputs)
            raw_result = str(result.raw if hasattr(result, "raw") else result)

            st.subheader("Results")
            st.json(json.loads(json.dumps({"result": raw_result})))

            st.subheader("Full Report")
            st.markdown(raw_result)
        except Exception as e:
            st.error(f"Pipeline execution failed: {str(e)}")
            st.exception(e)
