from tools import parse_pdf_statements, parse_csv_statements, calculate_financial_metrics, evaluate_underwriting_rules, generate_risk_report, send_report

agents = [
    {
        "id": "data_extraction_agent",
        "role": "Financial Document Parser",
        "goal": "Extract structured financial data from bank statements and credit reports with 100% accuracy",
        "tools": [parse_pdf_statements, parse_csv_statements],
        "task_description_template": "Use {bank_statements} and {credit_report} to extract structured financial data.",
        "expected_output": {
            "fields": [
                {"name": "extracted_data", "type": "object", "required": true},
                {"name": "applicant_name", "type": "string", "required": true},
                {"name": "loan_amount", "type": "number", "required": true},
                {"name": "property_value", "type": "number", "required": true}
            ]
        }
    },
    {
        "id": "financial_calculation_agent",
        "role": "Financial Metrics Calculator",
        "goal": "Calculate DTI, LTV, and other financial ratios from extracted data with precision",
        "tools": [calculate_financial_metrics],
        "task_description_template": "Calculate financial ratios using {extracted_data}, {loan_amount}, and {property_value}.",
        "expected_output": {
            "fields": [
                {"name": "calculated_ratios", "type": "object", "required": true},
                {"name": "extracted_data", "type": "object", "required": true},
                {"name": "applicant_name", "type": "string", "required": true}
            ]
        }
    },
    {
        "id": "underwriting_decision_agent",
        "role": "Underwriting Rules Evaluator",
        "goal": "Apply underwriting rules to calculated ratios and produce approve/deny/conditional decisions",
        "tools": [evaluate_underwriting_rules],
        "task_description_template": "Apply underwriting rules to {calculated_ratios}.",
        "expected_output": {
            "fields": [
                {"name": "underwriting_decision", "type": "string", "required": true},
                {"name": "decision_reasoning", "type": "string", "required": true},
                {"name": "recommendations", "type": "string", "required": true},
                {"name": "calculated_ratios", "type": "object", "required": true},
                {"name": "extracted_data", "type": "object", "required": true},
                {"name": "applicant_name", "type": "string", "required": true}
            ]
        }
    },
    {
        "id": "report_generation_agent",
        "role": "Risk Assessment Report Generator",
        "goal": "Generate comprehensive PDF risk assessment reports with all applicant data, ratios, and recommendations",
        "tools": [generate_risk_report],
        "task_description_template": "Generate a risk assessment report using {underwriting_decision}, {calculated_ratios}, {extracted_data}, {decision_reasoning}, and {recommendations}.",
        "expected_output": {
            "fields": [
                {"name": "risk_assessment_report", "type": "object", "required": true},
                {"name": "report_pdf_path", "type": "string", "required": true},
                {"name": "applicant_name", "type": "string", "required": true}
            ]
        }
    },
    {
        "id": "distribution_agent",
        "role": "Report Distribution Coordinator",
        "goal": "Deliver reports via email and store them securely in the database",
        "tools": [send_report],
        "task_description_template": "Deliver the report using {report_pdf_path} and {risk_assessment_report}.",
        "expected_output": {
            "fields": [
                {"name": "delivery_status", "type": "object", "required": true},
                {"name": "risk_assessment_report", "type": "object", "required": true},
                {"name": "report_pdf_path", "type": "string", "required": true}
            ]
        }
    }
]
