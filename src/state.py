import operator
from typing import TypedDict, Optional, Annotated


class WorkflowState(TypedDict):
    # Input
    query: str
    part_description: str
    shipment_context: dict

    # Supervisor
    query_type: str  # "parts" | "supply_chain" | "finance" | "cross"
    next: str

    # Part identification
    identified_part: Optional[dict]
    identification_confidence: float
    identification_source: str

    # Serial recovery
    recovered_serial: Optional[str]
    recovered_part_number: Optional[str]
    serial_source: str
    serial_confidence: float

    # Routing
    target_business_unit: Optional[str]
    priority: str  # "critical" | "high" | "normal"
    contact_person: Optional[str]
    storage_location: Optional[str]
    qc_required: bool

    # Action plan
    action_plan: Optional[str]

    # Escalation
    escalated: bool
    escalation_reason: Optional[str]
    investigation_package: Optional[dict]

    # Finance / SC answers
    supply_chain_answer: Optional[str]
    finance_answer: Optional[str]
    final_answer: Optional[str]

    messages: Annotated[list, operator.add]


def initial_state(query: str) -> WorkflowState:
    return WorkflowState(
        query=query,
        part_description="",
        shipment_context={},
        query_type="",
        next="",
        identified_part=None,
        identification_confidence=0.0,
        identification_source="",
        recovered_serial=None,
        recovered_part_number=None,
        serial_source="",
        serial_confidence=0.0,
        target_business_unit=None,
        priority="normal",
        contact_person=None,
        storage_location=None,
        qc_required=False,
        action_plan=None,
        escalated=False,
        escalation_reason=None,
        investigation_package=None,
        supply_chain_answer=None,
        finance_answer=None,
        final_answer=None,
        messages=[],
    )
