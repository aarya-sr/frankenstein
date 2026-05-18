import json
import os
import xml.etree.ElementTree as ET
from crewai.tools import tool


@tool("PDF Parser")
def parse_pdf(data: dict) -> dict:
    """Extracts text and tables from a PDF file path. Provide data with key 'file_path' pointing to the PDF file."""
    file_path = data.get("file_path", "")
    try:
        import fitz
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            page_data = {"page": page.number + 1, "text": page.get_text()}
            try:
                page_data["tables"] = str(page.find_tables())
            except Exception:
                page_data["tables"] = []
            pages.append(page_data)
        doc.close()
        return {"pages": pages, "total_pages": len(pages)}
    except Exception as e:
        return {"error": str(e), "pages": [], "total_pages": 0}


@tool("CSV Parser")
def parse_csv(data: dict) -> dict:
    """Parses a CSV file into structured JSON data. Provide data with key 'file_path' pointing to the CSV file."""
    file_path = data.get("file_path", "")
    try:
        import pandas as pd
        df = pd.read_csv(file_path, delimiter=data.get("delimiter", ","))
        records = df.to_dict(orient="records")
        return {"json_data": records, "columns": list(df.columns), "row_count": len(df)}
    except Exception as e:
        return {"error": str(e), "json_data": [], "columns": [], "row_count": 0}


@tool("XML Parser")
def parse_xml(data: dict) -> dict:
    """Parses XML content or file into structured JSON data. Provide data with key 'file_path' or 'content'."""
    content = data.get("content", "")
    file_path = data.get("file_path", "")
    try:
        if file_path and os.path.exists(file_path):
            tree = ET.parse(file_path)
            root = tree.getroot()
        elif content:
            root = ET.fromstring(content)
        else:
            return {"error": "No file_path or content provided", "json_data": {}}

        def elem_to_dict(elem):
            result = {}
            if elem.attrib:
                result["@attributes"] = dict(elem.attrib)
            if elem.text and elem.text.strip():
                result["text"] = elem.text.strip()
            for child in elem:
                child_data = elem_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            return result

        parsed = elem_to_dict(root)
        return {"json_data": parsed, "root_tag": root.tag}
    except Exception as e:
        return {"error": str(e), "json_data": {}}


@tool("Financial Calculator")
def calculate_financial_metrics(data: dict) -> dict:
    """Calculates DTI, LTV, and supplementary financial metrics. Provide data with keys: monthly_income, monthly_debt_payments, loan_amount, property_value, credit_score."""
    monthly_income = float(data.get("monthly_income", 0))
    monthly_debt_payments = float(data.get("monthly_debt_payments", 0))
    loan_amount = float(data.get("loan_amount", 0))
    property_value = float(data.get("property_value", 1))
    credit_score = float(data.get("credit_score", 0))

    warnings = []
    if monthly_income <= 0:
        warnings.append("WARNING: monthly_income is zero or negative")
        dti_ratio = 999.99
    else:
        dti_ratio = round((monthly_debt_payments / monthly_income) * 100, 2)

    if property_value <= 0:
        warnings.append("WARNING: property_value is zero or negative")
        ltv_ratio = 999.99
    else:
        ltv_ratio = round((loan_amount / property_value) * 100, 2)

    credit_utilization = None
    financial_ratios = {
        "dti_ratio": dti_ratio,
        "ltv_ratio": ltv_ratio,
        "credit_score": credit_score,
        "monthly_income": monthly_income,
        "monthly_debt_payments": monthly_debt_payments,
        "loan_amount": loan_amount,
        "property_value": property_value
    }

    if warnings:
        financial_ratios["warnings"] = warnings

    return {
        "dti_ratio": dti_ratio,
        "ltv_ratio": ltv_ratio,
        "financial_ratios": financial_ratios
    }


@tool("Data Transformer")
def transform_data(data: dict) -> dict:
    """Transforms, reshapes, and consolidates structured data fields. Provide data with keys 'source_data' (dict or list) and optionally 'transformation_spec' (list of operations)."""
    source_data = data.get("source_data", {})
    transformation_spec = data.get("transformation_spec", [])

    if isinstance(source_data, list):
        records = list(source_data)
    elif isinstance(source_data, dict):
        records = [source_data]
    else:
        records = []

    result = list(records)
    for op in transformation_spec:
        op_type = op.get("type")
        if op_type == "filter":
            field = op["field"]
            value = op["value"]
            result = [r for r in result if r.get(field) == value]
        elif op_type == "rename":
            old_name = op["from"]
            new_name = op["to"]
            result = [{new_name if k == old_name else k: v for k, v in r.items()} for r in result]
        elif op_type == "select":
            fields = op["fields"]
            result = [{k: r.get(k) for k in fields} for r in result]

    return {"transformed_data": result, "count": len(result)}


