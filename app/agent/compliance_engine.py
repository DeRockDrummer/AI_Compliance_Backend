from typing import List
from pydantic import BaseModel

class ControlResult(BaseModel):
    id: str
    name: str
    status: str  # "pass" | "fail" | "partial"
    details: str

class RiskResult(BaseModel):
    id: str
    severity: str  # "low" | "medium" | "high"
    description: str
    related_controls: List[str]

class ComplianceResult(BaseModel):
    overall_score: int
    framework: str
    controls: List[ControlResult]
    risks: List[RiskResult]
    recommendations: List[str]


def analyze_text_for_compliance(text: str) -> ComplianceResult:
    controls: List[ControlResult] = []
    risks: List[RiskResult] = []
    recommendations: List[str] = []

    # Control 1: Documented Purpose
    if "purpose" in text.lower():
        controls.append(ControlResult(
            id="C1",
            name="Documented purpose",
            status="pass",
            details="System purpose appears to be documented."
        ))
    else:
        controls.append(ControlResult(
            id="C1",
            name="Documented purpose",
            status="fail",
            details="No clear mention of system purpose."
        ))
        risks.append(RiskResult(
            id="R1",
            severity="medium",
            description="System purpose is not clearly documented.",
            related_controls=["C1"]
        ))
        recommendations.append("Document the AI system's purpose and intended use.")

    # Control 2: Risk Assessment
    if "risk assessment" in text.lower() or "risk analysis" in text.lower():
        controls.append(ControlResult(
            id="C2",
            name="Risk assessment",
            status="pass",
            details="Risk assessment is mentioned."
        ))
    else:
        controls.append(ControlResult(
            id="C2",
            name="Risk assessment",
            status="fail",
            details="No explicit risk assessment mentioned."
        ))
        risks.append(RiskResult(
            id="R2",
            severity="high",
            description="No documented risk assessment for the AI system.",
            related_controls=["C2"]
        ))
        recommendations.append("Perform and document a risk assessment for the AI system.")

    # Score calculation
    total_controls = len(controls)
    passed_controls = sum(1 for c in controls if c.status == "pass")
    overall_score = int((passed_controls / total_controls) * 100) if total_controls > 0 else 0

    return ComplianceResult(
        overall_score=overall_score,
        framework="internal_ai_compliance_v1",
        controls=controls,
        risks=risks,
        recommendations=recommendations
    )
