from crewai import Task
from agents import (
    data_extraction_agent,
    risk_calculation_agent,
    underwriting_rules_agent,
    report_generation_agent,
    storage_agent
)

data_extraction_task = Task(
    description=(
        "Extract all financial data from the provided documents. "
        "Parse the bank statement PDF at '{bank_statements}' using the PDF Parser Bank Statement tool, "
        "parse the credit report PDF at '{credit_reports}' using the PDF Parser Credit Report tool, "
        "and parse the structured financial CSV at '{structured_financial_data}' using the CSV Parser Financial tool. "
        "Combine all extracted data into a unified JSON structure under the key 'extracted_financial_data'. "
        "List any extraction errors or missing data under 'extraction_errors'. "
        "The extracted_financial_data should include: account balances, transaction histories (as a list of transactions with 'amount' and 'category' keys), "
        "income figures, debt payments, credit scores, credit utilization, outstanding debts, loan_amount, property_value, and CSV financial records."
    ),
    expected_output=(
        "A JSON object with keys 'extracted_financial_data' (object containing account balances, transaction histories, "
        "income figures, debt payments, credit scores, credit utilization, outstanding debts, loan_amount, property_value, "
        "and CSV financial records) and 'extraction_errors' (array of any issues encountered during extraction)."
    ),
    agent=data_extraction_agent
)

risk_calculation_task = Task(
    description=(
        "Using the extracted_financial_data from the data extraction step, calculate all financial risk ratios. "
        "Use the Financial Calculator tool to compute DTI (total monthly debt payments / gross monthly income), "
        "LTV (loan amount / appraised property value), income stability, and overdraft frequency. "
        "Use the Statistical Analyzer tool to compute statistical metrics (mean, median, std_dev, outlier detection, trends) "
        "on income and transaction patterns. "
        "Return the results as 'risk_ratios' and 'statistical_analysis', and forward the original 'extracted_financial_data' unchanged."
    ),
    expected_output=(
        "A JSON object with keys 'extracted_financial_data' (forwarded unchanged), "
        "'risk_ratios' (object with dti, ltv, income_stability, overdraft_frequency), "
        "and 'statistical_analysis' (object with mean, median, std_dev, outliers, trends)."
    ),
    agent=risk_calculation_agent,
    context=[data_extraction_task]
)

underwriting_rules_task = Task(
    description=(
        "Using the extracted_financial_data, risk_ratios, and statistical_analysis from upstream, "
        "evaluate the loan application against underwriting rules. "
        "Use the Rule Engine tool to check DTI<=0.43, LTV<=0.80, credit_score>=620, and income_stability>=0.7, "
        "producing pass/fail results with reasoning. "
        "Use the Scoring Engine tool to compute a weighted composite risk score (DTI 30%, LTV 25%, credit score 25%, income stability 20%). "
        "Return 'underwriting_evaluation', 'composite_risk_score', and 'rule_violations', and forward all upstream data."
    ),
    expected_output=(
        "A JSON object with keys 'extracted_financial_data', 'risk_ratios', 'statistical_analysis' (all forwarded), "
        "'underwriting_evaluation' (object with per-rule pass/fail and reasoning), "
        "'composite_risk_score' (object with composite score and breakdown), "
        "and 'rule_violations' (array of any failed rules)."
    ),
    agent=underwriting_rules_agent,
    context=[risk_calculation_task]
)

report_generation_task = Task(
    description=(
        "Using all upstream data\u2014extracted_financial_data, risk_ratios, statistical_analysis, "
        "underwriting_evaluation, composite_risk_score, extraction_errors, and rule_violations\u2014"
        "generate a comprehensive risk assessment report. "
        "Use the Report Generator tool to produce a report with sections: executive summary, financial data breakdown, "
        "risk ratio analysis, compliance results, composite risk score, and final recommendation. "
        "Return 'report_content' (structured JSON of the report) and 'risk_assessment_report' (file path to the generated report)."
    ),
    expected_output=(
        "A JSON object with keys 'report_content' (object containing structured report data for all sections) "
        "and 'risk_assessment_report' (string file path to the generated report)."
    ),
    agent=report_generation_agent,
    context=[underwriting_rules_task]
)

storage_task = Task(
    description=(
        "Store the generated risk assessment report securely. "
        "Use the Database Writer tool to insert the report_content and report file path into the risk_assessment_reports "
        "database table with full audit metadata (timestamp, version hash, access control tags). "
        "Validate write integrity and return 'storage_confirmation' (confirmation message with record ID) "
        "and forward 'risk_assessment_report' (the report file path)."
    ),
    expected_output=(
        "A JSON object with keys 'risk_assessment_report' (string file path to the report, forwarded) "
        "and 'storage_confirmation' (string confirming successful storage with record ID and timestamp)."
    ),
    agent=storage_agent,
    context=[report_generation_task]
)
