PARTS_CATALOG = [
    {
        "part_number": "FSB-2024-L",
        "name": "Front Sensor Mounting Bracket",
        "category": "sensor_hardware",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-001",
        "supplier_name": "Acme Forgings",
        "dimensions": {"length_cm": 30, "weight_kg": 0.8},
        "serial_prefix": "SN-FSB",
        "safety_critical": True,
        "storage_requirements": "Dry, <25°C, Bin S-14",
        "keywords": ["bracket", "sensor", "mounting", "front", "metal", "30cm"],
    },
    {
        "part_number": "BCA-2024-F",
        "name": "Front Brake Caliper Assembly",
        "category": "brake_system",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-002",
        "supplier_name": "SafeBrake Systems",
        "dimensions": {"length_cm": 20, "weight_kg": 2.1},
        "serial_prefix": "SN-BCA",
        "safety_critical": True,
        "storage_requirements": "Climate controlled, Bin B-02",
        "keywords": ["brake", "caliper", "front", "assembly", "braking"],
    },
    {
        "part_number": "LDR-2024-A",
        "name": "LiDAR Unit — Roof Mount",
        "category": "sensor_hardware",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-003",
        "supplier_name": "SensorTech Inc",
        "dimensions": {"length_cm": 15, "weight_kg": 1.2},
        "serial_prefix": "SN-LDR",
        "safety_critical": True,
        "storage_requirements": "ESD-safe packaging, Bin S-01",
        "keywords": ["lidar", "sensor", "roof", "unit", "scanner", "laser"],
    },
    {
        "part_number": "SUS-2024-FL",
        "name": "Front Left Suspension Arm",
        "category": "suspension",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-001",
        "supplier_name": "Acme Forgings",
        "dimensions": {"length_cm": 45, "weight_kg": 3.5},
        "serial_prefix": "SN-SUS",
        "safety_critical": True,
        "storage_requirements": "Dry storage, Bin C-07",
        "keywords": ["suspension", "arm", "front", "left", "control arm", "chassis"],
    },
    {
        "part_number": "CAM-2024-R",
        "name": "Rear Camera Module",
        "category": "sensor_hardware",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-003",
        "supplier_name": "SensorTech Inc",
        "dimensions": {"length_cm": 8, "weight_kg": 0.3},
        "serial_prefix": "SN-CAM",
        "safety_critical": True,
        "storage_requirements": "ESD-safe packaging, Bin S-05",
        "keywords": ["camera", "rear", "module", "vision", "imaging"],
    },
    {
        "part_number": "EBK-2024-A",
        "name": "Electronic Brake Controller",
        "category": "brake_system",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-002",
        "supplier_name": "SafeBrake Systems",
        "dimensions": {"length_cm": 12, "weight_kg": 0.6},
        "serial_prefix": "SN-EBK",
        "safety_critical": True,
        "storage_requirements": "Climate controlled, ESD-safe, Bin B-10",
        "keywords": ["brake", "controller", "electronic", "ecu", "control unit"],
    },
    {
        "part_number": "HRN-2024-M",
        "name": "Main Wiring Harness",
        "category": "electrical",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-004",
        "supplier_name": "ElectroParts Co",
        "dimensions": {"length_cm": 200, "weight_kg": 4.2},
        "serial_prefix": "SN-HRN",
        "safety_critical": False,
        "storage_requirements": "Dry, coiled, Bin E-03",
        "keywords": ["harness", "wiring", "cable", "electrical", "loom", "wire"],
    },
    {
        "part_number": "BPL-2024-D",
        "name": "Door Body Panel — Driver Side",
        "category": "body_panels",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-005",
        "supplier_name": "AutoBody Parts Ltd",
        "dimensions": {"length_cm": 90, "weight_kg": 8.5},
        "serial_prefix": "SN-BPL",
        "safety_critical": False,
        "storage_requirements": "Vertical rack, protected surface, Bin P-12",
        "keywords": ["door", "panel", "body", "driver", "side", "sheet metal"],
    },
    {
        "part_number": "MTR-2024-R",
        "name": "Rear Drive Motor",
        "category": "powertrain",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-006",
        "supplier_name": "PowerDrive Systems",
        "dimensions": {"length_cm": 40, "weight_kg": 18.0},
        "serial_prefix": "SN-MTR",
        "safety_critical": True,
        "storage_requirements": "Dry, horizontal, Bin M-01",
        "keywords": ["motor", "drive", "rear", "electric", "powertrain", "traction"],
    },
    {
        "part_number": "BAT-2024-P",
        "name": "Battery Pack Module",
        "category": "powertrain",
        "vehicle_model": "ZX1",
        "supplier_id": "SUP-006",
        "supplier_name": "PowerDrive Systems",
        "dimensions": {"length_cm": 60, "weight_kg": 35.0},
        "serial_prefix": "SN-BAT",
        "safety_critical": True,
        "storage_requirements": "Climate controlled 15-25°C, fire-rated storage, Bin M-05",
        "keywords": ["battery", "pack", "module", "energy", "cell", "power"],
    },
]


def search_catalog_fuzzy(description: str, category: str = None) -> list[dict]:
    description_lower = description.lower()
    results = []

    for part in PARTS_CATALOG:
        if category and part["category"] != category:
            continue

        score = 0.0
        keywords_matched = sum(1 for kw in part["keywords"] if kw in description_lower)
        name_words_matched = sum(
            1 for word in part["name"].lower().split() if word in description_lower
        )

        if part["part_number"].lower() in description_lower:
            score = 0.95
        elif keywords_matched >= 3:
            score = 0.85
        elif keywords_matched == 2 or name_words_matched >= 2:
            score = 0.75
        elif keywords_matched == 1 or name_words_matched == 1:
            score = 0.60

        if score > 0:
            results.append({**part, "match_score": score})

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:5]
