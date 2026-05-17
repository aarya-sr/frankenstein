from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DataSpec(BaseModel):
    name: str
    format: str
    description: str
    example: str | None = None


class ProcessStep(BaseModel):
    step_number: int
    description: str
    rules: list[str] = []
    depends_on: list[int] = []


class EdgeCase(BaseModel):
    description: str
    expected_handling: str


class QualityCriterion(BaseModel):
    criterion: str
    validation_method: str


class RequirementsDoc(BaseModel):
    domain: str
    inputs: list[DataSpec]
    outputs: list[DataSpec]
    process_steps: list[ProcessStep]
    edge_cases: list[EdgeCase]
    quality_criteria: list[QualityCriterion]
    constraints: list[str] = []
    assumptions: list[str] = []
    sample_input_example: dict | None = None
    sample_output_example: dict | None = None
    input_entry_mechanism: str | None = None


# ── Internal Elicitor models (not written to pipeline state) ─────────


class CategoryAssessment(BaseModel):
    name: Literal["Input/Output", "Process", "Data", "Edge Cases", "Quality Bar", "Sample Data"]
    confidence: float
    addressed_fields: list[str] = []
    missing_fields: list[str] = []
    notes: str = ""


class GapAnalysisResult(BaseModel):
    categories: list[CategoryAssessment]
    overall_quality: Literal["high", "medium", "low"]

    def gaps(self, threshold: float = 0.7) -> list[CategoryAssessment]:
        """Return categories below threshold, in priority order."""
        priority_order = ["Input/Output", "Process", "Data", "Edge Cases", "Quality Bar", "Sample Data"]
        below = [c for c in self.categories if c.confidence < threshold]
        return sorted(below, key=lambda c: priority_order.index(c.name))

    def all_complete(self, threshold: float = 0.7) -> bool:
        return all(c.confidence >= threshold for c in self.categories)


class QuestionCategory(BaseModel):
    name: str
    confidence: float
    questions: list[str]
