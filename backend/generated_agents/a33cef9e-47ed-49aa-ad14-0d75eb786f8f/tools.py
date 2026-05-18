import os
import json
import csv
from crewai.tools import tool


@tool("PDF Parser Bank Statement")
def pdf_parser_bank(data: dict) -> dict:
    """Extracts text and tables from bank statement PDF files. Provide data with key 'file_path' pointing to the PDF file path."""
    file_path = data.get("file_path", "")
    try:
        import fitz
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            page_data = {"page": page.number + 1, "text": page.get_text()}
            try:
                tables = page.find_tables()
                page_data["tables"] = [[table.extract() for table in tables] if tables else []]
            except Exception:
                page_data["tables"] = []
            pages.append(page_data)
        doc.close()
        return {"document_type": "bank_statement", "pages": pages, "total_pages": len(pages), "text": "\n".join(p.get("text", "") for p in pages), "tables": [t for p in pages for t in p.get("tables", [])]}
    except FileNotFoundError:
        return {"document_type": "bank_statement", "pages": [], "total_pages": 0, "text": "", "tables": [], "error": f"File not found: {file_path}"}
    except Exception as e:
        return {"document_type": "bank_statement", "pages": [], "total_pages": 0, "text": "", "tables": [], "error": str(e)}


@tool("PDF Parser Credit Report")
def pdf_parser_credit(data: dict) -> dict:
    """Extracts text and tables from credit report PDF files. Provide data with key 'file_path' pointing to the PDF file path."""
    file_path = data.get("file_path", "")
    try:
        import fitz
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            page_data = {"page": page.number + 1, "text": page.get_text()}
            try:
                tables = page.find_tables()
                page_data["tables"] = [[table.extract() for table in tables] if tables else []]
            except Exception:
                page_data["tables"] = []
            pages.append(page_data)
        doc.close()
        return {"document_type": "credit_report", "pages": pages, "total_pages": len(pages), "text": "\n".join(p.get("text", "") for p in pages), "tables": [t for p in pages for t in p.get("tables", [])]}
    except FileNotFoundError:
        return {"document_type": "credit_report", "pages": [], "total_pages": 0, "text": "", "tables": [], "error": f"File not found: {file_path}"}
    except Exception as e:
        return {"document_type": "credit_report", "pages": [], "total_pages": 0, "text": "", "tables": [], "error": str(e)}


@tool("CSV Parser Financial")
def csv_parser_financial(data: dict) -> dict:
    """Parses a CSV file of structured financial data into JSON records. Provide data with key 'file_path' pointing to the CSV file path."""
    file_path = data.get("file_path", "")
    delimiter = data.get("delimiter", ",")
    try:
        import pandas as pd
        df = pd.read_csv(file_path, delimiter=delimiter)
        records = df.to_dict(orient="records")
        return {"records": records, "columns": list(df.columns), "row_count": len(df)}
    except FileNotFoundError:
        return {"records": [], "columns": [], "row_count": 0, "error": f"File not found: {file_path}"}
    except Exception as e:
        return {"records": [], "columns": [], "row_count": 0, "error": str(e)}


@tool("Financial Calculator")
def financial_calc(data: dict) -> dict:
    """Calculates DTI, LTV, income stability, and overdraft frequency from extracted financial JSON data. Provide data with key 'extracted_financial_data' containing transactions, loan_amount, and property_value."""
    extracted = data.get("extracted_financial_data", {})
    transactions = extracted.get("transactions", [])
    incomes = [t["amount"] for t in transactions if t.get("amount", 0) > 0]
    expenses = [abs(t["amount"]) for t in transactions if t.get("amount", 0) < 0]
    total_income = sum(incomes)
    total_expenses = sum(expenses)
    dti = round(total_expenses / max(total_income, 1), 4)
    loan_amount = extracted.get("loan_amount", 0)
    property_value = extracted.get("property_value", 1)
    ltv = round(loan_amount / max(property_value, 1), 4)
    overdrafts = sum(1 for t in transactions if t.get("amount", 0) < -1000)
    avg_income = total_income / max(len(incomes), 1)
    income_variance = sum((i - avg_income) ** 2 for i in incomes) / max(len(incomes), 1)
    income_stability = round(1 - min(income_variance / max(avg_income ** 2, 1), 1), 4)
    large_unusual = [t for t in transactions if abs(t.get("amount", 0)) > avg_income * 0.5 and t.get("category") not in ["payroll", "rent", "mortgage"]]
    return {
        "dti": dti,
        "ltv": ltv,
        "income_stability": income_stability,
        "overdraft_frequency": overdrafts,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "unusual_transactions": len(large_unusual)
    }


