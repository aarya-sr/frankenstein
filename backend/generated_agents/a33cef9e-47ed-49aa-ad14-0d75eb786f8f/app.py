#!/usr/bin/env python3
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

st.set_page_config(page_title="Loan Underwriting Risk Assessment", layout="wide")
st.title("Loan Underwriting Risk Assessment")
st.caption(
    "Automated loan underwriting pipeline: extract financial data from documents, "
    "calculate risk ratios, evaluate against underwriting rules, generate a comprehensive "
    "risk assessment report, and store results securely."
)

with st.form("input_form"):
    st.subheader("Pipeline Inputs")
    bank_statements = st.text_area(
        "Bank Statements (file path)",
        value="bank_statement.pdf",
        height=68,
        help="Path to the bank statement PDF file"
    )
    credit_reports = st.text_area(
        "Credit Reports (file path)",
        value="credit_report.pdf",
        height=68,
        help="Path to the credit report PDF file"
    )
    structured_financial_data = st.text_area(
        "Structured Financial Data (file path)",
        value="financial_data.csv",
        height=68,
        help="Path to the structured financial CSV file"
    )
    submitted = st.form_submit_button("Run Pipeline")

if submitted:
    inputs = {
        "bank_statements": bank_statements.strip(),
        "credit_reports": credit_reports.strip(),
        "structured_financial_data": structured_financial_data.strip()
    }
    with st.spinner("Running loan underwriting risk assessment pipeline..."):
        try:
            crew = create_crew()
            result = crew.kickoff(inputs=inputs)
            raw_result = str(result.raw if hasattr(result, "raw") else result)
            st.subheader("Results")
            st.json(json.loads(json.dumps({"result": raw_result})))
            st.subheader("Full Output")
            st.text_area("Raw Output", value=raw_result, height=400)
        except Exception as e:
            st.error(f"Pipeline execution failed: {str(e)}")
            st.exception(e)
