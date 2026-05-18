from crewai import Crew, Process
from agents import (
    data_extraction_agent,
    financial_ratio_agent,
    underwriting_rules_agent,
    report_generation_agent,
    distribution_agent
)
from tasks import (
    data_extraction_task,
    financial_ratio_task,
    underwriting_rules_task,
    report_generation_task,
    distribution_task
)


def create_crew() -> Crew:
    return Crew(
        agents=[
            data_extraction_agent,
            financial_ratio_agent,
            underwriting_rules_agent,
            report_generation_agent,
            distribution_agent
        ],
        tasks=[
            data_extraction_task,
            financial_ratio_task,
            underwriting_rules_task,
            report_generation_task,
            distribution_task
        ],
        process=Process.sequential,
        memory=False,
        verbose=True
    )
