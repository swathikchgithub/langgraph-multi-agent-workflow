#!/usr/bin/env python3
"""
Multi-Agent Parts Workflow — CLI entry point.

Usage:
    python main.py                         # interactive mode
    python main.py "describe a part"       # single query
    python main.py --demo                  # run all demo scenarios
"""
import sys
from dotenv import load_dotenv

load_dotenv()

from src.graph import compile_graph
from src.state import initial_state

DEMO_QUERIES = [
    {
        "label": "Unidentified part with PO",
        "query": "A silver cylindrical bracket arrived without any labels. The shipment came with PO-2024-0445.",
        "context": {"po_number": "PO-2024-0445"},
    },
    {
        "label": "Part by description only",
        "query": "Large rectangular brake caliper assembly, red anodized, no serial, no labels.",
        "context": {},
    },
    {
        "label": "Supply chain query",
        "query": "Which suppliers have the highest defect rates over the past 30 days?",
        "context": {},
    },
    {
        "label": "Finance query",
        "query": "What are the biggest cost overruns by part category this quarter?",
        "context": {},
    },
    {
        "label": "Cross supply chain + finance",
        "query": "Give me a combined view of supplier defect rates and their spend vs budget.",
        "context": {},
    },
]


def run_query(graph, query: str, shipment_context: dict = None) -> dict:
    state = initial_state(query)
    if shipment_context:
        state["shipment_context"] = shipment_context

    result = graph.invoke(state)
    return result


def print_result(result: dict) -> None:
    print("\n" + "=" * 60)

    if result.get("escalated"):
        print("STATUS: ESCALATED — Human review required")
        print(f"Reason: {result.get('escalation_reason', '')}")
        pkg = result.get("investigation_package", {})
        if pkg:
            print(f"Best guess: {pkg.get('best_guess', 'None')} ({pkg.get('best_guess_confidence', 0):.0%})")
            print(f"Quarantine: {pkg.get('quarantine_location', 'Zone Q')}")
            print(f"Temp label: {pkg.get('temp_label', 'UNIDENTIFIED-???')}")

    elif result.get("action_plan"):
        print("STATUS: IDENTIFIED & ROUTED")
        part = result.get("identified_part") or {}
        print(f"Part:       {part.get('part_number')} — {part.get('part_name')}")
        print(f"Serial:     {result.get('recovered_serial', 'not recovered')}")
        print(f"Business Unit: {result.get('target_business_unit')}")
        print(f"Priority:   {result.get('priority')}")
        print(f"Storage:    {result.get('storage_location')}")
        print(f"QC needed:  {result.get('qc_required')}")
        print(f"\nAction Plan:\n{result.get('action_plan')}")

    elif result.get("final_answer"):
        print("STATUS: ANALYSIS COMPLETE")
        print(f"\n{result['final_answer']}")

    elif result.get("supply_chain_answer"):
        print("STATUS: SUPPLY CHAIN ANALYSIS")
        print(f"\n{result['supply_chain_answer']}")

    elif result.get("finance_answer"):
        print("STATUS: FINANCE ANALYSIS")
        print(f"\n{result['finance_answer']}")

    print("=" * 60)


def interactive_mode(graph) -> None:
    print("Multi-Agent Parts Workflow")
    print("Type 'quit' to exit, 'demo' to run demo scenarios\n")

    while True:
        try:
            query = input("Query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not query:
            continue
        if query.lower() == "quit":
            break
        if query.lower() == "demo":
            run_demo(graph)
            continue

        result = run_query(graph, query)
        print_result(result)


def run_demo(graph) -> None:
    print("\n=== RUNNING DEMO SCENARIOS ===\n")
    for i, scenario in enumerate(DEMO_QUERIES, 1):
        print(f"\n[{i}/{len(DEMO_QUERIES)}] {scenario['label']}")
        print(f"Query: {scenario['query']}")
        result = run_query(graph, scenario["query"], scenario.get("context"))
        print_result(result)


def main():
    graph = compile_graph()

    if "--demo" in sys.argv:
        run_demo(graph)
    elif len(sys.argv) > 1:
        query = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
        result = run_query(graph, query)
        print_result(result)
    else:
        interactive_mode(graph)


if __name__ == "__main__":
    main()
