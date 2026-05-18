from crewai import Crew, Process
from agents import (
    data_extraction_agent,
    risk_calculation_agent,
    underwriting_rules_agent,
    report_generation_agent,
    storage_agent
)
from tasks import (
    data_extraction_task,
    risk_calculation_task,
    underwriting_rules_task,
    report_generation_task,
    storage_task
)


def create_crew() -> Crew:
    """Create and return the loan underwriting risk assessment crew."""
    crew = Crew(
        agents=[
            data_extraction_agent,
            risk_calculation_agent,
            underwriting_rules_agent,
            report_generation_agent,
            storage_agent
        ],
        tasks=[
            data_extraction_task,
            risk_calculation_task,
            underwriting_rules_task,
            report_generation_task,
            storage_task
        ],
        process=Process.sequential,
        memory=False,
        verbose=True
    )
    return crew
