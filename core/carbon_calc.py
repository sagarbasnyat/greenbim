import pandas as pd
from difflib import get_close_matches
from core.co2data_api import get_finnish_carbon_value

FINNISH_BENCHMARKS = {
    "Residential apartment block": {
        "target": 400, "reference_years": 50
    },
    "Detached house": {
        "target": 450, "reference_years": 50
    },
    "Office building": {
        "target": 450, "reference_years": 50
    },
    "School or educational": {
        "target": 360, "reference_years": 50
    },
    "Commercial retail": {
        "target": 500, "reference_years": 50
    },
    "Industrial warehouse": {
        "target": 550, "reference_years": 50
    },
    "Hospital or healthcare": {
        "target": 520, "reference_years": 50
    },
}

KEYWORD_MAP = {
    "concrete": "Concrete (C25/30 general)",
    "beton": "Concrete (C25/30 general)",
    "betoni": "Concrete (C25/30 general)",
    "c20": "Concrete (C20/25 general)",
    "c25": "Concrete (C25/30 general)",
    "c30": "Concrete (C30/37 general)",
    "c35": "Concrete (C35/45 general)",
    "c40": "Concrete (C40/50 high strength)",
    "c50": "Concrete (C50/60 high strength)",
    "reinforced": "Concrete (reinforced C30/37 1%)",
    "teräsbetoni": "Concrete (reinforced C30/37 1%)",
    "stahlbeton": "Concrete (reinforced C30/37 1%)",
    "precast": "Concrete (precast element standard)",
    "elementti": "Concrete (precast element standard)",
    "ontelolaatta": "Concrete (precast hollow core slab)",
    "hollow core": "Concrete (precast hollow core slab)",
    "sandwich": "Concrete (precast sandwich element)",
    "ggbs": "Concrete (low carbon 50% GGBS)",
    "aac": "Concrete (AAC autoclaved aerated)",
    "ytong": "Concrete (AAC autoclaved aerated)",
    "steel": "Steel (structural section S355)",
    "teräs": "Steel (structural section S355)",
    "s355": "Steel (structural section S355)",
    "hea": "Steel (hot rolled HEA HEB)",
    "rhs": "Steel (hollow section RHS CHS)",
    "rebar": "Steel (rebar B500B)",
    "harjateräs": "Steel (rebar B500B)",
    "b500": "Steel (rebar B500B)",
    "timber": "Timber (softwood sawn C24)",
    "wood": "Timber (softwood sawn C24)",
    "puu": "Timber (softwood sawn C24)",
    "sahatavara": "Timber (softwood sawn C24)",
    "glulam": "Timber (glulam GL30)",
    "liimapuu": "Timber (glulam GL30)",
    "gl30": "Timber (glulam GL30)",
    "clt": "Timber (CLT cross laminated)",
    "lvl": "Timber (LVL Kerto)",
    "kerto": "Timber (LVL Kerto)",
    "plywood": "Plywood (spruce)",
    "osb": "OSB board",
    "mineral wool": "Insulation (mineral wool 30kg)",
    "mineraalivilla": "Insulation (mineral wool 30kg)",
    "paroc": "Insulation (mineral wool 50kg)",
    "isover": "Insulation (mineral wool 30kg)",
    "rockwool": "Insulation (mineral wool 50kg)",
    "villa": "Insulation (mineral wool 30kg)",
    "eps": "Insulation (EPS expanded)",
    "polystyrene": "Insulation (EPS expanded)",
    "styrox": "Insulation (EPS expanded)",
    "xps": "Insulation (XPS extruded)",
    "finnfoam": "Insulation (XPS extruded)",
    "wood fibre": "Insulation (wood fibre)",
    "cellulose": "Insulation (cellulose)",
    "gypsum": "Gypsum board (standard 13mm)",
    "kipsilevy": "Gypsum board (standard 13mm)",
    "gyproc": "Gypsum board (standard 13mm)",
    "plasterboard": "Gypsum board (standard 13mm)",
    "brick": "Brick (clay fired standard)",
    "tiili": "Brick (clay fired standard)",
    "calcium silicate": "Brick (calcium silicate)",
    "glass": "Glass (float general)",
    "lasi": "Glass (float general)",
    "glazing": "Glass (double glazed unit)",
    "aluminium": "Aluminium (primary extrusion)",
    "aluminum": "Aluminium (primary extrusion)",
    "alumiini": "Aluminium (primary extrusion)",
    "copper": "Copper (general)",
    "kupari": "Copper (general)",
    "granite": "Stone (granite)",
    "graniitti": "Stone (granite)",
    "stone": "Stone (granite)",
    "kivi": "Stone (granite)",
    "ceramic": "Ceramic tiles (floor)",
    "laatta": "Ceramic tiles (floor)",
    "bitumen": "Bitumen membrane (roofing)",
    "bituumi": "Bitumen membrane (roofing)",
    "sand": "Sand (fill)",
    "hiekka": "Sand (fill)",
    "gravel": "Gravel (fill)",
    "sora": "Gravel (fill)",
    "mortar": "Mortar (general)",
    "laasti": "Mortar (general)",
    "screed": "Screed (cement based)",
}

