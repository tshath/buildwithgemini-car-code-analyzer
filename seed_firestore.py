from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-3ff306ba56bc"

def seed_data():
    db = firestore.Client(project=PROJECT_ID)
    
    # 1. Seed OBD2 Diagnostic Codes Collection: "obd2_codes"
    obd2_codes = [
        {
            "code": "P0300",
            "title": "Random/Multiple Cylinder Misfire Detected",
            "system": "Ignition & Fuel System",
            "severity": "High",
            "symptoms": ["Check Engine light blinking", "Engine hesitation/jerking", "Rough idling", "Poor acceleration"],
            "possible_causes": ["Faulty spark plugs or ignition coils", "Clogged fuel injectors", "Vacuum leak", "Low fuel pressure"],
            "recommended_fixes": [
                "Inspect and replace worn spark plugs and ignition coils",
                "Check fuel trim values and test fuel injectors",
                "Perform smoke test to locate intake vacuum leaks"
            ],
            "estimated_diy_cost": "$50 - $180",
            "estimated_shop_cost": "$250 - $600",
            "urgency": "Urgent (Avoid driving if light is flashing to protect catalytic converter)"
        },
        {
            "code": "P0420",
            "title": "Catalyst System Efficiency Below Threshold (Bank 1)",
            "system": "Exhaust & Emissions",
            "severity": "Medium",
            "symptoms": ["Check Engine light illuminated", "Slight drop in fuel efficiency", "Rotten egg sulfur smell from exhaust"],
            "possible_causes": ["Degraded catalytic converter", "Faulty downstream O2 sensor", "Exhaust leak before or near converter", "Engine misfire residue"],
            "recommended_fixes": [
                "Inspect for exhaust leaks upstream of the catalytic converter",
                "Test downstream O2 sensor voltage readings",
                "Replace catalytic converter if substrate is contaminated or degraded"
            ],
            "estimated_diy_cost": "$200 - $700",
            "estimated_shop_cost": "$800 - $2,200",
            "urgency": "Moderate (Vehicle drivable, but emissions test will fail and fuel economy may suffer)"
        },
        {
            "code": "P0171",
            "title": "System Too Lean (Bank 1)",
            "system": "Fuel & Air Metering",
            "severity": "Medium-High",
            "symptoms": ["Rough idle", "Engine pinging or knocking under load", "Lack of power", "Surging throttle"],
            "possible_causes": ["Dirty or faulty Mass Air Flow (MAF) sensor", "Intake manifold vacuum leak", "Weak fuel pump or clogged fuel filter", "Faulty PCV valve"],
            "recommended_fixes": [
                "Clean the Mass Air Flow (MAF) sensor with dedicated MAF spray",
                "Inspect intake boots and vacuum hoses for cracks",
                "Verify fuel pressure meets manufacturer specs"
            ],
            "estimated_diy_cost": "$15 - $90",
            "estimated_shop_cost": "$200 - $550",
            "urgency": "High (Prolonged lean condition can cause engine knocking and valve damage)"
        },
        {
            "code": "P0128",
            "title": "Coolant Thermostat Temperature Below Regulating Temperature",
            "system": "Cooling System",
            "severity": "Low-Medium",
            "symptoms": ["Engine takes long time to warm up", "Cabin heater blows lukewarm air", "Temperature gauge stays low"],
            "possible_causes": ["Thermostat stuck in open position", "Faulty Engine Coolant Temperature (ECT) sensor", "Low coolant level"],
            "recommended_fixes": [
                "Replace engine coolant thermostat",
                "Flush and top off engine coolant with OEM spec fluid",
                "Inspect ECT sensor connector for corrosion"
            ],
            "estimated_diy_cost": "$30 - $75",
            "estimated_shop_cost": "$250 - $450",
            "urgency": "Low (Safe to drive short-term, but engine stays in open-loop mode burning excess fuel)"
        },
        {
            "code": "P0455",
            "title": "Evaporative Emission (EVAP) System Gross Leak Detected",
            "system": "EVAP / Emissions",
            "severity": "Low",
            "symptoms": ["Check Engine light illuminated", "Fuel vapor odor near fuel tank", "No noticeable drivability issues"],
            "possible_causes": ["Loose, damaged, or missing gas cap", "Stuck open purge valve or vent valve", "Cracked EVAP vapor hose"],
            "recommended_fixes": [
                "Inspect, tighten, or replace fuel filler gas cap",
                "Inspect EVAP canister vent solenoid valve",
                "Perform low-pressure EVAP smoke test"
            ],
            "estimated_diy_cost": "$15 - $60",
            "estimated_shop_cost": "$150 - $350",
            "urgency": "Low (Non-critical to drivability, but fails emissions inspection)"
        }
    ]

    for item in obd2_codes:
        code_id = item["code"]
        db.collection("obd2_codes").document(code_id).set(item)
        print(f"Seeded OBD2 code: {code_id}")

    # 2. Seed a sample vehicle in "garage_vehicles"
    sample_vehicle = {
        "vehicle_id": "veh_001",
        "owner_name": "Alex",
        "year": 2018,
        "make": "Honda",
        "model": "Civic",
        "trim": "EX 1.5L Turbo",
        "mileage": 68500,
        "skill_level": "DIY Enthusiast",
        "logged_codes": ["P0300"]
    }
    db.collection("garage_vehicles").document("veh_001").set(sample_vehicle)
    print("Seeded garage vehicle: veh_001 (2018 Honda Civic)")

if __name__ == "__main__":
    seed_data()
    print("Firestore seeding complete!")
