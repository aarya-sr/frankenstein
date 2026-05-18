from tools import extract_text_from_documents, transform_extracted_data, calculate_risk_ratios, evaluate_underwriting_rules, generate_risk_assessment_report

agents = [
    {
        "id": "document_extraction_agent",
        "role": "Financial Document Processor",
        "goal": "Extract all text and structured data from bank statements and credit reports with maximum accuracy",
        "tools": [extract_text_from_documents],
        "task_description": "Use {bank_statements_path} and {credit_reports_path} to extract all text and structured data.",
        "receives_from": [],
        "sends_to": ["data_transformation_agent"]
    },
    {
        "id": "data_transformation_agent",
        "role": "Financial Data Structurer",
        "goal": "Transform raw extracted text into clean, structured financial data with monthly averages and standardized formats",
        "tools": [transform_extracted_data],
        "task_description": "Transform extracted data into structured financial data.",
        "receives_from": ["document_extraction_agent"],
        "sends_to": ["risk_calculation_agent"]
    },
    {
        "id": "risk_calculation_agent",
        "role": "Financial Risk Analyst",
        "goal": "Calculate precise DTI and LTV ratios from structured financial data according to underwriting standards",
        "tools": [calculate_risk_ratios],
        "task_description": "Calculate DTI and LTV ratios from structured financial data.",
        "receives_from": ["data_transformation_agent"],
        "sends_to": ["underwriting_decision_agent"]
    },
    {
        "id": "underwriting_decision_agent",
        "role": "Loan Underwriting Decision Maker",
        "goal": "Apply underwriting rules to risk ratios and determine loan approval or denial with clear reasoning",
        "tools": [evaluate_underwriting_rules],
        "task_description": "Apply underwriting rules to determine loan approval or denial.",
        "receives_from": ["risk_calculation_agent"],
        "sends_to": ["report_generation_agent"]
    },
    {
        "id": "report_generation_agent",
        "role": "Risk Assessment Report Writer",
        "goal": "Generate comprehensive, professional risk assessment reports in JSON or PDF format with all key metrics and recommendations",
        "tools": [generate_risk_assessment_report],
        "task_description": "Generate a comprehensive risk assessment report.",
        "receives_from": ["underwriting_decision_agent"],
        "sends_to": []
    }
]
