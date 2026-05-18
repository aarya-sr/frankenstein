from crewai.tools import tool
import fitz

def pdf_parser_pymupdf(file_path: str, extract_tables: bool = True) -> dict:
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        page_data = {"page": page.number + 1, "text": page.get_text()}
        if extract_tables:
            page_data["tables"] = page.find_tables()
        pages.append(page_data)
    doc.close()
    return {"pages": pages, "total_pages": len(pages)}

@tool("Parse Bank Statements")
def parse_bank_statements(data: dict) -> dict:
    bank_statements_path = data.get("bank_statements")
    extracted_data = pdf_parser_pymupdf(bank_statements_path)
    return {"extracted_bank_data": extracted_data}

@tool("Parse Credit Reports")
def parse_credit_reports(data: dict) -> dict:
    credit_reports_path = data.get("credit_reports")
    extracted_data = pdf_parser_pymupdf(credit_reports_path)
    return {"extracted_credit_data": extracted_data}

@tool("Calculate Financial Metrics")
def calculate_financial_metrics(data: dict) -> dict:
    extracted_bank_data = data.get("extracted_bank_data")
    extracted_credit_data = data.get("extracted_credit_data")
    # Placeholder for actual financial calculations
    dti = 0.35  # Example value
    ltv = 0.75  # Example value
    credit_score = 700  # Example value
    return {"DTI": dti, "LTV": ltv, "creditScore": credit_score}

@tool("Evaluate Underwriting Rules")
def evaluate_underwriting_rules(data: dict) -> dict:
    dti = data.get("DTI")
    ltv = data.get("LTV")
    credit_score = data.get("creditScore")
    # Placeholder for rule evaluation
    recommendation = "approve" if dti <= 0.43 and ltv <= 0.80 and credit_score >= 620 else "manual_review"
    rule_results = []  # Example empty list
    reasoning = "All metrics within acceptable thresholds."  # Example reasoning
    return {"recommendation": recommendation, "rule_results": rule_results, "reasoning": reasoning}

@tool("Generate Risk Assessment Report")
def generate_risk_assessment_report(data: dict) -> dict:
    recommendation = data.get("recommendation")
    dti = data.get("DTI")
    ltv = data.get("LTV")
    credit_score = data.get("creditScore")
    reasoning = data.get("reasoning")
    # Placeholder for report generation
    storage_location = "/path/to/report.json"  # Example path
    notification_status = "notified"  # Example status
    return {"storage_location": storage_location, "notification_status": notification_status}

@tool("Financial Calculator")
def financial_calculator(data: dict) -> dict:
    # Placeholder for financial calculations
    return calculate_financial_metrics(data)

@tool("Report Generator")
def report_generator(data: dict) -> dict:
    # Placeholder for report generation
    return generate_risk_assessment_report(data)

@tool("Rule Engine")
def rule_engine(data: dict) -> dict:
    # Placeholder for rule evaluation
    return evaluate_underwriting_rules(data)
