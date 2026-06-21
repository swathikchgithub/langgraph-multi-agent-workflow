"""
Unit and integration tests for the Multi-Agent Parts Workflow.
Run with: pytest tests/ -v
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.state import initial_state, WorkflowState
from src.data.parts_catalog import search_catalog_fuzzy, PARTS_CATALOG
from src.data.purchase_orders import PURCHASE_ORDERS, SUPPLIER_METRICS, FINANCE_DATA
from src.data.business_units import get_routing, ROUTING_RULES
from src.tools.catalog_tools import (
    search_catalog, lookup_po, lookup_by_supplier,
    get_business_unit_info, get_defect_rates, get_cost_variance,
    get_unreconciled_items, dispatch_tool,
)


# ---------------------------------------------------------------------------
# State tests
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_query_is_set(self):
        state = initial_state("test query")
        assert state["query"] == "test query"

    def test_defaults_are_safe(self):
        state = initial_state("x")
        assert state["identification_confidence"] == 0.0
        assert state["serial_confidence"] == 0.0
        assert state["escalated"] is False
        assert state["qc_required"] is False
        assert state["messages"] == []
        assert state["identified_part"] is None

    def test_part_description_starts_empty(self):
        # Supervisor agent fills part_description; initial_state leaves it blank
        state = initial_state("a silver bracket")
        assert state["part_description"] == ""


# ---------------------------------------------------------------------------
# Parts catalog tests
# ---------------------------------------------------------------------------

class TestPartsCatalog:
    def test_exact_keyword_match(self):
        results = search_catalog_fuzzy("LiDAR sensor")
        assert len(results) > 0
        assert results[0]["part_number"] == "LDR-2024-A"

    def test_fuzzy_keyword_match(self):
        results = search_catalog_fuzzy("brake caliper")
        assert any(r["part_number"] == "BCA-2024-F" for r in results)

    def test_no_match_returns_empty(self):
        results = search_catalog_fuzzy("xyzzy nonexistent widget")
        assert results == []

    def test_category_filter(self):
        results = search_catalog_fuzzy("assembly", category="brake_system")
        for r in results:
            assert r["category"] == "brake_system"

    def test_results_sorted_by_score(self):
        results = search_catalog_fuzzy("camera")
        if len(results) > 1:
            assert results[0]["score"] >= results[1]["score"]

    def test_all_catalog_parts_have_required_fields(self):
        required = {"part_number", "name", "category", "keywords", "supplier_name"}
        for part in PARTS_CATALOG:
            missing = required - set(part.keys())
            assert not missing, f"{part['part_number']} missing fields: {missing}"


# ---------------------------------------------------------------------------
# Purchase order tests
# ---------------------------------------------------------------------------

class TestPurchaseOrders:
    def test_known_po_exists(self):
        assert "PO-2024-0445" in PURCHASE_ORDERS

    def test_po_has_line_items(self):
        po = PURCHASE_ORDERS["PO-2024-0445"]
        assert "line_items" in po
        assert len(po["line_items"]) > 0

    def test_line_item_has_serial_range(self):
        po = PURCHASE_ORDERS["PO-2024-0445"]
        item = po["line_items"][0]
        assert "serial_range" in item
        assert "start" in item["serial_range"]
        assert "end" in item["serial_range"]

    def test_supplier_metrics_have_defect_rate(self):
        for sid, metrics in SUPPLIER_METRICS.items():
            assert "defect_rate_30d" in metrics, f"{sid} missing defect_rate_30d"
            assert 0.0 <= metrics["defect_rate_30d"] <= 1.0

    def test_finance_data_has_cost_variance(self):
        assert "cost_variance" in FINANCE_DATA
        assert len(FINANCE_DATA["cost_variance"]) > 0

    def test_unreconciled_items_have_required_fields(self):
        for item in FINANCE_DATA["unreconciled_items"]:
            assert "supplier" in item
            assert "amount" in item
            assert "days_open" in item


# ---------------------------------------------------------------------------
# Business unit routing tests
# ---------------------------------------------------------------------------

class TestBusinessUnitRouting:
    def test_known_category_routes_correctly(self):
        routing = get_routing("sensor_hardware")
        assert routing["business_unit"] == "Sensor Integration Team"

    def test_brake_system_routes_to_safety(self):
        routing = get_routing("brake_system")
        assert routing["business_unit"] == "Safety Systems Team"

    def test_unknown_category_uses_default(self):
        routing = get_routing("unknown_widget_xyz")
        assert routing is not None
        assert "business_unit" in routing

    def test_all_routing_rules_have_contact(self):
        for category, rule in ROUTING_RULES.items():
            assert "contact_person" in rule, f"{category} missing contact_person"
            assert "business_unit" in rule, f"{category} missing business_unit"


# ---------------------------------------------------------------------------
# Tool function tests
# ---------------------------------------------------------------------------

class TestTools:
    def test_search_catalog_returns_json(self):
        result = search_catalog("LiDAR")
        data = json.loads(result)
        assert "matches" in data

    def test_search_catalog_no_match(self):
        result = search_catalog("xyzzy_nonexistent")
        data = json.loads(result)
        assert data["matches"] == []

    def test_lookup_po_found(self):
        result = lookup_po("PO-2024-0445")
        data = json.loads(result)
        assert data["found"] is True
        assert "po" in data

    def test_lookup_po_not_found(self):
        result = lookup_po("PO-9999-9999")
        data = json.loads(result)
        assert data["found"] is False

    def test_lookup_po_case_insensitive(self):
        result = lookup_po("po-2024-0445")
        data = json.loads(result)
        assert data["found"] is True

    def test_lookup_by_supplier_found(self):
        result = lookup_by_supplier("Acme Forgings")
        data = json.loads(result)
        assert data["found"] is True

    def test_lookup_by_supplier_not_found(self):
        result = lookup_by_supplier("NonexistentSupplierXYZ")
        data = json.loads(result)
        assert data["found"] is False

    def test_get_defect_rates_all(self):
        result = get_defect_rates()
        data = json.loads(result)
        assert "suppliers" in data
        assert len(data["suppliers"]) > 0

    def test_get_defect_rates_sorted_descending(self):
        result = get_defect_rates()
        data = json.loads(result)
        rates = [s["defect_rate_30d"] for s in data["suppliers"]]
        assert rates == sorted(rates, reverse=True)

    def test_get_cost_variance_all(self):
        result = get_cost_variance()
        data = json.loads(result)
        assert data["found"] is True
        assert "all_categories" in data

    def test_get_cost_variance_specific_category(self):
        result = get_cost_variance("sensor_hardware")
        data = json.loads(result)
        assert data["found"] is True

    def test_get_unreconciled_items(self):
        result = get_unreconciled_items()
        data = json.loads(result)
        assert "items" in data

    def test_dispatch_tool_unknown(self):
        result = dispatch_tool("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data

    def test_get_business_unit_info_returns_json(self):
        result = get_business_unit_info("sensor_hardware")
        data = json.loads(result)
        assert "business_unit" in data


# ---------------------------------------------------------------------------
# Agent unit tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestSupervisorAgent:
    def test_routes_parts_query(self, mocker):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "query_type": "parts",
            "part_description": "silver bracket",
            "shipment_context": {"po_number": "PO-2024-0445", "supplier_name": None, "quantity": None, "date": None},
            "next": "part_identifier",
            "reasoning": "Query is about identifying an unknown part",
        }))]

        mocker.patch("src.agents.supervisor.call_llm", return_value=mock_response)

        from src.agents import supervisor
        state = initial_state("silver bracket arrived without labels, PO-2024-0445")
        result = supervisor.run(state)

        assert result["query_type"] == "parts"
        assert result["next"] == "part_identifier"
        assert result["part_description"] == "silver bracket"

    def test_routes_supply_chain_query(self, mocker):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "query_type": "supply_chain",
            "part_description": "",
            "shipment_context": {},
            "next": "supply_chain",
            "reasoning": "Query about supplier defect rates",
        }))]

        mocker.patch("src.agents.supervisor.call_llm", return_value=mock_response)

        from src.agents import supervisor
        state = initial_state("Which supplier has the highest defect rate?")
        result = supervisor.run(state)

        assert result["query_type"] == "supply_chain"
        assert result["next"] == "supply_chain"


class TestEscalationAgent:
    def test_escalates_low_confidence_part(self, mocker):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "escalation_reason": "Identification confidence 45% below 70% threshold",
            "investigation_package": {
                "best_guess": "Sensor bracket",
                "best_guess_confidence": 0.45,
                "quarantine_location": "Zone Q / Shelf Q-1",
                "temp_label": "UNIDENTIFIED-20240615-0001",
                "recommended_specialist": "Supplier Quality Engineer",
            },
            "notifications": [],
        }))]

        mocker.patch("src.agents.escalation.call_llm", return_value=mock_response)

        from src.agents import escalation
        state = initial_state("mystery part")
        state["identification_confidence"] = 0.45
        state["serial_confidence"] = 0.0
        result = escalation.run(state)

        assert result["escalated"] is True
        assert "investigation_package" in result
        assert result["investigation_package"]["quarantine_location"] == "Zone Q / Shelf Q-1"


class TestConfidenceRouting:
    def test_high_confidence_routes_to_serial(self):
        from src.graph import _route_after_identification
        state = initial_state("part")
        state["identification_confidence"] = 0.85
        assert _route_after_identification(state) == "serial_resolver"

    def test_low_confidence_routes_to_escalation(self):
        from src.graph import _route_after_identification
        state = initial_state("part")
        state["identification_confidence"] = 0.50
        assert _route_after_identification(state) == "escalation"

    def test_high_serial_confidence_routes_to_router(self):
        from src.graph import _route_after_serial
        state = initial_state("part")
        state["identification_confidence"] = 0.90
        state["serial_confidence"] = 0.85
        assert _route_after_serial(state) == "router"

    def test_low_serial_confidence_escalates(self):
        from src.graph import _route_after_serial
        state = initial_state("part")
        state["identification_confidence"] = 0.90
        state["serial_confidence"] = 0.40
        assert _route_after_serial(state) == "escalation"

    def test_threshold_is_inclusive(self):
        from src.graph import _route_after_identification
        state = initial_state("part")
        state["identification_confidence"] = 0.70
        assert _route_after_identification(state) == "serial_resolver"


# ---------------------------------------------------------------------------
# Integration test — graph routing (mocked agents)
# ---------------------------------------------------------------------------

class TestGraphRouting:
    def test_parts_query_flows_through_identification(self, mocker):
        """Parts query should visit: supervisor → part_identifier → serial_resolver|escalation"""
        visited = []

        def make_mock_agent(name, output):
            def mock_run(state):
                visited.append(name)
                return output
            return mock_run

        mocker.patch("src.agents.supervisor.run", make_mock_agent("supervisor", {
            "query_type": "parts",
            "part_description": "bracket",
            "shipment_context": {},
            "next": "part_identifier",
            "messages": [],
        }))
        mocker.patch("src.agents.part_identifier.run", make_mock_agent("part_identifier", {
            "identified_part": None,
            "identification_confidence": 0.3,
            "identification_source": "catalog_match",
            "messages": [],
        }))
        mocker.patch("src.agents.escalation.run", make_mock_agent("escalation", {
            "escalated": True,
            "escalation_reason": "low confidence",
            "investigation_package": {},
            "messages": [],
        }))

        from src.graph import compile_graph
        graph = compile_graph()
        state = initial_state("mystery bracket")
        graph.invoke(state)

        assert "supervisor" in visited
        assert "part_identifier" in visited
        assert "escalation" in visited

    def test_supply_chain_query_skips_identification(self, mocker):
        """Supply chain query should NOT visit part_identifier."""
        visited = []

        def make_mock_agent(name, output):
            def mock_run(state):
                visited.append(name)
                return output
            return mock_run

        mocker.patch("src.agents.supervisor.run", make_mock_agent("supervisor", {
            "query_type": "supply_chain",
            "part_description": "",
            "shipment_context": {},
            "next": "supply_chain",
            "messages": [],
        }))
        mocker.patch("src.agents.supply_chain.run", make_mock_agent("supply_chain", {
            "supply_chain_answer": "Defect analysis...",
            "messages": [],
        }))
        mocker.patch("src.agents.synthesizer.run", make_mock_agent("synthesizer", {
            "final_answer": "Summary...",
            "messages": [],
        }))

        from src.graph import compile_graph
        graph = compile_graph()
        state = initial_state("supplier defect rates?")
        graph.invoke(state)

        assert "supervisor" in visited
        assert "supply_chain" in visited
        assert "part_identifier" not in visited
