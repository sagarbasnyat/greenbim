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

# Smart keyword mapping — maps common IFC material keywords
# to your database material names
KEYWORD_MAP = {
    # Concrete variations
    "concrete": "Concrete (general C25/30)",
    "beton": "Concrete (general C25/30)",
    "c20": "Concrete (general C25/30)",
    "c25": "Concrete (general C25/30)",
    "c30": "Concrete (reinforced C30/37 1%)",
    "c35": "Concrete (reinforced C35/45 2%)",
    "c40": "Concrete (reinforced C35/45 2%)",
    "reinforced": "Concrete (reinforced C30/37 1%)",
    "stahlbeton": "Concrete (reinforced C30/37 1%)",
    "precast": "Concrete (precast element)",
    "fertigbeton": "Concrete (precast element)",
    "ggbs": "Concrete (low carbon 50% GGBS)",
    "low carbon concrete": "Concrete (low carbon 50% GGBS)",

    # Steel variations
    "steel": "Steel (structural section S355)",
    "stahl": "Steel (structural section S355)",
    "metal": "Steel (structural section S355)",
    "s235": "Steel (structural section S355)",
    "s275": "Steel (structural section S355)",
    "s355": "Steel (structural section S355)",
    "rebar": "Steel (rebar B500B)",
    "reinforcement": "Steel (rebar B500B)",
    "bewehrung": "Steel (rebar B500B)",
    "eaf": "Steel (recycled EAF route)",
    "recycled steel": "Steel (recycled EAF route)",

    # Timber variations
    "timber": "Timber (glulam GL30)",
    "wood": "Timber (softwood sawn)",
    "holz": "Timber (softwood sawn)",
    "glulam": "Timber (glulam GL30)",
    "brettschichtholz": "Timber (glulam GL30)",
    "bsh": "Timber (glulam GL30)",
    "clt": "Timber (CLT cross laminated)",
    "cross laminated": "Timber (CLT cross laminated)",
    "kreuzlagenholz": "Timber (CLT cross laminated)",
    "lvl": "Timber (LVL laminated veneer)",
    "softwood": "Timber (softwood sawn)",
    "nadelholz": "Timber (softwood sawn)",
    "pine": "Timber (softwood sawn)",
    "spruce": "Timber (softwood sawn)",

    # Masonry variations
    "brick": "Brick (clay fired)",
    "ziegel": "Brick (clay fired)",
    "clay": "Brick (clay fired)",
    "masonry": "Brick (clay fired)",
    "mauerwerk": "Brick (clay fired)",
    "calcium silicate": "Brick (calcium silicate)",
    "kalksandstein": "Brick (calcium silicate)",

    # Glass variations
    "glass": "Glass (float general)",
    "glas": "Glass (float general)",
    "glazing": "Glass (float general)",
    "verglasung": "Glass (float general)",
    "triple": "Glass (triple glazed unit)",
    "dreifach": "Glass (triple glazed unit)",

    # Aluminium variations
    "aluminium": "Aluminium (general primary)",
    "aluminum": "Aluminium (general primary)",
    "aluminiu": "Aluminium (general primary)",
    "alu": "Aluminium (general primary)",

    # Insulation variations
    "insulation": "Insulation (mineral wool)",
    "daemmung": "Insulation (mineral wool)",
    "mineral wool": "Insulation (mineral wool)",
    "mineralwolle": "Insulation (mineral wool)",
    "rockwool": "Insulation (mineral wool)",
    "glasswool": "Insulation (mineral wool)",
    "eps": "Insulation (EPS expanded)",
    "polystyrene": "Insulation (EPS expanded)",
    "styrofoam": "Insulation (EPS expanded)",
    "xps": "Polystyrene (XPS)",
    "wood fibre": "Insulation (wood fibre)",
    "holzfaser": "Insulation (wood fibre)",
    "cellulose": "Insulation (cellulose)",

    # Gypsum variations
    "gypsum": "Gypsum board (standard)",
    "gips": "Gypsum board (standard)",
    "plasterboard": "Gypsum board (standard)",
    "drywall": "Gypsum board (standard)",
    "plaster": "Gypsum board (standard)",

    # Stone variations
    "granite": "Stone (granite)",
    "granit": "Stone (granite)",
    "limestone": "Stone (limestone)",
    "kalkstein": "Stone (limestone)",
    "stone": "Stone (granite)",
    "stein": "Stone (granite)",

    # Other
    "ceramic": "Ceramic tiles",
    "keramik": "Ceramic tiles",
    "tile": "Ceramic tiles",
    "copper": "Copper (general)",
    "kupfer": "Copper (general)",
}


def load_carbon_db(db_path="data/carbon_db.csv"):
    return pd.read_csv(db_path)


def smart_match(material_name, db):
    if not material_name or material_name == "Unknown":
        return None

    name_lower = material_name.lower().strip()

    # Step 1 — exact match first
    for _, row in db.iterrows():
        if row["material_name"].lower() == name_lower:
            return row

    # Step 2 — keyword map match
    for keyword, mapped_name in KEYWORD_MAP.items():
        if keyword in name_lower:
            match = db[
                db["material_name"] == mapped_name
            ]
            if not match.empty:
                return match.iloc[0]

    # Step 3 — fuzzy match on full name
    names = db["material_name"].tolist()
    fuzzy = get_close_matches(
        name_lower,
        [n.lower() for n in names],
        n=1,
        cutoff=0.4
    )
    if fuzzy:
        matched = names[
            [n.lower() for n in names].index(fuzzy[0])
        ]
        return db[db["material_name"] == matched].iloc[0]

    # Step 4 — partial word match
    name_words = name_lower.split()
    for word in name_words:
        if len(word) > 3:
            for keyword, mapped_name in KEYWORD_MAP.items():
                if word in keyword or keyword in word:
                    match = db[
                        db["material_name"] == mapped_name
                    ]
                    if not match.empty:
                        return match.iloc[0]

    return None


def calculate_carbon(ifc_df, db_path="data/carbon_db.csv"):
    db = load_carbon_db(db_path)
    results = []

    for _, row in ifc_df.iterrows():
        match = smart_match(str(row["material"]), db)

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
    matched = carbon_df[
        carbon_df["match_status"] == "matched"
    ]
    if matched.empty:
        return pd.DataFrame()
    hotspots = (
        matched.groupby("matched_material")
        .agg(
            total_carbon=("carbon_kg_co2e", "sum"),
            total_mass=("mass_kg", "sum"),
            element_count=("element_id", "count")
        )
        .reset_index()
        .sort_values("total_carbon", ascending=False)
        .head(top_n)
    )
    total = carbon_df["carbon_kg_co2e"].sum()
    if total > 0:
        hotspots["carbon_pct"] = (
            hotspots["total_carbon"] / total * 100
        ).round(1)
    else:
        hotspots["carbon_pct"] = 0
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

    carbon_per_m2 = (
        total_carbon / floor_area if floor_area > 0 else 0
    )
    budget = target * floor_area
    difference = carbon_per_m2 - target
    difference_total = total_carbon - budget
    percentage = (
        carbon_per_m2 / target * 100
    ) if target > 0 else 0

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
        "standard": (
            "Finnish Ministry of Environment 2021 / EN 15978"
        )
    }