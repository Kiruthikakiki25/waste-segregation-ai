import json
import os
from strands import tool

with open("data/kabadiwalas.json", "r") as f:
    DB = json.load(f)


@tool
def classify_waste(items: str) -> str:
    """
    Classify waste items into categories: plastic, paper, cardboard, metal, ewaste, glass, wet, other.
    Also flag e-waste hazards.
    Input: comma-separated list of items the user described.
    """
    keywords = {
        "ewaste": ["phone", "mobile", "laptop", "computer", "charger", "battery", "tv", "television",
                   "monitor", "keyboard", "mouse", "tablet", "ipad", "printer", "cable", "wire"],
        "plastic": ["bottle", "plastic", "container", "bag", "cover", "bucket", "pipe", "straw"],
        "paper": ["paper", "newspaper", "book", "magazine", "notebook"],
        "cardboard": ["cardboard", "box", "carton", "packaging"],
        "metal": ["metal", "iron", "steel", "aluminium", "aluminum", "tin", "can", "scrap"],
        "glass": ["glass", "bottle", "mirror", "window"],
        "wet": ["food", "vegetable", "fruit", "leftover", "organic", "leaf", "waste"]
    }

    hazard_items = ["phone", "mobile", "laptop", "battery", "charger", "tv", "monitor"]

    item_list = [i.strip().lower() for i in items.split(",")]
    results = []

    for item in item_list:
        category = "other"
        for cat, keys in keywords.items():
            if any(k in item for k in keys):
                category = cat
                break

        is_hazard = any(h in item for h in hazard_items)
        disposal = {
            "ewaste": "Do NOT throw in regular bin. Hand over to certified e-waste collector only.",
            "plastic": "Rinse and dry before giving to recycler. Remove caps separately.",
            "paper": "Keep dry. Bundle together for kabadiwala pickup.",
            "cardboard": "Flatten boxes. Keep away from moisture.",
            "metal": "Separate ferrous and non-ferrous if possible.",
            "glass": "Wrap in newspaper before handing over. Handle with care.",
            "wet": "Compost at home or use municipal wet waste bin.",
            "other": "Check with local municipal corporation for disposal."
        }

        result = {
            "item": item,
            "category": category,
            "disposal_instruction": disposal[category],
            "hazard_warning": "⚠️ E-WASTE HAZARD: Contains toxic materials. Never burn or dump." if is_hazard else None
        }
        results.append(result)

    return json.dumps(results, indent=2)


@tool
def find_recyclers(waste_types: str, pincode: str = "", city: str = "") -> str:
    """
    Find nearby recyclers based on waste type and location (pincode or city).
    Input: waste_types as comma-separated string, pincode or city name.
    """
    types = [t.strip().lower() for t in waste_types.split(",")]
    recyclers = DB["recyclers"]
    matches = []

    for r in recyclers:
        location_match = (
            pincode and r["pincode"] == pincode
        ) or (
            city and city.lower() in r["city"].lower()
        ) or (
            not pincode and not city
        )

        type_match = any(t in r["accepts"] for t in types)

        if location_match and type_match:
            matched_types = [t for t in types if t in r["accepts"]]
            matches.append({
                "name": r["name"],
                "area": r["area"],
                "city": r["city"],
                "contact": r["contact"],
                "accepts": matched_types,
                "price_per_kg": {t: r["price_per_kg"].get(t, "N/A") for t in matched_types},
                "why_matched": f"Accepts {', '.join(matched_types)} in your area"
            })

    if not matches:
        return json.dumps({"message": "No recyclers found for your area. Try a nearby city or different waste type."})

    return json.dumps(matches, indent=2)


@tool
def estimate_value(waste_type: str, weight_kg: float) -> str:
    """
    Estimate indicative value of recyclable waste.
    NOTE: These are sample rates only, not verified live market prices.
    Input: waste_type (plastic/paper/metal/ewaste/cardboard/glass), weight in kg.
    """
    rates = DB["sample_rates"]
    waste_type = waste_type.lower()

    if waste_type not in rates:
        return json.dumps({
            "error": f"No rate available for {waste_type}",
            "available_types": list(rates.keys())
        })

    rate = rates[waste_type]
    estimated_value = rate * weight_kg

    return json.dumps({
        "waste_type": waste_type,
        "weight_kg": weight_kg,
        "rate_per_kg": rate,
        "estimated_value_inr": round(estimated_value, 2),
        "disclaimer": "⚠️ Indicative rate only. Not a verified live market price."
    }, indent=2)


@tool
def get_impact_stats(session_data: str) -> str:
    """
    Calculate environmental impact based on session waste data.
    Input: JSON string with waste categories and weights.
    Example: {"plastic": 2, "paper": 1.5, "ewaste": 0.5}
    """
    try:
        data = json.loads(session_data)
    except Exception:
        return json.dumps({"error": "Invalid session data format"})

    rates = DB["sample_rates"]
    recyclable_types = ["plastic", "paper", "cardboard", "metal", "glass"]

    total_weight = sum(data.values())
    recyclable_weight = sum(v for k, v in data.items() if k in recyclable_types)
    total_value = sum(rates.get(k, 0) * v for k, v in data.items())
    landfill_diverted = recyclable_weight

    return json.dumps({
        "total_waste_kg": round(total_weight, 2),
        "recyclable_weight_kg": round(recyclable_weight, 2),
        "estimated_value_inr": round(total_value, 2),
        "landfill_diverted_kg": round(landfill_diverted, 2),
        "co2_saved_kg": round(recyclable_weight * 2.5, 2),
        "disclaimer": "Impact estimates are approximate and for awareness purposes only."
    }, indent=2)