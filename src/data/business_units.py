ROUTING_RULES = {
    "brake_system": {
        "business_unit": "Safety Systems Team",
        "priority": "critical",
        "contact_person": "Sarah Chen <s.chen@company.com>",
        "slack_channel": "#safety-systems-receiving",
        "qc_required": True,
        "qc_turnaround_hours": 2,
        "storage_area": "Warehouse B, Section BRAKE",
    },
    "sensor_hardware": {
        "business_unit": "Sensor Integration Team",
        "priority": "high",
        "contact_person": "Marcus Williams <m.williams@company.com>",
        "slack_channel": "#sensor-integration-receiving",
        "qc_required": True,
        "qc_turnaround_hours": 4,
        "storage_area": "Warehouse B, Section SENSOR",
    },
    "suspension": {
        "business_unit": "Chassis Engineering",
        "priority": "high",
        "contact_person": "Priya Patel <p.patel@company.com>",
        "slack_channel": "#chassis-eng-receiving",
        "qc_required": True,
        "qc_turnaround_hours": 4,
        "storage_area": "Warehouse A, Section CHASSIS",
    },
    "powertrain": {
        "business_unit": "Powertrain Engineering",
        "priority": "high",
        "contact_person": "David Kim <d.kim@company.com>",
        "slack_channel": "#powertrain-receiving",
        "qc_required": True,
        "qc_turnaround_hours": 6,
        "storage_area": "Warehouse A, Section POWER",
    },
    "electrical": {
        "business_unit": "Electrical Systems",
        "priority": "normal",
        "contact_person": "Ana Rodriguez <a.rodriguez@company.com>",
        "slack_channel": "#electrical-receiving",
        "qc_required": False,
        "qc_turnaround_hours": None,
        "storage_area": "Warehouse C, Section ELEC",
    },
    "body_panels": {
        "business_unit": "Body Assembly",
        "priority": "normal",
        "contact_person": "Tom Harris <t.harris@company.com>",
        "slack_channel": "#body-assembly-receiving",
        "qc_required": False,
        "qc_turnaround_hours": None,
        "storage_area": "Warehouse C, Section BODY",
    },
}

DEFAULT_ROUTING = {
    "business_unit": "General Receiving",
    "priority": "normal",
    "contact_person": "Receiving Supervisor <receiving@company.com>",
    "slack_channel": "#general-receiving",
    "qc_required": True,
    "qc_turnaround_hours": 8,
    "storage_area": "Warehouse D, Section HOLD",
}


def get_routing(part_category: str) -> dict:
    return ROUTING_RULES.get(part_category, DEFAULT_ROUTING)
