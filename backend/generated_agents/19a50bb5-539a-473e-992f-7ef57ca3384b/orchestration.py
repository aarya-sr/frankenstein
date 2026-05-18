from crewai import Crew
from agents import agents

def create_crew() -> Crew:
    return Crew(agents=agents)
