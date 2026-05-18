from crewai import Task
from agents import (
    data_extraction_agent,
    financial_calculation_agent,
    underwriting_rules_agent,
    report_generation_agent,
    report_delivery_agent
)
from tools import (
    pdf_parser,
    csv_parser,
    xml_parser,
    data_transformer,
    financial_calculator,
    rule_engine,
    scoring_engine,
    report_generator,
    email_sender,
    database_writer
)

data_extraction_task = Task(
    description=(
        "Extract and structure all relevant financial data from the provided bank statements "
        "({bank_statements}) and credit reports ({credit_reports}). "
        "The data is provided as JSON arrays, not as file paths. Since the data is already structured JSON, "
        "you should use the Data Transformer tool to merge and normalize all the data into a single canonical "
        "JSON structure. Pass the bank_statements and credit_reports as the 'parsed_documents' list to the "
        "Data Transformer tool. Extract the applicant name, monthly income, total outstanding debt, credit score, "
        "and payment history. Also pass through the pipeline-level loan_amount ({loan_amount}) and "
        "property_value ({property_value}) unchanged. Flag any missing or incomplete data fields in data_quality_flags."
    ),
    expected_output=(
        "A JSON object containing: extracted_financial_data (unified object with all parsed financial data), "
        "applicant_name, monthly_income, total_outstanding_debt, credit_score, payment_history, "
        "loan_amount, property_value, and data_quality_flags."
    ),
    agent=data_extraction_agent,
    tools=[pdf_parser, csv_parser, xml_parser, data_transformer]
)

financial_calculation_task = Task(
    description=(
        "Using the extracted financial data from the previous step, calculate key financial ratios. "
        "Use the Financial Calculator tool with a JSON input containing: monthly_income, total_outstanding_debt, "
        "loan_amount ({loan_amount}), property_value ({property_value}), and transactions (if available). "
        "The tool will compute Debt-to-Income (DTI) as a percentage and Loan-to-Value (LTV) as a percentage, "
        "and assess income stability. Pass through credit_score, payment_history, and applicant_name unchanged "
        "for downstream agents."
    ),
    expected_output=(
        "A JSON object containing: financial_ratios (object with all computed ratios), DTI (percentage), "
        "LTV (percentage), income_stability (stable/unstable/insufficient_data), plus pass-through fields: "
        "credit_score, payment_history, applicant_name, monthly_income."
    ),
    agent=financial_calculation_agent,
    tools=[financial_calculator],
    context=[data_extraction_task]
)

underwriting_rules_task = Task(
    description=(
        "Apply underwriting rules and thresholds to the calculated financial ratios and credit data. "
        "Use the Rule Engine tool with a JSON input containing: DTI, LTV, credit_score, monthly_income. "
        "The default rules check: DTI < 36%, LTV < 80%, credit_score >= 620, and monthly_income > 0. "
        "Then use the Scoring Engine tool with a JSON input containing: DTI, LTV, credit_score, payment_history. "
        "The default weights are: DTI=0.3, LTV=0.25, credit_score=0.3, payment_history=0.15. "
        "Based on the rule results and risk score, determine a recommendation of 'approve' (all rules pass and "
        "risk_score < 0.4), 'deny' (critical rules fail or risk_score > 0.7), or 'refer' (otherwise). "
        "Pass through applicant_name, monthly_income, DTI, LTV, credit_score, and income_stability for the "
        "report generator."
    ),
    expected_output=(
        "A JSON object containing: rule_evaluation_results (array of per-rule pass/fail with reasoning), "
        "risk_score (composite number), risk_factors (array of identified risk factors), "
        "recommendation ('approve', 'deny', or 'refer'), plus pass-through fields: applicant_name, "
        "monthly_income, DTI, LTV, credit_score, income_stability."
    ),
    agent=underwriting_rules_agent,
    tools=[rule_engine, scoring_engine],
    context=[financial_calculation_task]
)

report_generation_task = Task(
    description=(
        "Compile all analysis results into a comprehensive risk assessment report. "
        "Use the Report Generator tool with a JSON input containing: applicant_name, monthly_income, DTI, LTV, "
        "credit_score, income_stability, risk_score, risk_factors, rule_evaluation_results, and recommendation. "
        "The output must be a well-structured JSON report with sections: applicant_information (object), "
        "financial_data_summary (object with DTI, LTV, monthly_income, income_stability), "
        "credit_score_analysis (object with credit_score, risk_factors, risk_score), "
        "underwriting_rules_applied (array), recommendation (string), and notes (string with explanatory commentary)."
    ),
    expected_output=(
        "A JSON object matching the pipeline output schema with fields: applicant_information, "
        "financial_data_summary, credit_score_analysis, underwriting_rules_applied, recommendation, and notes."
    ),
    agent=report_generation_agent,
    tools=[report_generator],
    context=[underwriting_rules_task]
)

report_delivery_task = Task(
    description=(
        "Deliver the completed risk assessment report. Use the Email Sender tool to send the report "
        "to the designated underwriter (use recipient 'underwriter@example.com'). Pass the full report "
        "from the previous step as the 'report' key and the recipient email as the 'recipient' key. "
        "Then use the Database Writer tool to persist the report in the secure database for audit and "
        "compliance purposes. Pass the report as 'report' and the applicant_name as 'applicant_name'. "
        "Confirm successful delivery and storage, and flag any failures."
    ),
    expected_output=(
        "A JSON object containing: delivery_status with email_sent (boolean), database_stored (boolean), "
        "and any error messages if delivery failed."
    ),
    agent=report_delivery_agent,
    tools=[email_sender, database_writer],
    context=[report_generation_task]
)