FALLBACK_DENSITIES = {
    "concrete": 2400,
    "steel": 7850,
    "timber": 500,
    "wood": 500,
    "insulation": 30,
    "glass": 2500,
    "aluminium": 2700,
    "brick": 1700,
    "gypsum": 950,
    "stone": 2600,
    "copper": 8900,
    "default": 1000,
}

_carbon_db = None


def load_carbon_db(db_path="data/carbon_db.csv"):
    global _carbon_db
    if _carbon_db is not None:
        return _carbon_db
    try:
        _carbon_db = pd.read_csv(db_path)
    except Exception:
        _carbon_db = pd.DataFrame()
    return _carbon_db


def get_fallback_density(material_name):
    name_lower = material_name.lower()
    for keyword, density in FALLBACK_DENSITIES.items():
        if keyword in name_lower:
            return density
    return FALLBACK_DENSITIES["default"]


def match_csv_material(material_name, db):
    if db.empty:
        return None
    name_lower = material_name.lower().strip()

    for _, row in db.iterrows():
        if row["material_name"].lower() == name_lower:
            return row

    for keyword, mapped_name in KEYWORD_MAP.items():
        if keyword in name_lower:
            match = db[db["material_name"] == mapped_name]
            if not match.empty:
                return match.iloc[0]

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


def calculate_carbon(
    ifc_df, db_path="data/carbon_db.csv"
):
    carbon_db = load_carbon_db(db_path)
    results = []

    for _, row in ifc_df.iterrows():
        material_name = str(row["material"])
        volume = row["volume_m3"]

        finnish_data = get_finnish_carbon_value(material_name)

        if finnish_data:
            density = finnish_data.get("density_kg_m3")
            if not density:
                density = get_fallback_density(material_name)
            ec_factor = finnish_data["conservative_gwp"]
            mass = volume * density
            carbon = mass * ec_factor

            results.append({
                **row.to_dict(),
                "matched_material": finnish_data["material_name"],
                "density_kg_m3": density,
                "mass_kg": round(mass, 2),
                "ec_factor": ec_factor,
                "carbon_kg_co2e": round(carbon, 2),
                "source": finnish_data["source"],
                "stage": "A1-A3",
                "match_status": "matched_co2data",
                "data_quality": "Finnish verified EPD"
            })

        else:
            csv_match = match_csv_material(
                material_name, carbon_db
            )

            if csv_match is not None:
                mass = volume * csv_match["density_kg_m3"]
                carbon = mass * csv_match["ec_kg_co2e_per_kg"]

                results.append({
                    **row.to_dict(),
                    "matched_material": csv_match["material_name"],
                    "density_kg_m3": csv_match["density_kg_m3"],
                    "mass_kg": round(mass, 2),
                    "ec_factor": csv_match["ec_kg_co2e_per_kg"],
                    "carbon_kg_co2e": round(carbon, 2),
                    "source": csv_match["source"],
                    "stage": csv_match["stage"],
                    "match_status": "matched_csv",
                    "data_quality": "Generic EN 15804"
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
                    "match_status": "unmatched",
                    "data_quality": "No match"
                })

    return pd.DataFrame(results)


def get_hotspots(carbon_df, top_n=3):
    matched = carbon_df[
        carbon_df["match_status"] != "unmatched"
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


def get_benchmark_result(
    total_carbon, floor_area, building_type
):
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
        "difference_total_t": round(
            difference_total / 1000, 2
        ),
        "percentage_of_target": round(percentage, 1),
        "reference_years": years,
        "status": status,
        "label": label,
        "standard": (
            "Finnish Ministry of Environment 2021 / EN 15978"
        )
    }