@tool("Rule Engine")
def evaluate_rules(data: dict) -> dict:
    """Evaluates financial data against underwriting rules. Provide data with keys: dti_ratio, ltv_ratio, credit_score, monthly_income, and optionally 'rules' (list of rule dicts)."""
    rules = data.get("rules", [
        {"name": "dti_threshold", "field": "dti_ratio", "operator": "<=", "threshold": 43, "weight": 0.3, "severity": "high"},
        {"name": "ltv_threshold", "field": "ltv_ratio", "operator": "<=", "threshold": 80, "weight": 0.25, "severity": "high"},
        {"name": "credit_score_minimum", "field": "credit_score", "operator": ">=", "threshold": 620, "weight": 0.3, "severity": "high"},
        {"name": "income_verification", "field": "monthly_income", "operator": ">", "threshold": 0, "weight": 0.15, "severity": "critical"}
    ])

    results = []
    score = 0.0
    for rule in rules:
        field_name = rule["field"]
        value = data.get(field_name)
        if value is None:
            results.append({"rule": rule["name"], "passed": False, "reason": f"Missing field: {field_name}", "severity": rule.get("severity", "medium")})
            continue
        value = float(value)
        op = rule["operator"]
        threshold = float(rule["threshold"])
        passed = False
        if op == "<=" and value <= threshold:
            passed = True
        elif op == ">=" and value >= threshold:
            passed = True
        elif op == "<" and value < threshold:
            passed = True
        elif op == ">" and value > threshold:
            passed = True
        elif op == "==" and value == threshold:
            passed = True

        if passed:
            score += rule.get("weight", 0)
        results.append({
            "rule": rule["name"],
            "passed": passed,
            "value": value,
            "threshold": threshold,
            "severity": rule.get("severity", "medium"),
            "reason": f"{field_name} {'PASS' if passed else 'FAIL'}: {value} {op} {threshold}"
        })

    risk_score = round(1 - score, 4)
    return {
        "rule_evaluation_results": results,
        "risk_score": risk_score,
        "reasoning": "; ".join(r["reason"] for r in results)
    }


@tool("Scoring Engine")
def calculate_scores(data: dict) -> dict:
    """Produces a weighted composite risk score from individual metric scores. Provide data with keys 'metrics' (dict of metric values) and optionally 'weights' (dict of metric weights)."""
    metrics = data.get("metrics", {})
    weights = data.get("weights", {
        "dti_score": 0.3,
        "ltv_score": 0.25,
        "credit_score_metric": 0.3,
        "payment_history_score": 0.15
    })

    scores = {}
    total_score = 0.0
    for field, weight in weights.items():
        if field not in metrics:
            scores[field] = {"score": 0, "weight": weight, "reason": f"Missing metric: {field}"}
            continue
        value = metrics[field]
        if isinstance(value, dict):
            value = value.get("mean", 0)
        value = float(value)
        normalized = min(max(value / 100, 0), 1)
        weighted = normalized * weight
        total_score += weighted
        scores[field] = {
            "raw_value": value,
            "normalized": round(normalized, 4),
            "weighted": round(weighted, 4),
            "weight": weight
        }

    return {
        "composite_risk_score": round(total_score, 4),
        "score_breakdown": scores,
        "reasoning": "; ".join(f"{k}: {v.get('weighted', 0):.4f} (weight {v['weight']})" for k, v in scores.items())
    }


