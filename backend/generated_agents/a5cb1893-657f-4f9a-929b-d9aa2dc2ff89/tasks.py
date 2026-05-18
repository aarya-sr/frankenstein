from crewai import Task
from agents import (
    data_extraction_agent,
    financial_ratio_agent,
    underwriting_rules_agent,
    report_generation_agent,
    distribution_agent
)
from tools import (
    parse_pdf,
    parse_csv,
    parse_xml,
    calculate_financial_metrics,
    transform_data,
    evaluate_rules,
    calculate_scores,
    generate_report,
    send_email,
    write_to_database
)

data_extraction_task = Task(
    description=(
        "Extract structured financial data from the provided bank statements at '{bank_statements}' "
        "and credit reports at '{credit_reports}'. Detect the file format (PDF, CSV, XML, or inline JSON) "
        "and use the appropriate parser tool. If the input looks like a JSON string (starts with '{{'), parse it "
        "directly as JSON without using file-based tools. Extract the applicant name, monthly income, monthly "
        "debt payments, and credit score. Also note the loan amount {loan_amount} and property value {property_value} "
        "for downstream use. Flag any missing or inconsistent data explicitly. Return a JSON object with keys: "
        "extracted_bank_data, extracted_credit_data, applicant_name, monthly_income, monthly_debt_payments, "
        "credit_score, loan_amount, property_value, and optionally data_quality_flags."
    ),
    expected_output=(
        "A JSON object containing extracted_bank_data (object), extracted_credit_data (object), "
        "applicant_name (string), monthly_income (number), monthly_debt_payments (number), "
        "credit_score (number), loan_amount (number), property_value (number), "
        "and optionally data_quality_flags (array)."
    ),
    agent=data_extraction_agent,
    tools=[parse_pdf, parse_csv, parse_xml]
)

financial_ratio_task = Task(
    description=(
        "Using the extracted financial data from the previous agent - including monthly_income, monthly_debt_payments, "
        "credit_score, extracted_bank_data, and extracted_credit_data - along with loan_amount {loan_amount} and "
        "property_value {property_value}, calculate the Debt-to-Income (DTI) ratio and Loan-to-Value (LTV) ratio. "
        "Compute any supplementary financial metrics such as credit utilization and income stability indicators. "
        "If monthly_income is zero or negative, raise an explicit warning. Return a JSON object with keys: "
        "dti_ratio, ltv_ratio, financial_ratios (containing all computed metrics), and pass through all upstream "
        "fields: extracted_bank_data, extracted_credit_data, monthly_income, monthly_debt_payments, credit_score, "
        "applicant_name, loan_amount, property_value."
    ),
    expected_output=(
        "A JSON object containing dti_ratio (number), ltv_ratio (number), financial_ratios (object with all "
        "computed metrics), extracted_bank_data (object), extracted_credit_data (object), monthly_income (number), "
        "monthly_debt_payments (number), credit_score (number), applicant_name (string), loan_amount (number), "
        "property_value (number)."
    ),
    agent=financial_ratio_agent,
    tools=[calculate_financial_metrics, transform_data],
    context=[data_extraction_task]
)

underwriting_rules_task = Task(
    description=(
        "Apply underwriting rules against the calculated financial ratios and extracted data. Evaluate: "
        "DTI ratio (threshold <= 43%), LTV ratio (threshold <= 80%), credit score (minimum 620), and income "
        "verification (monthly_income > 0). For each rule, produce a pass/fail result with explanation. Then "
        "compute a composite risk score using weighted scoring (DTI: 0.3, LTV: 0.25, credit score: 0.3, "
        "payment history: 0.15). Render a final decision of 'approve', 'deny', or 'manual_review' with detailed "
        "comments. Return a JSON object with keys: rule_evaluation_results, composite_risk_score, "
        "underwriting_decision, comments, and pass through: applicant_name, loan_amount, monthly_income, "
        "monthly_debt_payments, dti_ratio, ltv_ratio, credit_score."
    ),
    expected_output=(
        "A JSON object containing rule_evaluation_results (object with per-rule pass/fail and reasoning), "
        "composite_risk_score (number), underwriting_decision (string: approve/deny/manual_review), "
        "comments (string), applicant_name (string), loan_amount (number), monthly_income (number), "
        "monthly_debt_payments (number), dti_ratio (number), ltv_ratio (number), credit_score (number)."
    ),
    agent=underwriting_rules_agent,
    tools=[evaluate_rules, calculate_scores],
    context=[financial_ratio_task]
)

report_generation_task = Task(
    description=(
        "Generate a comprehensive, well-formatted risk assessment report. The report must include sections for: "
        "applicant information (applicant_name, loan_amount), financial summary (monthly_income, monthly_debt_payments), "
        "ratio analysis (dti_ratio, ltv_ratio, credit_score), rule evaluation details (rule_evaluation_results), "
        "and decision summary (underwriting_decision, composite_risk_score, comments). Ensure the report is accurate, "
        "traceable, and meets regulatory formatting requirements. Return a JSON object with keys: "
        "risk_assessment_report (the generated report content), applicant_name, underwriting_decision."
    ),
    expected_output=(
        "A JSON object containing risk_assessment_report (string - the full report content), "
        "applicant_name (string), underwriting_decision (string)."
    ),
    agent=report_generation_agent,
    tools=[generate_report],
    context=[underwriting_rules_task]
)

distribution_task = Task(
    description=(
        "Distribute the completed risk assessment report. First, send the report via email to the underwriting "
        "team at underwriting-team@company.com with subject 'Risk Assessment Report - [applicant_name]' and "
        "include the risk_assessment_report content in the body. Second, store the report data securely in the "
        "'risk_assessment_reports' database table using an upsert operation. Verify both operations succeed and "
        "report their statuses. Return a JSON object with keys: risk_assessment_report (the report content), "
        "email_status (string indicating success/failure), database_status (string indicating success/failure)."
    ),
    expected_output=(
        "A JSON object containing risk_assessment_report (string), email_status (string) and "
        "database_status (string) indicating the success or failure of each distribution operation."
    ),
    agent=distribution_agent,
    tools=[send_email, write_to_database],
    context=[report_generation_task]
)
