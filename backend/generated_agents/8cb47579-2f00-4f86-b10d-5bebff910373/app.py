import json, os, streamlit as st
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
st.caption("A pipeline to assess loan underwriting risk based on financial documents.")

# Build input form from pipeline_input_schema fields
with st.form("input_form"):
    inputs = {}
    # One text_area per pipeline_input_schema field
    inputs["bank_statements"] = st.text_area("bank_statements", height=100)
    inputs["credit_reports"] = st.text_area("credit_reports", height=100)
    submitted = st.form_submit_button("Run Pipeline")

if submitted:
    with st.spinner("Running agent pipeline..."):
        crew = create_crew()
        result = crew.kickoff(inputs=inputs)
    st.subheader("Results")
    st.json(json.loads(json.dumps({"result": str(result.raw if hasattr(result, "raw") else result)})))