@tool("Report Generator")
def generate_report(data: dict) -> dict:
    """Generates a formatted risk assessment report from structured analysis data. Provide data with key 'report_data' (dict), optionally 'template_sections' (list) and 'output_format' (string)."""
    report_data = data.get("report_data", {})
    template_sections = data.get("template_sections", [
        "applicant_info", "financial_summary", "ratio_analysis",
        "rule_evaluation", "decision_summary"
    ])
    output_format = data.get("output_format", "pdf")

    sections = []
    sections.append("# Risk Assessment Report\n")

    if "applicant_info" in template_sections:
        sections.append("## Applicant Information")
        sections.append(f"- **Applicant Name:** {report_data.get('applicant_name', 'N/A')}")
        sections.append(f"- **Loan Amount:** ${report_data.get('loan_amount', 'N/A'):,.2f}" if isinstance(report_data.get('loan_amount'), (int, float)) else f"- **Loan Amount:** {report_data.get('loan_amount', 'N/A')}")
        sections.append("")

    if "financial_summary" in template_sections:
        sections.append("## Financial Summary")
        sections.append(f"- **Monthly Income:** ${report_data.get('monthly_income', 'N/A'):,.2f}" if isinstance(report_data.get('monthly_income'), (int, float)) else f"- **Monthly Income:** {report_data.get('monthly_income', 'N/A')}")
        sections.append(f"- **Monthly Debt Payments:** ${report_data.get('monthly_debt_payments', 'N/A'):,.2f}" if isinstance(report_data.get('monthly_debt_payments'), (int, float)) else f"- **Monthly Debt Payments:** {report_data.get('monthly_debt_payments', 'N/A')}")
        sections.append("")

    if "ratio_analysis" in template_sections:
        sections.append("## Ratio Analysis")
        sections.append(f"- **DTI Ratio:** {report_data.get('dti_ratio', 'N/A')}%")
        sections.append(f"- **LTV Ratio:** {report_data.get('ltv_ratio', 'N/A')}%")
        sections.append(f"- **Credit Score:** {report_data.get('credit_score', 'N/A')}")
        sections.append("")

    if "rule_evaluation" in template_sections:
        sections.append("## Rule Evaluation")
        rule_results = report_data.get("rule_evaluation_results", [])
        if isinstance(rule_results, list):
            for r in rule_results:
                status = "PASS" if r.get("passed") else "FAIL"
                sections.append(f"- **{r.get('rule', 'Unknown')}**: {status} - {r.get('reason', '')}")
        elif isinstance(rule_results, dict):
            sections.append(f"  {json.dumps(rule_results, indent=2)}")
        else:
            sections.append(f"  {str(rule_results)}")
        sections.append("")

    if "decision_summary" in template_sections:
        sections.append("## Decision Summary")
        sections.append(f"- **Underwriting Decision:** {report_data.get('underwriting_decision', 'N/A')}")
        sections.append(f"- **Composite Risk Score:** {report_data.get('composite_risk_score', 'N/A')}")
        sections.append(f"- **Comments:** {report_data.get('comments', 'N/A')}")
        sections.append("")

    report_md = "\n".join(sections)
    return {
        "risk_assessment_report": report_md,
        "output_format": output_format,
        "executive_summary": f"Risk assessment complete. Decision: {report_data.get('underwriting_decision', 'N/A')}. Score: {report_data.get('composite_risk_score', 'N/A')}."
    }


@tool("Email Sender")
def send_email(data: dict) -> dict:
    """Sends the risk assessment report via email. Provide data with keys: recipients (list or string), subject (string), body (string), and optionally attachments (list)."""
    recipients = data.get("recipients", "underwriting-team@company.com")
    subject = data.get("subject", "Risk Assessment Report")
    body = data.get("body", "")
    attachments = data.get("attachments", [])

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if isinstance(recipients, list):
            to_addr = ", ".join(recipients)
        else:
            to_addr = str(recipients)

        msg = MIMEMultipart()
        msg["From"] = os.getenv("SMTP_FROM", "noreply@company.com")
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if smtp_host:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                user = os.getenv("SMTP_USER")
                pwd = os.getenv("SMTP_PASSWORD")
                if user and pwd:
                    server.login(user, pwd)
                server.send_message(msg)
            return {"email_status": "sent_successfully", "to": to_addr, "subject": subject}
        else:
            return {"email_status": "simulated_success_no_smtp_configured", "to": to_addr, "subject": subject}
    except Exception as e:
        return {"email_status": f"failed: {str(e)}"}


@tool("Database Writer")
def write_to_database(data: dict) -> dict:
    """Writes risk assessment report data to the database. Provide data with keys: table_name (string), record (dict), operation (string: insert or upsert)."""
    table_name = data.get("table_name", "risk_assessment_reports")
    record = data.get("record", {})
    operation = data.get("operation", "upsert")

    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv("DATABASE_URL", "sqlite:///output.db")
        engine = create_engine(db_url)

        if not record:
            return {"database_status": "no_record_provided", "written": 0}

        # Serialize any non-string values
        serialized_record = {}
        for k, v in record.items():
            if isinstance(v, (dict, list)):
                serialized_record[k] = json.dumps(v)
            else:
                serialized_record[k] = str(v) if v is not None else ""

        columns = list(serialized_record.keys())
        col_defs = ", ".join(f"\"{c}\" TEXT" for c in columns)

        with engine.begin() as conn:
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS \"{table_name}\" ({col_defs})"))
            placeholders = ", ".join(f":{c}" for c in columns)
            col_names = ", ".join(f"\"{c}\"" for c in columns)
            conn.execute(text(f"INSERT INTO \"{table_name}\" ({col_names}) VALUES ({placeholders})"), serialized_record)

        return {"database_status": "written_successfully", "table": table_name, "written": 1}
    except Exception as e:
        return {"database_status": f"failed: {str(e)}"}
