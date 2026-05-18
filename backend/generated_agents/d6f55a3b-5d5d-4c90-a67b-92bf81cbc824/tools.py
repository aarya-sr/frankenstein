from crewai.tools import tool
import pytesseract
from PIL import Image
import fitz
import json

def ocr_tesseract(file_path: str, language: str = "eng") -> dict:
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang=language)
    confidence_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    avg_confidence = sum(float(c) for c in confidence_data["conf"] if c != "-1") / max(len([c for c in confidence_data["conf"] if c != "-1"]), 1)
    return {"text": text, "confidence": round(avg_confidence / 100, 2)}

@tool("Extract Text from Documents")
def extract_text_from_documents(data: dict) -> dict:
    bank_statements_path = data.get("bank_statements_path")
    credit_reports_path = data.get("credit_reports_path")
    bank_data = pdf_parser_pymupdf(bank_statements_path)
    credit_data = pdf_parser_pymupdf(credit_reports_path)
    return {"extracted_bank_data": bank_data, "extracted_credit_data": credit_data}


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

@tool("Transform Extracted Data")
def transform_extracted_data(data: dict) -> dict:
    extracted_bank_data = data.get("extracted_bank_data")
    extracted_credit_data = data.get("extracted_credit_data")
    # Placeholder transformation logic
    structured_data = {"structured_financial_data": {}, "monthly_income": 5000, "monthly_debt": 1500, "loan_amount": 250000, "property_value": 300000}
    return structured_data

@tool("Calculate Risk Ratios")
def calculate_risk_ratios(data: dict) -> dict:
    structured_financial_data = data.get("structured_financial_data")
    monthly_income = data.get("monthly_income")
    monthly_debt = data.get("monthly_debt")
    loan_amount = data.get("loan_amount")
    property_value = data.get("property_value")
    dti_ratio = monthly_debt / monthly_income
    ltv_ratio = loan_amount / property_value
    risk_metrics = {"dti_ratio": dti_ratio, "ltv_ratio": ltv_ratio}
    return {"dti_ratio": dti_ratio, "ltv_ratio": ltv_ratio, "risk_metrics": risk_metrics}

@tool("Evaluate Underwriting Rules")
def evaluate_underwriting_rules(data: dict) -> dict:
    dti_ratio = data.get("dti_ratio")
    ltv_ratio = data.get("ltv_ratio")
    risk_metrics = data.get("risk_metrics")
    # Placeholder rule evaluation logic
    underwriting_decision = "Approved" if dti_ratio <= 0.43 and ltv_ratio <= 0.80 else "Denied"
    decision_rationale = "DTI and LTV within acceptable limits" if underwriting_decision == "Approved" else "DTI or LTV exceeds limits"
    return {"underwriting_decision": underwriting_decision, "decision_rationale": decision_rationale, "dti_ratio": dti_ratio, "ltv_ratio": ltv_ratio, "risk_metrics": risk_metrics}

@tool("Generate Risk Assessment Report")
def generate_risk_assessment_report(data: dict) -> dict:
    dti_ratio = data.get("dti_ratio")
    ltv_ratio = data.get("ltv_ratio")
    underwriting_decision = data.get("underwriting_decision")
    decision_rationale = data.get("decision_rationale")
    risk_metrics = data.get("risk_metrics")
    report = {
        "risk_assessment_report": {
            "dti_ratio": dti_ratio,
            "ltv_ratio": ltv_ratio,
            "underwriting_decision": underwriting_decision,
            "decision_rationale": decision_rationale,
            "risk_metrics": risk_metrics
        },
        "report_format": "json"
    }
    return report

@tool("Financial Calculator")
def financial_calculator(data: dict) -> dict:
    # Placeholder for financial calculations
    return {}

@tool("JSON Transformer")
def json_transformer(data: dict) -> dict:
    # Placeholder for JSON transformation logic
    return {}

@tool("Report Generator")
def report_generator(data: dict) -> dict:
    # Placeholder for report generation logic
    return {}

@tool("Rule Engine")
def rule_engine(data: dict) -> dict:
    # Placeholder for rule engine logic
    return {}