@tool("Statistical Analyzer")
def stat_analyzer(data: dict) -> dict:
    """Computes statistical metrics (mean, median, std_dev, outlier detection, trends) on financial transaction data. Provide data with key 'extracted_financial_data' containing transaction records."""
    extracted = data.get("extracted_financial_data", {})
    transactions = extracted.get("transactions", [])
    if not transactions:
        return {"mean": 0, "median": 0, "std_dev": 0, "outliers": [], "trends": "insufficient_data", "statistics": {}}
    try:
        import pandas as pd
        df = pd.DataFrame(transactions)
        numeric_fields = df.select_dtypes(include="number").columns.tolist()
        stats = {}
        for field in numeric_fields:
            col = df[field].dropna()
            if len(col) == 0:
                continue
            q1 = col.quantile(0.25)
            q3 = col.quantile(0.75)
            iqr = q3 - q1
            outliers = col[(col < q1 - 1.5 * iqr) | (col > q3 + 1.5 * iqr)].tolist()
            stats[field] = {
                "mean": round(float(col.mean()), 4),
                "median": round(float(col.median()), 4),
                "std": round(float(col.std()), 4) if len(col) > 1 else 0.0,
                "min": round(float(col.min()), 4),
                "max": round(float(col.max()), 4),
                "outlier_count": len(outliers)
            }
        amounts = [t.get("amount", 0) for t in transactions]
        overall_mean = round(sum(amounts) / max(len(amounts), 1), 4)
        sorted_amounts = sorted(amounts)
        mid = len(sorted_amounts) // 2
        overall_median = sorted_amounts[mid] if len(sorted_amounts) % 2 != 0 else round((sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2, 4) if sorted_amounts else 0
        variance = sum((a - overall_mean) ** 2 for a in amounts) / max(len(amounts) - 1, 1)
        overall_std = round(variance ** 0.5, 4)
        trend = "stable"
        if len(amounts) >= 4:
            first_half = sum(amounts[:len(amounts)//2]) / max(len(amounts)//2, 1)
            second_half = sum(amounts[len(amounts)//2:]) / max(len(amounts) - len(amounts)//2, 1)
            if second_half > first_half * 1.1:
                trend = "increasing"
            elif second_half < first_half * 0.9:
                trend = "decreasing"
        return {
            "mean": overall_mean,
            "median": overall_median,
            "std_dev": overall_std,
            "outliers": [],
            "trends": trend,
            "statistics": stats,
            "fields_analyzed": list(stats.keys())
        }
    except Exception as e:
        return {"mean": 0, "median": 0, "std_dev": 0, "outliers": [], "trends": "error", "statistics": {}, "error": str(e)}


@tool("Rule Engine")
def rule_engine_inst(data: dict) -> dict:
    """Evaluates risk ratios against underwriting rules (DTI<=0.43, LTV<=0.80, credit_score>=620, income_stability>=0.7) and returns pass/fail with reasoning. Provide data with keys 'risk_ratios' and 'extracted_financial_data'."""
    risk_ratios = data.get("risk_ratios", {})
    extracted = data.get("extracted_financial_data", {})
    credit_score = extracted.get("credit_score", 0)
    eval_data = {
        "dti": risk_ratios.get("dti", 0),
        "ltv": risk_ratios.get("ltv", 0),
        "credit_score": credit_score,
        "income_stability": risk_ratios.get("income_stability", 0)
    }
    rules = [
        {"name": "dti_check", "field": "dti", "operator": "<=", "threshold": 0.43, "severity": "high", "weight": 0.3},
        {"name": "ltv_check", "field": "ltv", "operator": "<=", "threshold": 0.80, "severity": "high", "weight": 0.25},
        {"name": "credit_score_check", "field": "credit_score", "operator": ">=", "threshold": 620, "severity": "high", "weight": 0.25},
        {"name": "income_stability_check", "field": "income_stability", "operator": ">=", "threshold": 0.7, "severity": "medium", "weight": 0.2}
    ]
    results = []
    violations = []
    score = 0.0
    for rule in rules:
        value = eval_data.get(rule["field"])
        if value is None:
            entry = {"rule": rule["name"], "passed": False, "reason": f"Missing field: {rule['field']}", "severity": rule["severity"]}
            results.append(entry)
            violations.append(entry)
            continue
        op = rule["operator"]
        threshold = rule["threshold"]
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
        entry = {
            "rule": rule["name"],
            "passed": passed,
            "value": value,
            "threshold": threshold,
            "severity": rule["severity"],
            "reason": f"{rule['field']} {'PASSED' if passed else 'FAILED'}: {value} {op} {threshold}"
        }
        results.append(entry)
        if not passed:
            violations.append(entry)
    return {
        "evaluation_results": results,
        "rule_violations": violations,
        "rules_passed": sum(1 for r in results if r["passed"]),
        "rules_failed": sum(1 for r in results if not r["passed"]),
        "reasoning": "; ".join(r["reason"] for r in results)
    }


@tool("Scoring Engine")
def scoring_engine_inst(data: dict) -> dict:
    """Produces a weighted composite risk score from DTI, LTV, credit score, and income stability metrics. Provide data with keys 'risk_ratios' and 'extracted_financial_data'."""
    risk_ratios = data.get("risk_ratios", {})
    extracted = data.get("extracted_financial_data", {})
    weights = {
        "dti_score": 0.3,
        "ltv_score": 0.25,
        "credit_score_normalized": 0.25,
        "income_stability_score": 0.2
    }
    dti = risk_ratios.get("dti", 0)
    ltv = risk_ratios.get("ltv", 0)
    credit_score = extracted.get("credit_score", 0)
    income_stability = risk_ratios.get("income_stability", 0)
    dti_score = max(0, min(1, 1 - (dti / 0.6)))
    ltv_score = max(0, min(1, 1 - (ltv / 1.0)))
    credit_normalized = max(0, min(1, (credit_score - 300) / 550))
    income_score = max(0, min(1, income_stability))
    metrics = {
        "dti_score": round(dti_score, 4),
        "ltv_score": round(ltv_score, 4),
        "credit_score_normalized": round(credit_normalized, 4),
        "income_stability_score": round(income_score, 4)
    }
    total_score = 0.0
    score_breakdown = {}
    for metric_name, weight in weights.items():
        val = metrics.get(metric_name, 0)
        weighted = round(val * weight, 4)
        total_score += weighted
        score_breakdown[metric_name] = {
            "raw_value": val,
            "weight": weight,
            "weighted_score": weighted
        }
    composite = round(total_score, 4)
    risk_level = "Low" if composite >= 0.7 else "Medium" if composite >= 0.4 else "High"
    return {
        "composite_score": composite,
        "risk_level": risk_level,
        "score_breakdown": score_breakdown,
        "reasoning": "; ".join(f"{k}: {v['weighted_score']} (weight {v['weight']})" for k, v in score_breakdown.items())
    }


@tool("Report Generator")
def report_gen(data: dict) -> dict:
    """Generates a structured risk assessment report from all upstream analysis data. Provide data with keys: extracted_financial_data, risk_ratios, statistical_analysis, underwriting_evaluation, composite_risk_score, extraction_errors, rule_violations."""
    extracted = data.get("extracted_financial_data", {})
    risk_ratios = data.get("risk_ratios", {})
    stat_analysis = data.get("statistical_analysis", {})
    underwriting = data.get("underwriting_evaluation", {})
    composite = data.get("composite_risk_score", {})
    errors = data.get("extraction_errors", [])
    violations = data.get("rule_violations", [])
    sections = []
    sections.append("# Loan Underwriting Risk Assessment Report\n")
    sections.append("## Executive Summary\n")
    risk_level = composite.get("risk_level", "Unknown")
    composite_score = composite.get("composite_score", "N/A")
    sections.append(f"**Composite Risk Score:** {composite_score} ({risk_level} Risk)\n")
    rules_passed = underwriting.get("rules_passed", 0)
    rules_failed = underwriting.get("rules_failed", 0)
    sections.append(f"**Underwriting Rules:** {rules_passed} passed, {rules_failed} failed\n")
    if violations:
        sections.append(f"**Rule Violations:** {len(violations)} violation(s) detected\n")
    sections.append("## Financial Data Summary\n")
    sections.append(f"- **Credit Score:** {extracted.get('credit_score', 'N/A')}")
    sections.append(f"- **Loan Amount:** {extracted.get('loan_amount', 'N/A')}")
    sections.append(f"- **Property Value:** {extracted.get('property_value', 'N/A')}")
    sections.append(f"- **Total Income:** {risk_ratios.get('total_income', 'N/A')}")
    sections.append(f"- **Total Expenses:** {risk_ratios.get('total_expenses', 'N/A')}\n")
    sections.append("## Risk Ratio Analysis\n")
    sections.append(f"- **DTI (Debt-to-Income):** {risk_ratios.get('dti', 'N/A')}")
    sections.append(f"- **LTV (Loan-to-Value):** {risk_ratios.get('ltv', 'N/A')}")
    sections.append(f"- **Income Stability:** {risk_ratios.get('income_stability', 'N/A')}")
    sections.append(f"- **Overdraft Frequency:** {risk_ratios.get('overdraft_frequency', 'N/A')}\n")
    sections.append("## Statistical Analysis\n")
    sections.append(f"- **Mean Transaction:** {stat_analysis.get('mean', 'N/A')}")
    sections.append(f"- **Median Transaction:** {stat_analysis.get('median', 'N/A')}")
    sections.append(f"- **Std Deviation:** {stat_analysis.get('std_dev', 'N/A')}")
    sections.append(f"- **Trend:** {stat_analysis.get('trends', 'N/A')}\n")
    sections.append("## Compliance Results\n")
    eval_results = underwriting.get("evaluation_results", [])
    for result in eval_results:
        status = "PASS" if result.get("passed") else "FAIL"
        sections.append(f"- **{result.get('rule', 'Unknown')}**: {status} - {result.get('reason', '')}")
    sections.append("")
    sections.append("## Composite Risk Score\n")
    breakdown = composite.get("score_breakdown", {})
    for metric_name, metric_info in breakdown.items():
        sections.append(f"- **{metric_name}**: weighted score {metric_info.get('weighted_score', 'N/A')} (weight {metric_info.get('weight', 'N/A')})")
    sections.append(f"\n**Total Composite Score:** {composite_score}\n")
    sections.append("## Recommendations\n")
    if risk_level == "Low":
        sections.append("**Recommendation:** APPROVE - The applicant meets all underwriting criteria with a low risk profile.\n")
    elif risk_level == "Medium":
        sections.append("**Recommendation:** CONDITIONAL APPROVE - The applicant has moderate risk. Additional documentation or conditions may be required.\n")
    else:
        sections.append("**Recommendation:** DECLINE or REFER - The applicant presents high risk. Manual review by senior underwriter recommended.\n")
    if errors:
        sections.append("## Data Extraction Notes\n")
        for err in errors:
            sections.append(f"- {err}")
        sections.append("")
    report_md = "\n".join(sections)
    report_file_path = "risk_assessment_report.md"
    try:
        with open(report_file_path, "w") as f:
            f.write(report_md)
    except Exception as e:
        report_file_path = f"error_writing_report: {str(e)}"
    report_content = {
        "executive_summary": f"Composite Risk Score: {composite_score} ({risk_level} Risk). Rules passed: {rules_passed}, failed: {rules_failed}.",
        "financial_data": {"credit_score": extracted.get("credit_score"), "loan_amount": extracted.get("loan_amount"), "property_value": extracted.get("property_value")},
        "risk_ratios": risk_ratios,
        "statistical_analysis": stat_analysis,
        "compliance_results": eval_results,
        "composite_risk_score": composite,
        "rule_violations": violations,
        "recommendation": risk_level
    }
    return {"report_content": report_content, "report_file_path": report_file_path, "report_markdown": report_md}


@tool("Database Writer")
def db_writer(data: dict) -> dict:
    """Inserts the risk assessment report and metadata into the risk_assessment_reports database table. Provide data with keys 'report_content' and 'report_file_path'."""
    import datetime
    import hashlib
    report_content = data.get("report_content", {})
    report_file_path = data.get("report_file_path", "")
    table = "risk_assessment_reports"
    timestamp = datetime.datetime.utcnow().isoformat()
    content_str = json.dumps(report_content, default=str)
    version_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    record = {
        "timestamp": timestamp,
        "report_file_path": report_file_path,
        "report_content": content_str,
        "version_hash": version_hash,
        "access_control": "internal_underwriting"
    }
    db_url = os.getenv("DATABASE_URL", "sqlite:///output.db")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        columns = list(record.keys())
        col_defs = ", ".join(f"{c} TEXT" for c in columns)
        with engine.begin() as conn:
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})"))
            placeholders = ", ".join(f":{c}" for c in columns)
            col_names = ", ".join(columns)
            conn.execute(text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"), record)
        return {
            "storage_confirmation": f"Report stored successfully in table '{table}' at {timestamp}. Version hash: {version_hash}",
            "record_id": version_hash,
            "timestamp": timestamp,
            "table": table
        }
    except Exception as e:
        return {
            "storage_confirmation": f"Storage failed: {str(e)}",
            "record_id": None,
            "timestamp": timestamp,
            "error": str(e)
        }
