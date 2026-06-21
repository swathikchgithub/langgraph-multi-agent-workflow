from langgraph.graph import StateGraph, END

from src.state import WorkflowState, initial_state
from src.agents import supervisor, part_identifier, serial_resolver, router
from src.agents import action_recommender, escalation, supply_chain, finance, synthesizer

CONFIDENCE_THRESHOLD = 0.7


def _route_after_supervisor(state: WorkflowState) -> str:
    return state["next"]


def _route_after_identification(state: WorkflowState) -> str:
    confidence = state.get("identification_confidence", 0.0)
    if confidence >= CONFIDENCE_THRESHOLD:
        return "serial_resolver"
    return "escalation"


def _route_after_serial(state: WorkflowState) -> str:
    id_conf = state.get("identification_confidence", 0.0)
    ser_conf = state.get("serial_confidence", 0.0)
    if id_conf >= CONFIDENCE_THRESHOLD and ser_conf >= CONFIDENCE_THRESHOLD:
        return "router"
    return "escalation"


def _route_after_router(state: WorkflowState) -> str:
    return "action_recommender"


def _route_cross(state: WorkflowState) -> str:
    return "supply_chain"


def build_graph() -> StateGraph:
    g = StateGraph(WorkflowState)

    g.add_node("supervisor", supervisor.run)
    g.add_node("part_identifier", part_identifier.run)
    g.add_node("serial_resolver", serial_resolver.run)
    g.add_node("router", router.run)
    g.add_node("action_recommender", action_recommender.run)
    g.add_node("escalation", escalation.run)
    g.add_node("supply_chain", supply_chain.run)
    g.add_node("finance", finance.run)
    g.add_node("synthesizer", synthesizer.run)

    g.set_entry_point("supervisor")

    g.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "part_identifier": "part_identifier",
            "supply_chain": "supply_chain",
            "finance": "finance",
            "cross": "supply_chain",
        },
    )

    g.add_conditional_edges(
        "part_identifier",
        _route_after_identification,
        {
            "serial_resolver": "serial_resolver",
            "escalation": "escalation",
        },
    )

    g.add_conditional_edges(
        "serial_resolver",
        _route_after_serial,
        {
            "router": "router",
            "escalation": "escalation",
        },
    )

    g.add_edge("router", "action_recommender")
    g.add_edge("action_recommender", END)
    g.add_edge("escalation", END)

    # Supply chain can lead to finance (cross queries) or synthesizer
    g.add_conditional_edges(
        "supply_chain",
        lambda s: "finance" if s.get("query_type") == "cross" else "synthesizer",
        {
            "finance": "finance",
            "synthesizer": "synthesizer",
        },
    )

    g.add_edge("finance", "synthesizer")
    g.add_edge("synthesizer", END)

    return g


def compile_graph():
    return build_graph().compile()
