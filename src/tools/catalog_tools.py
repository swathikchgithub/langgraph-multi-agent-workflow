import json
from src.data.parts_catalog import search_catalog_fuzzy, PARTS_CATALOG
from src.data.purchase_orders import PURCHASE_ORDERS, SUPPLIER_METRICS, FINANCE_DATA
from src.data.business_units import get_routing


def search_catalog(description: str, category: str = None) -> str:
    """Search the parts catalog by description. Returns top matches with similarity scores."""
    results = search_catalog_fuzzy(description, category)
    if not results:
        return json.dumps({"matches": [], "message": "No catalog matches found."})
    return json.dumps({"matches": results})


def lookup_po(po_number: str) -> str:
    """Look up a purchase order by number. Returns line items with part numbers and serial ranges."""
    po = PURCHASE_ORDERS.get(po_number.upper().strip())
    if not po:
        return json.dumps({"found": False, "message": f"PO {po_number} not found."})
    return json.dumps({"found": True, "po": po})


def lookup_by_supplier(supplier_name: str, days_back: int = 30) -> str:
    """Get recent POs and shipments from a supplier by name."""
    name_lower = supplier_name.lower()
    matching_pos = [
        po for po in PURCHASE_ORDERS.values()
        if name_lower in po["supplier_name"].lower()
    ]
    if not matching_pos:
        return json.dumps({"found": False, "message": f"No POs found for supplier: {supplier_name}"})
    return json.dumps({"found": True, "purchase_orders": matching_pos})


def get_business_unit_info(part_category: str) -> str:
    """Get business unit assignment and routing rules for a part category."""
    routing = get_routing(part_category)
    return json.dumps(routing)


def get_defect_rates(supplier_name: str = None) -> str:
    """Get defect rates and performance metrics by supplier."""
    if supplier_name:
        name_lower = supplier_name.lower()
        matches = {
            sid: metrics for sid, metrics in SUPPLIER_METRICS.items()
            if name_lower in metrics["name"].lower()
        }
        if not matches:
            return json.dumps({"found": False, "message": f"Supplier '{supplier_name}' not found."})
        return json.dumps({"found": True, "suppliers": matches})

    # Return all suppliers sorted by defect rate
    sorted_suppliers = sorted(
        SUPPLIER_METRICS.items(),
        key=lambda x: x[1]["defect_rate_30d"],
        reverse=True
    )
    return json.dumps({
        "suppliers": [
            {
                "supplier_id": sid,
                "name": m["name"],
                "defect_rate_30d": m["defect_rate_30d"],
                "defect_rate_90d": m["defect_rate_90d"],
                "on_time_delivery_rate": m["on_time_delivery_rate"],
                "avg_lead_time_days": m["avg_lead_time_days"],
            }
            for sid, m in sorted_suppliers
        ]
    })


def get_cost_variance(category: str = None) -> str:
    """Get budget vs actual cost variance by part category."""
    variance_data = FINANCE_DATA["cost_variance"]
    if category:
        if category not in variance_data:
            return json.dumps({"found": False, "message": f"No data for category: {category}"})
        return json.dumps({"found": True, "category": category, "data": variance_data[category]})
    return json.dumps({"found": True, "all_categories": variance_data})


def get_unreconciled_items() -> str:
    """Get open unreconciled finance items."""
    return json.dumps({"items": FINANCE_DATA["unreconciled_items"]})


# Tool definitions for Claude tool_use
CATALOG_TOOLS = [
    {
        "name": "search_catalog",
        "description": "Search the parts catalog by description or keywords. Returns top matching parts with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Part description or keywords"},
                "category": {"type": "string", "description": "Optional: filter by category (sensor_hardware, brake_system, suspension, etc.)"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "lookup_po",
        "description": "Look up a purchase order by PO number. Returns line items with part numbers and serial number ranges.",
        "input_schema": {
            "type": "object",
            "properties": {
                "po_number": {"type": "string", "description": "Purchase order number (e.g. PO-2024-0445)"},
            },
            "required": ["po_number"],
        },
    },
    {
        "name": "lookup_by_supplier",
        "description": "Get recent purchase orders from a supplier by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string", "description": "Supplier name (partial match supported)"},
            },
            "required": ["supplier_name"],
        },
    },
]

SUPPLY_CHAIN_TOOLS = [
    {
        "name": "get_defect_rates",
        "description": "Get defect rates and performance metrics for suppliers. Omit supplier_name to get all suppliers ranked by defect rate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string", "description": "Optional: specific supplier name"},
            },
        },
    },
    {
        "name": "lookup_by_supplier",
        "description": "Get purchase orders and shipment history for a supplier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string", "description": "Supplier name"},
            },
            "required": ["supplier_name"],
        },
    },
]

FINANCE_TOOLS = [
    {
        "name": "get_cost_variance",
        "description": "Get budget vs actual cost variance by part category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional: specific part category"},
            },
        },
    },
    {
        "name": "get_unreconciled_items",
        "description": "Get open unreconciled finance items that need attention.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_defect_rates",
        "description": "Get supplier metrics including spend vs budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string"},
            },
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    dispatch = {
        "search_catalog": lambda: search_catalog(**tool_input),
        "lookup_po": lambda: lookup_po(**tool_input),
        "lookup_by_supplier": lambda: lookup_by_supplier(**tool_input),
        "get_business_unit_info": lambda: get_business_unit_info(**tool_input),
        "get_defect_rates": lambda: get_defect_rates(**tool_input),
        "get_cost_variance": lambda: get_cost_variance(**tool_input),
        "get_unreconciled_items": lambda: get_unreconciled_items(),
    }
    fn = dispatch.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    return fn()
