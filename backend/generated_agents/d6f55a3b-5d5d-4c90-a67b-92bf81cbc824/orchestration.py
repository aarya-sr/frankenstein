from crewai import Crew
from agents import agents


def create_crew() -> Crew:
    return Crew(
        agents=agents,
        memory_strategy="shared",
        shared_memory_keys=[
            "bank_statements_path",
            "credit_reports_path",
            "extracted_bank_data",
            "extracted_credit_data",
            "structured_financial_data",
            "monthly_income",
            "monthly_debt",
            "loan_amount",
            "property_value",
            "dti_ratio",
            "ltv_ratio",
            "risk_metrics",
            "underwriting_decision",
            "decision_rationale",
            "risk_assessment_report"
        ],
        persistence="session"
    )
