import json
from crewai.tools import tool


def _ensure_dict(data):
    """Ensure data is a dict, parsing from JSON string if needed."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return {"raw": str(data) if data else ""}


@tool("PDF Parser")
def pdf_parser(data: dict) -> dict:
    """Extracts text and tables from PDF file paths. Expects data with key 'file_path' pointing to a PDF file. If the file is not found or not a real PDF, returns the raw data as text."""
    data = _ensure_dict(data)
    file_path = data.get("file_path", "")
    try:
        import fitz
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            page_data = {"page": page.number + 1, "text": page.get_text()}
            try:
                tables = page.find_tables()
                page_data["tables"] = [[cell for cell in row] for table in tables for row in table.extract()]
            except Exception:
                page_data["tables"] = []
            pages.append(page_data)
        doc.close()
        return {"pages": pages, "total_pages": len(pages)}
    except Exception as e:
        return {"text": str(data), "tables": [], "parse_note": f"Could not parse as PDF: {str(e)}. Returning raw data."}


@tool("CSV Parser")
def csv_parser(data: dict) -> dict:
    """Parses CSV file content into structured JSON records. Expects data with key 'file_path' pointing to a CSV file. If file not found, returns raw data."""
    data = _ensure_dict(data)
    file_path = data.get("file_path", "")
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        records = df.to_dict(orient="records")
        return {"json_data": records, "columns": list(df.columns), "row_count": len(df)}
    except Exception as e:
        return {"json_data": [], "parse_note": f"Could not parse as CSV: {str(e)}. Returning empty."}


@tool("XML Parser")
def xml_parser(data: dict) -> dict:
    """Parses XML file content into structured JSON records. Expects data with key 'file_path' pointing to an XML file. If file not found, returns raw data."""
    data = _ensure_dict(data)
    file_path = data.get("file_path", "")
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()

        def elem_to_dict(elem):
            result = {}
            for child in elem:
                if len(child) > 0:
                    result[child.tag] = elem_to_dict(child)
                else:
                    result[child.tag] = child.text
            if not result:
                return elem.text
            return result

        json_data = elem_to_dict(root)
        return {"json_data": json_data}
    except Exception as e:
        return {"json_data": {}, "parse_note": f"Could not parse as XML: {str(e)}. Returning empty."}


@tool("Data Transformer")
def data_transformer(data: dict) -> dict:
    """Merges and normalizes parsed document fragments into a unified canonical JSON structure. Expects data with 'parsed_documents' (list of parsed data dicts) and optional 'field_mappings' (dict mapping source fields to target fields)."""
    data = _ensure_dict(data)
    parsed_documents = data.get("parsed_documents", [])
    field_mappings = data.get("field_mappings", {
        "account_holder_name": "applicant_name",
        "transaction_amount": "transaction_amount",
        "transaction_date": "transaction_date",
        "transaction_description": "transaction_description",
        "balance": "current_balance",
        "monthly_income": "monthly_income",
        "credit_score": "credit_score",
        "total_outstanding_debt": "total_outstanding_debt",
        "payment_history": "payment_history",
        "credit_utilization_ratio": "credit_utilization_ratio",
        "number_of_open_accounts": "number_of_open_accounts",
        "public_records": "public_records"
    })

    unified = {
        "applicant_name": None,
        "monthly_income": 0,
        "total_outstanding_debt": 0,
        "credit_score": 0,
        "payment_history": [],
        "current_balance": 0,
        "credit_utilization_ratio": 0,
        "number_of_open_accounts": 0,
        "public_records": [],
        "transactions": []
    }

    if isinstance(parsed_documents, list):
        for doc in parsed_documents:
            if not isinstance(doc, dict):
                continue
            for source_key, target_key in field_mappings.items():
                if source_key in doc:
                    val = doc[source_key]
                    if target_key in unified:
                        if isinstance(unified[target_key], list) and isinstance(val, list):
                            unified[target_key].extend(val)
                        elif unified[target_key] is None or unified[target_key] == 0:
                            unified[target_key] = val
                    else:
                        unified[target_key] = val

            if "transaction_amount" in doc:
                tx = {
                    "amount": doc.get("transaction_amount", 0),
                    "date": doc.get("transaction_date", ""),
                    "description": doc.get("transaction_description", "")
                }
                unified["transactions"].append(tx)

    return {"unified_data": unified}


@tool("Financial Calculator")
def financial_calculator(data: dict) -> dict:
    """Calculates DTI, LTV, income stability, and other financial ratios from structured financial data. Expects data with keys: monthly_income, total_outstanding_debt, loan_amount, property_value, and optionally transactions."""
    data = _ensure_dict(data)
    monthly_income = float(data.get("monthly_income", 0))
    total_outstanding_debt = float(data.get("total_outstanding_debt", 0))
    loan_amount = float(data.get("loan_amount", 0))
    property_value = float(data.get("property_value", 1))
    transactions = data.get("transactions", [])

    # DTI = total monthly debt / monthly income (as percentage)
    monthly_debt = total_outstanding_debt / 12.0 if total_outstanding_debt > 0 else 0
    dti = round((monthly_debt / max(monthly_income, 1)) * 100, 2)

    # LTV = loan_amount / property_value (as percentage)
    ltv = round((loan_amount / max(property_value, 1)) * 100, 2)

    # Income stability assessment
    if isinstance(transactions, list) and len(transactions) > 1:
        incomes = [t.get("amount", 0) for t in transactions if isinstance(t, dict) and t.get("amount", 0) > 0]
        if len(incomes) > 1:
            avg_inc = sum(incomes) / len(incomes)
            variance = sum((i - avg_inc) ** 2 for i in incomes) / len(incomes)
            stability_ratio = 1 - min(variance / max(avg_inc ** 2, 1), 1)
            if stability_ratio > 0.7:
                income_stability = "stable"
            elif stability_ratio > 0.4:
                income_stability = "moderate"
            else:
                income_stability = "unstable"
        else:
            income_stability = "insufficient_data"
    else:
        income_stability = "insufficient_data"

    financial_ratios = {
        "DTI": dti,
        "LTV": ltv,
        "monthly_debt_obligation": round(monthly_debt, 2),
        "monthly_income": monthly_income,
        "loan_amount": loan_amount,
        "property_value": property_value
    }

    return {
        "DTI": dti,
        "LTV": ltv,
        "income_stability": income_stability,
        "financial_ratios": financial_ratios
    }


@tool("Rule Engine")
def rule_engine(data: dict) -> dict:
    """Evaluates financial metrics against underwriting rules and returns pass/fail results with reasoning. Expects data with keys: DTI, LTV, credit_score, monthly_income, and optionally rules (list of rule dicts)."""
    data = _ensure_dict(data)
    dti = float(data.get("DTI", 0))
    ltv = float(data.get("LTV", 0))
    credit_score = float(data.get("credit_score", 0))
    monthly_income = float(data.get("monthly_income", 0))

    rules = data.get("rules", [
        {"name": "DTI_threshold", "field": "DTI", "operator": "<", "threshold": 36},
        {"name": "LTV_threshold", "field": "LTV", "operator": "<", "threshold": 80},
        {"name": "credit_score_minimum", "field": "credit_score", "operator": ">=", "threshold": 620},
        {"name": "income_verification", "field": "monthly_income", "operator": ">", "threshold": 0}
    ])

    metrics = {
        "DTI": dti,
        "LTV": ltv,
        "credit_score": credit_score,
        "monthly_income": monthly_income
    }

    results = []
    all_passed = True
    for rule in rules:
        field = rule.get("field", "")
        value = metrics.get(field)
        if value is None:
            results.append({"rule": rule["name"], "passed": False, "reason": f"Missing field: {field}"})
            all_passed = False
            continue
        op = rule.get("operator", "<")
        threshold = rule.get("threshold", 0)
        passed = False
        if op == "<":
            passed = value < threshold
        elif op == "<=":
            passed = value <= threshold
        elif op == ">":
            passed = value > threshold
        elif op == ">=":
            passed = value >= threshold
        elif op == "==":
            passed = value == threshold

        if not passed:
            all_passed = False

        results.append({
            "rule": rule["name"],
            "passed": passed,
            "value": value,
            "threshold": threshold,
            "reason": f"{field} {'passed' if passed else 'failed'}: {value} {op} {threshold}"
        })

    return {
        "rule_evaluation_results": results,
        "all_rules_passed": all_passed
    }


@tool("Scoring Engine")
def scoring_engine(data: dict) -> dict:
    """Produces a weighted composite risk score from financial metrics with per-metric breakdown. Expects data with keys: DTI, LTV, credit_score, payment_history, and optionally weights."""
    data = _ensure_dict(data)
    dti = float(data.get("DTI", 50))
    ltv = float(data.get("LTV", 80))
    credit_score = float(data.get("credit_score", 0))
    payment_history = data.get("payment_history", [])

    weights = data.get("weights", {
        "DTI": 0.3,
        "LTV": 0.25,
        "credit_score": 0.3,
        "payment_history": 0.15
    })

    # Normalize DTI: lower is better, 0% = 1.0, 50%+ = 0.0
    dti_score = max(0, min(1, 1 - (dti / 50)))

    # Normalize LTV: lower is better, 0% = 1.0, 100%+ = 0.0
    ltv_score = max(0, min(1, 1 - (ltv / 100)))

    # Normalize credit score: 300-850 range
    credit_norm = max(0, min(1, (credit_score - 300) / 550))

    # Payment history score: ratio of on-time payments
    if isinstance(payment_history, list) and len(payment_history) > 0:
        on_time = sum(1 for p in payment_history if isinstance(p, dict) and p.get("status", "").lower() in ["on-time", "on_time", "current"])
        ph_score = on_time / len(payment_history)
    else:
        ph_score = 0.5  # neutral if no data

    metric_scores = {
        "DTI": dti_score,
        "LTV": ltv_score,
        "credit_score": credit_norm,
        "payment_history": ph_score
    }

    composite = 0.0
    score_breakdown = {}
    risk_factors = []

    for metric_name, weight in weights.items():
        raw = metric_scores.get(metric_name, 0)
        weighted = round(raw * weight, 4)
        composite += weighted
        score_breakdown[metric_name] = {
            "raw_score": round(raw, 4),
            "weight": weight,
            "weighted_score": weighted
        }
        if raw < 0.5:
            risk_factors.append(f"{metric_name} is below acceptable threshold (score: {round(raw, 4)})")

    composite = round(composite, 4)

    # Risk score: higher composite = lower risk. We invert for risk_score.
    risk_score = round(1 - composite, 4)

    return {
        "risk_score": risk_score,
        "composite_score": composite,
        "risk_factors": risk_factors,
        "score_breakdown": score_breakdown
    }


@tool("Report Generator")
def report_generator(data: dict) -> dict:
    """Compiles analysis results into a structured JSON risk assessment report with all required sections. Expects data with keys: applicant_name, monthly_income, DTI, LTV, credit_score, income_stability, risk_score, risk_factors, rule_evaluation_results, recommendation."""
    data = _ensure_dict(data)
    applicant_name = data.get("applicant_name", "Unknown")
    monthly_income = data.get("monthly_income", 0)
    dti = data.get("DTI", 0)
    ltv = data.get("LTV", 0)
    credit_score = data.get("credit_score", 0)
    income_stability = data.get("income_stability", "unknown")
    risk_score = data.get("risk_score", 0)
    risk_factors = data.get("risk_factors", [])
    rule_evaluation_results = data.get("rule_evaluation_results", [])
    recommendation = data.get("recommendation", "refer")

    risk_level = "Low" if risk_score < 0.3 else "Medium" if risk_score < 0.6 else "High"

    applicant_information = {
        "name": applicant_name,
        "monthly_income": monthly_income
    }

    financial_data_summary = {
        "DTI": dti,
        "LTV": ltv,
        "monthly_income": monthly_income,
        "income_stability": income_stability
    }

    credit_score_analysis = {
        "credit_score": credit_score,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }

    notes_parts = []
    notes_parts.append(f"Risk assessment completed for {applicant_name}.")
    notes_parts.append(f"Overall risk level: {risk_level} (score: {risk_score}).")
    if risk_factors:
        notes_parts.append(f"Key risk factors: {'; '.join(str(r) for r in risk_factors)}.")
    failed_rules = [r for r in rule_evaluation_results if isinstance(r, dict) and not r.get("passed", True)]
    if failed_rules:
        notes_parts.append(f"Failed rules: {', '.join(r.get('rule', 'unknown') for r in failed_rules)}.")
    else:
        notes_parts.append("All underwriting rules passed.")
    notes = " ".join(notes_parts)

    return {
        "applicant_information": applicant_information,
        "financial_data_summary": financial_data_summary,
        "credit_score_analysis": credit_score_analysis,
        "underwriting_rules_applied": rule_evaluation_results,
        "recommendation": recommendation,
        "notes": notes
    }


@tool("Email Sender")
def email_sender(data: dict) -> dict:
    """Sends the risk assessment report to the designated underwriter via email. Expects data with keys: report (the report dict or string) and recipient (email address string). In this simulation, it logs the action and returns a delivery status."""
    data = _ensure_dict(data)
    report = data.get("report", {})
    recipient = data.get("recipient", "underwriter@example.com")

    # Simulated email sending
    try:
        report_summary = str(report)[:500] if report else "Empty report"
        return {
            "email_delivery_status": "sent",
            "recipient": recipient,
            "message": f"Report successfully sent to {recipient}.",
            "report_preview": report_summary
        }
    except Exception as e:
        return {
            "email_delivery_status": "failed",
            "recipient": recipient,
            "message": f"Failed to send email: {str(e)}"
        }


@tool("Database Writer")
def database_writer(data: dict) -> dict:
    """Persists the risk assessment report to the secure database for audit and compliance. Expects data with keys: report (the report dict) and applicant_name (string). In this simulation, it logs the action and returns a write confirmation."""
    data = _ensure_dict(data)
    report = data.get("report", {})
    applicant_name = data.get("applicant_name", "Unknown")

    # Simulated database write
    try:
        import hashlib
        import datetime
        report_str = json.dumps(report, default=str)
        record_id = hashlib.md5(report_str.encode()).hexdigest()[:12]
        return {
            "write_confirmation": {
                "status": "success",
                "record_id": record_id,
                "table": "risk_assessment_reports",
                "applicant_name": applicant_name,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "write_confirmation": {
                "status": "failed",
                "error": str(e)
            }
        }
