PURCHASE_ORDERS = {
    "PO-2024-0445": {
        "po_number": "PO-2024-0445",
        "supplier_id": "SUP-001",
        "supplier_name": "Acme Forgings",
        "order_date": "2024-03-10",
        "expected_delivery": "2024-03-20",
        "line_items": [
            {
                "part_number": "FSB-2024-L",
                "part_name": "Front Sensor Mounting Bracket",
                "quantity": 50,
                "batch_id": "B2024-0315",
                "serial_range": {
                    "start": "SN-FSB-0445-001",
                    "end": "SN-FSB-0445-050",
                },
            }
        ],
    },
    "PO-2024-0312": {
        "po_number": "PO-2024-0312",
        "supplier_id": "SUP-002",
        "supplier_name": "SafeBrake Systems",
        "order_date": "2024-02-28",
        "expected_delivery": "2024-03-15",
        "line_items": [
            {
                "part_number": "BCA-2024-F",
                "part_name": "Front Brake Caliper Assembly",
                "quantity": 100,
                "batch_id": "B2024-0301",
                "serial_range": {
                    "start": "SN-BCA-0312-001",
                    "end": "SN-BCA-0312-100",
                },
            },
            {
                "part_number": "EBK-2024-A",
                "part_name": "Electronic Brake Controller",
                "quantity": 25,
                "batch_id": "B2024-0302",
                "serial_range": {
                    "start": "SN-EBK-0312-001",
                    "end": "SN-EBK-0312-025",
                },
            },
        ],
    },
    "PO-2024-0501": {
        "po_number": "PO-2024-0501",
        "supplier_id": "SUP-003",
        "supplier_name": "SensorTech Inc",
        "order_date": "2024-04-01",
        "expected_delivery": "2024-04-15",
        "line_items": [
            {
                "part_number": "LDR-2024-A",
                "part_name": "LiDAR Unit — Roof Mount",
                "quantity": 20,
                "batch_id": "B2024-0410",
                "serial_range": {
                    "start": "SN-LDR-0501-001",
                    "end": "SN-LDR-0501-020",
                },
            },
            {
                "part_number": "CAM-2024-R",
                "part_name": "Rear Camera Module",
                "quantity": 40,
                "batch_id": "B2024-0411",
                "serial_range": {
                    "start": "SN-CAM-0501-001",
                    "end": "SN-CAM-0501-040",
                },
            },
        ],
    },
    "PO-2024-0398": {
        "po_number": "PO-2024-0398",
        "supplier_id": "SUP-001",
        "supplier_name": "Acme Forgings",
        "order_date": "2024-03-25",
        "expected_delivery": "2024-04-05",
        "line_items": [
            {
                "part_number": "SUS-2024-FL",
                "part_name": "Front Left Suspension Arm",
                "quantity": 30,
                "batch_id": "B2024-0330",
                "serial_range": {
                    "start": "SN-SUS-0398-001",
                    "end": "SN-SUS-0398-030",
                },
            }
        ],
    },
    "PO-2024-0610": {
        "po_number": "PO-2024-0610",
        "supplier_id": "SUP-006",
        "supplier_name": "PowerDrive Systems",
        "order_date": "2024-05-10",
        "expected_delivery": "2024-05-25",
        "line_items": [
            {
                "part_number": "MTR-2024-R",
                "part_name": "Rear Drive Motor",
                "quantity": 10,
                "batch_id": "B2024-0520",
                "serial_range": {
                    "start": "SN-MTR-0610-001",
                    "end": "SN-MTR-0610-010",
                },
            },
            {
                "part_number": "BAT-2024-P",
                "part_name": "Battery Pack Module",
                "quantity": 10,
                "batch_id": "B2024-0521",
                "serial_range": {
                    "start": "SN-BAT-0610-001",
                    "end": "SN-BAT-0610-010",
                },
            },
        ],
    },
}

SUPPLIER_METRICS = {
    "SUP-001": {
        "name": "Acme Forgings",
        "defect_rate_30d": 0.023,
        "defect_rate_90d": 0.018,
        "avg_lead_time_days": 10,
        "on_time_delivery_rate": 0.94,
        "open_pos": ["PO-2024-0445", "PO-2024-0398"],
        "ytd_spend": 1_250_000,
        "ytd_budget": 1_100_000,
    },
    "SUP-002": {
        "name": "SafeBrake Systems",
        "defect_rate_30d": 0.008,
        "defect_rate_90d": 0.006,
        "avg_lead_time_days": 14,
        "on_time_delivery_rate": 0.97,
        "open_pos": ["PO-2024-0312"],
        "ytd_spend": 890_000,
        "ytd_budget": 900_000,
    },
    "SUP-003": {
        "name": "SensorTech Inc",
        "defect_rate_30d": 0.041,
        "defect_rate_90d": 0.035,
        "avg_lead_time_days": 21,
        "on_time_delivery_rate": 0.88,
        "open_pos": ["PO-2024-0501"],
        "ytd_spend": 2_100_000,
        "ytd_budget": 1_800_000,
    },
    "SUP-006": {
        "name": "PowerDrive Systems",
        "defect_rate_30d": 0.012,
        "defect_rate_90d": 0.010,
        "avg_lead_time_days": 30,
        "on_time_delivery_rate": 0.91,
        "open_pos": ["PO-2024-0610"],
        "ytd_spend": 4_500_000,
        "ytd_budget": 4_200_000,
    },
}

FINANCE_DATA = {
    "cost_variance": {
        "brake_system": {"budget": 900_000, "actual": 890_000, "variance_pct": -1.1},
        "sensor_hardware": {"budget": 1_800_000, "actual": 2_100_000, "variance_pct": 16.7},
        "suspension": {"budget": 500_000, "actual": 520_000, "variance_pct": 4.0},
        "powertrain": {"budget": 4_200_000, "actual": 4_500_000, "variance_pct": 7.1},
        "electrical": {"budget": 300_000, "actual": 285_000, "variance_pct": -5.0},
        "body_panels": {"budget": 200_000, "actual": 195_000, "variance_pct": -2.5},
    },
    "unreconciled_items": [
        {
            "id": "UNREC-001",
            "supplier": "SensorTech Inc",
            "amount": 45_000,
            "description": "LiDAR units — invoice received, PO quantity mismatch",
            "days_open": 12,
        },
        {
            "id": "UNREC-002",
            "supplier": "Acme Forgings",
            "amount": 18_500,
            "description": "Suspension arm batch B2024-0330 — delivery confirmed, invoice pending",
            "days_open": 5,
        },
    ],
}
