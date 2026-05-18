from crewai import Crew
from agents import agents

def create_crew() -> Crew:
    return Crew(
        agents=agents,
        kickoff_inputs={
            "bank_statements": "pipeline_input_schema",
            "credit_report": "pipeline_input_schema",
            "loan_amount": "pipeline_input_schema",
            "property_value": "pipeline_input_schema",
            "applicant_name": "pipeline_input_schema"
        }
    )
