from tools import parse_bank_statements, parse_credit_reports, calculate_financial_metrics, evaluate_underwriting_rules, generate_risk_assessment_report

agents = [
    {
        "id": "document_extraction_agent",
        "role": "Financial Document Processor",
        "goal": "Extract all financial data from bank statements and credit reports with high accuracy, flagging any unreadable or missing data fields",
        "tools": [parse_bank_statements, parse_credit_reports],
        "receives_from": [],
        "sends_to": ["financial_calculation_agent"]
    },
    {
        "id": "financial_calculation_agent",
        "role": "Financial Metrics Calculator",
        "goal": "Calculate accurate DTI and LTV ratios from extracted financial data, normalizing income and expense data according to underwriting standards",
        "tools": [calculate_financial_metrics],
        "receives_from": ["document_extraction_agent"],
        "sends_to": ["underwriting_decision_agent"]
    },
    {
        "id": "underwriting_decision_agent",
        "role": "Underwriting Rules Evaluator",
        "goal": "Apply underwriting rules to financial ratios and credit score, producing a clear approve/deny/manual_review recommendation with detailed reasoning based on threshold evaluation",
        "tools": [evaluate_underwriting_rules],
        "receives_from": ["financial_calculation_agent"],
        "sends_to": ["report_generation_agent"]
    },
    {
        "id": "report_generation_agent",
        "role": "Risk Assessment Report Generator",
        "goal": "Generate a structured JSON risk assessment report containing all required fields and store it securely, notifying the loan officer upon completion",
        "tools": [generate_risk_assessment_report],
        "receives_from": ["underwriting_decision_agent"],
        "sends_to": []
    }
]
