from tools import parse_pdf, parse_csv, calculate_financial_metrics, apply_underwriting_rules, generate_report, send_report

agents = [
    {
        "id": "document_extraction_agent",
        "role": "Financial Document Processor",
        "goal": "Extract and parse all relevant financial data from bank statements and credit reports into structured JSON format",
        "tools": [parse_pdf, parse_csv],
        "receives_from": [],
        "sends_to": ["financial_calculation_agent"]
    },
    {
        "id": "financial_calculation_agent",
        "role": "Financial Metrics Calculator",
        "goal": "Calculate critical underwriting metrics including DTI (debt-to-income ratio) and LTV (loan-to-value ratio) from extracted financial data",
        "tools": [calculate_financial_metrics],
        "receives_from": ["document_extraction_agent"],
        "sends_to": ["risk_assessment_agent"]
    },
    {
        "id": "risk_assessment_agent",
        "role": "Underwriting Risk Analyst",
        "goal": "Apply underwriting rules to assess debt levels, verify income, evaluate credit history, and determine loan approval decision based on risk thresholds",
        "tools": [apply_underwriting_rules],
        "receives_from": ["financial_calculation_agent"],
        "sends_to": ["report_generation_agent"]
    },
    {
        "id": "report_generation_agent",
        "role": "Risk Assessment Report Compiler",
        "goal": "Generate a comprehensive, professionally formatted PDF risk assessment report containing applicant information, financial analysis, underwriting decision, and recommendations",
        "tools": [generate_report],
        "receives_from": ["risk_assessment_agent"],
        "sends_to": ["delivery_agent"]
    },
    {
        "id": "delivery_agent",
        "role": "Secure Report Delivery Coordinator",
        "goal": "Securely transmit the risk assessment report to the user via email and make it available for download, ensuring compliance with data security requirements",
        "tools": [send_report],
        "receives_from": ["report_generation_agent"],
        "sends_to": []
    }
]
