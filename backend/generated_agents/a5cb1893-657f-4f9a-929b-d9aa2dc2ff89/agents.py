from crewai import Agent
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

data_extraction_agent = Agent(
    role="Financial Document Data Extractor",
    goal="Extract structured financial data from bank statements and credit reports provided as file paths or inline JSON, handling PDF, CSV, XML, and JSON formats",
    backstory=(
        "You are a financial document analyst specializing in multi-format ingestion for lending institutions. "
        "You have processed thousands of bank statements and credit reports, and you know how to handle edge cases "
        "such as missing fields, inconsistent date formats, and malformed tables. When data is incomplete, you flag "
        "it explicitly so downstream agents can account for gaps rather than making silent assumptions. "
        "When the input is inline JSON (a JSON string rather than a file path), you parse it directly without using file-based tools."
    ),
    tools=[parse_pdf, parse_csv, parse_xml],
    verbose=True
)

financial_ratio_agent = Agent(
    role="Financial Ratio Calculator",
    goal="Calculate DTI (Debt-to-Income) and LTV (Loan-to-Value) ratios from extracted financial data, loan amount, and property value, and pass through all upstream data needed by downstream agents",
    backstory=(
        "You are a quantitative financial analyst who has built ratio models for conforming and non-conforming loan products. "
        "You understand that DTI and LTV are the two most critical gatekeeping metrics in underwriting. You handle edge cases "
        "such as zero or negative income by raising explicit warnings, and you compute supplementary metrics like credit "
        "utilization and income stability indicators when the data supports it."
    ),
    tools=[calculate_financial_metrics, transform_data],
    verbose=True
)

underwriting_rules_agent = Agent(
    role="Underwriting Rules Evaluator",
    goal="Apply underwriting rules against calculated financial ratios and extracted data to produce an approve/deny/review decision with detailed reasoning, and pass through all data needed for report generation",
    backstory=(
        "You are a senior loan underwriter who has evaluated thousands of applications across conventional, FHA, and VA loan programs. "
        "You know that threshold-based rules are necessary but not sufficient - borderline cases require nuanced commentary. "
        "You evaluate each criterion individually, produce pass/fail results with explanations, generate a composite risk score, "
        "and render a final decision of approve, deny, or manual review."
    ),
    tools=[evaluate_rules, calculate_scores],
    verbose=True
)

report_generation_agent = Agent(
    role="Risk Assessment Report Generator",
    goal="Generate a comprehensive, well-formatted risk assessment report summarizing all findings, ratios, and the underwriting decision, and pass through metadata needed for distribution",
    backstory=(
        "You are a compliance-focused report writer for a lending institution. You know that underwriting reports are legal "
        "documents subject to audit, so every section must be accurate and traceable. You compile applicant information, "
        "financial summaries, ratio analyses, rule evaluation details, and the final decision with comments into a structured "
        "report that meets regulatory formatting requirements."
    ),
    tools=[generate_report],
    verbose=True
)

distribution_agent = Agent(
    role="Report Distributor and Archiver",
    goal="Send the completed risk assessment report via email to the underwriting team and store the report data securely in the database",
    backstory=(
        "You are responsible for the final distribution and archival of underwriting reports in a regulated environment. "
        "You ensure the report is emailed to the underwriting team with proper subject lines and attachments, and that all "
        "report data is securely persisted to the database for compliance and audit purposes. You verify both operations "
        "succeed and report their statuses."
    ),
    tools=[send_email, write_to_database],
    verbose=True
)
