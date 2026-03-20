import pandas as pd
from difflib import get_close_matches

FINNISH_BENCHMARKS = {
    "Residential apartment block": {"target": 400, "reference_years": 50},
    "Detached house": {"target": 450, "reference_years": 50},
    "Office building": {"target": 450, "reference_years": 50},
    "School or educational": {"target": 360, "reference_years": 50},
    "Commercial retail": {"target": 500, "reference_years": 50},
    "Industrial warehouse": {"target": 550, "reference_years": 50},
    "Hospital or healthcare": {"target": 520, "reference_years": 50},
}

def load_carbon_db(db_path="data/carbon_db.csv"):
    return pd.read_csv(db_path)

def match_material(material_name, db):
    names = db["material_name"].tolist()
    matches = get_close_matches(
        material_name.lower(),
        [n.lower() for n in names],
        n=1,
        cutoff=0.4
    )
    if matches:
        matched_name = names[[n.lower() for n in names].index(matches[0])]
        return db[db["material_name"] == matched_name].iloc[0]
    return None

def calculate_carbon(ifc_df, db_path="data/carbon_db.csv"):
    db = load_carbon_db(db_path)
    results = []

    for _, row in ifc_df.iterrows():
        match = match_material(str(row["material"]), db)

        if match is not None:
            mass = row["volume_m3"] * match["density_kg_m3"]
            carbon = mass * match["ec_kg_co2e_per_kg"]
            results.append({
                **row.to_dict(),
                "matched_material": match["material_name"],
                "density_kg_m3": match["density_kg_m3"],
                "mass_kg": round(mass, 2),
                "ec_factor": match["ec_kg_co2e_per_kg"],
                "carbon_kg_co2e": round(carbon, 2),
                "source": match["source"],
                "stage": match["stage"],
                "match_status": "matched"
            })
        else:
            results.append({
                **row.to_dict(),
                "matched_material": "Unknown",
                "density_kg_m3": 0,
                "mass_kg": 0,
                "ec_factor": 0,
                "carbon_kg_co2e": 0,
                "source": "N/A",
                "stage": "N/A",
                "match_status": "unmatched"
            })

    return pd.DataFrame(results)

def get_hotspots(carbon_df, top_n=3):
    hotspots = (
        carbon_df.groupby("matched_material")
        .agg(
            total_carbon=("carbon_kg_co2e", "sum"),
            total_mass=("mass_kg", "sum"),
            element_count=("element_id", "count")
        )
        .reset_index()
        .sort_values("total_carbon", ascending=False)
        .head(top_n)
    )
    hotspots["carbon_pct"] = (
        hotspots["total_carbon"] /
        carbon_df["carbon_kg_co2e"].sum() * 100
    ).round(1)
    return hotspots

def get_carbon_by_storey(carbon_df):
    return (
        carbon_df.groupby("storey")["carbon_kg_co2e"]
        .sum()
        .reset_index()
        .sort_values("carbon_kg_co2e", ascending=False)
    )

def get_carbon_by_type(carbon_df):
    return (
        carbon_df.groupby("element_type")["carbon_kg_co2e"]
        .sum()
        .reset_index()
        .sort_values("carbon_kg_co2e", ascending=False)
    )

def get_benchmark_result(total_carbon, floor_area, building_type):
    if building_type not in FINNISH_BENCHMARKS:
        return None

    benchmark = FINNISH_BENCHMARKS[building_type]
    target = benchmark["target"]
    years = benchmark["reference_years"]

    carbon_per_m2 = total_carbon / floor_area if floor_area > 0 else 0
    budget = target * floor_area
    difference = carbon_per_m2 - target
    difference_total = total_carbon - budget
    percentage = (carbon_per_m2 / target * 100) if target > 0 else 0

    if carbon_per_m2 <= target * 0.85:
        status = "green"
        label = "Well within target"
    elif carbon_per_m2 <= target:
        status = "green"
        label = "Within target"
    elif carbon_per_m2 <= target * 1.15:
        status = "amber"
        label = "Slightly over target"
    else:
        status = "red"
        label = "Over target"

    return {
        "building_type": building_type,
        "total_carbon_kg": round(total_carbon, 1),
        "total_carbon_t": round(total_carbon / 1000, 2),
        "floor_area_m2": floor_area,
        "carbon_per_m2": round(carbon_per_m2, 1),
        "target_per_m2": target,
        "budget_kg": round(budget, 1),
        "difference_per_m2": round(difference, 1),
        "difference_total_t": round(difference_total / 1000, 2),
        "percentage_of_target": round(percentage, 1),
        "reference_years": years,
        "status": status,
        "label": label,
        "standard": "Finnish Ministry of Environment 2021 / EN 15978"
    }