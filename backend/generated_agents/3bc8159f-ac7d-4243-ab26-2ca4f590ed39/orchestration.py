from crewai import Crew, Process
from agents import (
    data_extraction_agent,
    financial_calculation_agent,
    underwriting_rules_agent,
    report_generation_agent,
    report_delivery_agent
)
from tasks import (
    data_extraction_task,
    financial_calculation_task,
    underwriting_rules_task,
    report_generation_task,
    report_delivery_task
)


def create_crew():
    crew = Crew(
        agents=[
            data_extraction_agent,
            financial_calculation_agent,
            underwriting_rules_agent,
            report_generation_agent,
            report_delivery_agent
        ],
        tasks=[
            data_extraction_task,
            financial_calculation_task,
            underwriting_rules_task,
            report_generation_task,
            report_delivery_task
        ],
        process=Process.sequential,
        verbose=True
    )
    return crew
