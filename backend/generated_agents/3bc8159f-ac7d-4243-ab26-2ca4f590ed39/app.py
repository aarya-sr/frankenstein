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
st.caption("AI-powered loan underwriting pipeline that extracts financial data, calculates ratios, evaluates rules, scores risk, and generates comprehensive assessment reports.")

# Load default sample data
default_sample = {
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

with st.form("input_form"):
    st.subheader("Pipeline Inputs")

    col1, col2 = st.columns(2)
    with col1:
        loan_amount = st.number_input("Loan Amount ($)", min_value=0.0, value=200000.0, step=1000.0)
        property_value = st.number_input("Property Value ($)", min_value=0.0, value=250000.0, step=1000.0)

    bank_statements_str = st.text_area(
        "Bank Statements (JSON array)",
        value=json.dumps(default_sample["bank_statements"], indent=2),
        height=200
    )

    credit_reports_str = st.text_area(
        "Credit Reports (JSON array)",
        value=json.dumps(default_sample["credit_reports"], indent=2),
        height=200
    )

    submitted = st.form_submit_button("Run Underwriting Pipeline")

if submitted:
    try:
        bank_statements = json.loads(bank_statements_str)
        credit_reports = json.loads(credit_reports_str)
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON input: {e}")
        st.stop()

    inputs = {
        "bank_statements": bank_statements,
        "credit_reports": credit_reports,
        "loan_amount": loan_amount,
        "property_value": property_value
    }

    with st.spinner("Running loan underwriting pipeline... This may take a few minutes."):
        try:
            crew = create_crew()
            result = crew.kickoff(inputs=inputs)
            raw_result = str(result.raw if hasattr(result, "raw") else result)
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    st.subheader("Results")

    try:
        parsed = json.loads(raw_result)
        st.json(parsed)
    except (json.JSONDecodeError, TypeError):
        st.json({"result": raw_result})

    st.subheader("Raw Output")
    st.text_area("Raw Result", value=raw_result, height=400)
