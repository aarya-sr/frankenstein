from tools import parse_pdf, parse_csv, merge_and_structure_data, normalize_financial_data, evaluate_risk, generate_report

agents = [
    {
        "id": "document_extraction_agent",
        "role": "Financial Document Parser",
        "goal": "Extract structured financial data from bank statements (PDF) and credit reports (CSV) with 100% field accuracy",
        "tools": [parse_pdf, parse_csv, merge_and_structure_data],
        "receives_from": [],
        "sends_to": ["data_transformation_agent"]
    },
    {
        "id": "data_transformation_agent",
        "role": "Financial Data Normalizer",
        "goal": "Transform extracted financial data into standardized format and calculate DTI and LTV ratios with precision",
        "tools": [normalize_financial_data],
        "receives_from": ["document_extraction_agent"],
        "sends_to": ["risk_assessment_agent"]
    },
    {
        "id": "risk_assessment_agent",
        "role": "Loan Risk Analyst",
        "goal": "Evaluate applicant creditworthiness against underwriting guidelines and produce a risk score with recommendation",
        "tools": [evaluate_risk],
        "receives_from": ["data_transformation_agent"],
        "sends_to": ["report_generation_agent"]
    },
    {
        "id": "report_generation_agent",
        "role": "Underwriting Report Specialist",
        "goal": "Generate comprehensive PDF risk assessment reports that summarize all findings and recommendations",
        "tools": [generate_report],
        "receives_from": ["risk_assessment_agent"],
        "sends_to": []
    }
]
