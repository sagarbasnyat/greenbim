import pandas as pd
import os
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
    "concrete": "Ready-mix concrete, C25/30",
    "beton": "Ready-mix concrete, C25/30",
    "betoni": "Ready-mix concrete, C25/30",
    "c20": "Ready-mix concrete, C20/25",
    "c25": "Ready-mix concrete, C25/30",
    "c30": "Ready-mix concrete, C30/37",
    "c35": "Ready-mix concrete, C35/45",
    "c40": "Ready-mix concrete, C40/50",
    "c45": "Ready-mix concrete, C45/55",
    "c50": "Ready-mix concrete, C50/60",
    "reinforced concrete": "Ready-mix concrete, C30/37",
    "teräsbetoni": "Ready-mix concrete, C30/37",
    "stahlbeton": "Ready-mix concrete, C30/37",
    "precast": "Precast concrete, hollow core slab 265 mm",
    "elementti": "Precast concrete, hollow core slab 265 mm",
    "ontelolaatta": "Precast concrete, hollow core slab 265 mm",
    "hollow core": "Precast concrete, hollow core slab 265 mm",
    "sandwich": "Precast concrete, sandwich, exterior wall 150+220+80 mm",
    "aac": "Autoclaved aerated concrete block, exterior walls",
    "ytong": "Autoclaved aerated concrete block, exterior walls",
    "siporex": "Autoclaved aerated concrete block, exterior walls",
    "kevytbetoni": "Autoclaved aerated concrete block, exterior walls",
    "structural steel": "Structural steel for load bearing structure",
    "steel": "Structural steel for load bearing structure",
    "teräs": "Structural steel for load bearing structure",
    "stahl": "Structural steel for load bearing structure",
    "s235": "Structural steel for load bearing structure",
    "s275": "Structural steel for load bearing structure",
    "s355": "Structural steel for load bearing structure",
    "s420": "Structural steel for load bearing structure",
    "hea": "Structural steel for load bearing structure",
    "heb": "Structural steel for load bearing structure",
    "rhs": "Structural steel for load bearing structure",
    "chs": "Structural steel for load bearing structure",
    "steel profile": "Steel profile, 100 % scrap-based",
    "recycled steel": "Steel profile, 100 % scrap-based",
    "eaf": "Steel profile, 100 % scrap-based",
    "steel pile": "Steel pile",
    "teräspaalu": "Steel pile",
    "rebar": "Steel rebar for concrete reinforcement",
    "reinforcement": "Steel rebar for concrete reinforcement",
    "harjateräs": "Steel rebar for concrete reinforcement",
    "raudoitus": "Steel rebar for concrete reinforcement",
    "betoniteräs": "Steel rebar for concrete reinforcement",
    "b500": "Steel rebar for concrete reinforcement",
    "a500": "Steel rebar for concrete reinforcement",
    "stainless steel": "Stainless steel sheet",
    "stainless rebar": "Stainless steel rebar",
    "glulam": "GLT, Glued laminated timber",
    "glt": "GLT, Glued laminated timber",
    "liimapuu": "GLT, Glued laminated timber",
    "bsh": "GLT, Glued laminated timber",
    "gl24": "GLT, Glued laminated timber",
    "gl30": "GLT, Glued laminated timber",
    "clt": "CLT, Cross laminated timber",
    "cross laminated": "CLT, Cross laminated timber",
    "ristikkoliimapuu": "CLT, Cross laminated timber",
    "lvl beam": "LVL, laminated veneer lumber for beams, posts, and panels",
    "lvl wall": "LVL, laminated veneer lumber for wall studs",
    "lvl": "LVL, laminated veneer lumber for beams, posts, and panels",
    "kerto": "LVL, laminated veneer lumber for beams, posts, and panels",
    "viilupuu": "LVL, laminated veneer lumber for beams, posts, and panels",
    "sawn timber": "Sawn timber",
    "sahatavara": "Sawn timber",
    "timber": "Sawn timber",
    "wood": "Sawn timber",
    "puu": "Sawn timber",
    "holz": "Sawn timber",
    "softwood": "Sawn timber",
    "pine": "Sawn timber",
    "spruce": "Sawn timber",
    "kuusi": "Sawn timber",
    "mänty": "Sawn timber",
    "plywood spruce": "Plywood, spruce, uncoated",
    "plywood birch": "Plywood, birch, uncoated",
    "plywood": "Plywood, spruce, uncoated",
    "vaneri": "Plywood, spruce, uncoated",
    "osb": "OSB panel",
    "chipboard": "Chipboard",
    "mdf": "Fibreboard, medium density, mdf",
    "mineral wool 20": "Glass wool insulation, density 20 kg/m3",
    "mineral wool 60": "Glass wool insulation, density 60 kg/m3",
    "mineral wool 100": "Glass wool insulation, density 100 kg/m3",
    "glass wool": "Glass wool insulation, density 20 kg/m3",
    "lasivillalevy": "Glass wool insulation, density 20 kg/m3",
    "stone wool facade": "Stone wool insulation for facades, density 61 kg/m3",
    "stone wool roof": "Stone wool insulation for roofs, density 63 kg/m3",
    "stone wool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "kivivilla": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "rockwool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "paroc": "Stone wool insulation for facades, density 61 kg/m3",
    "isover": "Glass wool insulation, density 20 kg/m3",
    "mineral wool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "mineraalivilla": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "villa": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "eps": "EPS insulation",
    "polystyrene": "EPS insulation",
    "polystyreeni": "EPS insulation",
    "styrox": "EPS insulation",
    "thermisol": "EPS insulation",
    "xps": "XPS-insulation",
    "finnfoam": "XPS-insulation",
    "pu insulation": "PU-insulation",
    "pur": "PU-insulation",
    "pir": "Phenolic insulation, aluminum foil coating, 40-200mm",
    "cellulose board": "Cellulose insulation board",
    "cellulose loose": "Cellulose insulation, loose-fill",
    "cellulose": "Cellulose insulation board",
    "puukuitu": "Cellulose insulation board",
    "wood fibre": "Cellulose insulation board",
    "gypsum fire": "Gypsum plasterboard, hard, fire resistant",
    "gypsum wind": "Gypsum plasterboard, wind shield",
    "gypsum plasterboard": "Gypsum plasterboard, interiors",
    "gypsum board": "Gypsum plasterboard, interiors",
    "plasterboard": "Gypsum plasterboard, interiors",
    "kipsilevy": "Gypsum plasterboard, interiors",
    "gyproc": "Gypsum plasterboard, interiors",
    "knauf": "Gypsum plasterboard, interiors",
    "drywall": "Gypsum plasterboard, interiors",
    "gypsum": "Gypsum plasterboard, interiors",
    "kipsi": "Gypsum plasterboard, interiors",
    "plastering mortar": "Plastering mortar",
    "masonry mortar": "Masonry mortar",
    "general mortar": "General mortar",
    "mortar": "General mortar",
    "laasti": "General mortar",
    "screed": "Screed, cement-based",
    "tasoitus": "Screed, cement-based",
    "brick red": "Brick, red",
    "clay brick": "Brick, red",
    "brick": "Brick, red",
    "tiili": "Brick, red",
    "polttotiili": "Brick, red",
    "wienerberger": "Brick, red",
    "light brick": "Brick, light",
    "kevyttiili": "Brick, light",
    "calcium silicate": "Calcium silicate brick",
    "kalkkihiekkatiili": "Calcium silicate brick",
    "float glass": "Float glass",
    "glass": "Float glass",
    "lasi": "Float glass",
    "glazing": "Insulating glass unit",
    "insulating glass": "Insulating glass unit",
    "eristyslasi": "Insulating glass unit",
    "triple glazed": "Window, wood-aluminium, triple-glazed",
    "kolmilasi": "Window, wood-aluminium, triple-glazed",
    "coated glass": "Coated glass",
    "laminated glass": "Laminated glass",
    "toughened glass": "Thermally toughened glass",
    "aluminium profile": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "aluminium sheet": "Aluminium sheet for walls and ceilings, scrap 0%",
    "aluminium recycled": "Aluminium profile, scrap 100%",
    "aluminium": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "aluminum": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "alumiini": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "alu": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "copper sheet": "Copper sheet",
    "copper tube": "Copper tube",
    "copper": "Copper sheet",
    "kupari": "Copper sheet",
    "fibre cement": "Fibre cement board",
    "ceramic floor": "Ceramic tile for floors",
    "ceramic wall": "Ceramic tile for walls",
    "ceramic": "Ceramic tile for floors",
    "laatta": "Ceramic tile for floors",
    "tile": "Ceramic tile for floors",
    "parquet": "Flooring, parquet",
    "vinyl flooring": "Vinyl flooring",
    "bitumen membrane": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "bitumen": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "bituumi": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "bitumikermi": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "gravel": "Gravel and sand",
    "sand": "Gravel and sand",
    "hiekka": "Gravel and sand",
    "sora": "Gravel and sand",
    "crushed rock": "Crushed rock",
    "murske": "Crushed rock",
    "crushed concrete": "Crushed concrete",
    "fly ash": "Fly ash",
    "lentotuhka": "Fly ash",
    "natural stone": "Natural stone, tile for facades and floors",
    "granite": "Natural stone, tile for facades and floors",
    "graniitti": "Natural stone, tile for facades and floors",
    "luonnonkivi": "Natural stone, tile for facades and floors",
    "slate": "Natural stone, slate for facades and yard",
    "concrete pile": "Concrete pile RTB-300",
    "betonipaalut": "Concrete pile RTB-300",
    "concrete block": "Concrete block, insulated, U=0.17 W/m2K",
    "concrete paving": "Concrete paving block",
    "sandwich panel steel": "Sandwich panel, steel, mineral wool insulation",
    "color coated steel": "Color coated steel sheet profile",
    "profiled sheet": "Color coated steel sheet profile",
    "geotextile": "Geotextile, PP-based",
    "geotekstiili": "Geotextile, PP-based",
    "höyrynsulku": "Water vapor barrier, PE",
    "vapour barrier": "Water vapor barrier, PE",
    "solar panel": "Solar panel, monocrystalline",
    "aurinkopaneeli": "Solar panel, monocrystalline",
    "paint": "Paint, acrylic, water-borne for interior use",
    "maali": "Paint, acrylic, water-borne for interior use",
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
_finnish_db = None


def load_carbon_db(db_path="data/carbon_db.csv"):
    global _carbon_db
    if _carbon_db is not None:
        return _carbon_db
    try:
        _carbon_db = pd.read_csv(db_path)
    except Exception:
        _carbon_db = pd.DataFrame()
    return _carbon_db


def load_finnish_db(db_path="data/finnish_materials.csv"):
    global _finnish_db
    if _finnish_db is not None:
        return _finnish_db
    try:
        _finnish_db = pd.read_csv(db_path)
    except Exception:
        _finnish_db = pd.DataFrame()
    return _finnish_db


def get_fallback_density(material_name):
    name_lower = material_name.lower()
    for keyword, density in FALLBACK_DENSITIES.items():
        if keyword in name_lower:
            return density
    return FALLBACK_DENSITIES["default"]


def match_finnish_library(material_name, finnish_db):
    if finnish_db is None or finnish_db.empty:
        return None
    name_lower = material_name.lower().strip()
    for _, row in finnish_db.iterrows():
        ifc_name = str(row.get("ifc_name", "")).lower()
        aliases = str(row.get("aliases", "")).lower()
        all_terms = ifc_name + "," + aliases
        for term in all_terms.split(","):
            term = term.strip()
            if len(term) > 2 and term in name_lower:
                return str(row.get("mapped_co2data_name", ""))
    return None


def match_csv_material(material_name, db):
    if db is None or db.empty:
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
    ifc_df,
    db_path="data/carbon_db.csv",
    finnish_db_path="data/finnish_materials.csv"
):
    carbon_db = load_carbon_db(db_path)
    finnish_db = load_finnish_db(finnish_db_path)
    results = []

    for _, row in ifc_df.iterrows():
        material_name = str(row["material"])
        volume = row["volume_m3"]

        # Step 1 — Finnish supplier library
        finnish_mapped = match_finnish_library(
            material_name, finnish_db
        )

        # Step 2 — co2data.fi live API
        if finnish_mapped:
            finnish_data = get_finnish_carbon_value(
                finnish_mapped
            )
        else:
            finnish_data = get_finnish_carbon_value(
                material_name
            )

        if finnish_data:
            density = finnish_data.get("density_kg_m3")
            if not density:
                density = get_fallback_density(material_name)
            ec_factor = finnish_data["conservative_gwp"]
            mass = volume * density
            carbon = mass * ec_factor

            results.append({
                **row.to_dict(),
                "matched_material": finnish_data[
                    "material_name"
                ],
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
            # Step 3 — CSV fallback
            csv_match = match_csv_material(
                material_name, carbon_db
            )

            if csv_match is not None:
                mass = volume * csv_match["density_kg_m3"]
                carbon = (
                    mass * csv_match["ec_kg_co2e_per_kg"]
                )

                results.append({
                    **row.to_dict(),
                    "matched_material": csv_match[
                        "material_name"
                    ],
                    "density_kg_m3": csv_match[
                        "density_kg_m3"
                    ],
                    "mass_kg": round(mass, 2),
                    "ec_factor": csv_match[
                        "ec_kg_co2e_per_kg"
                    ],
                    "carbon_kg_co2e": round(carbon, 2),
                    "source": csv_match["source"],
                    "stage": csv_match["stage"],
                    "match_status": "matched_csv",
                    "data_quality": "Generic EN 15804"
                })

            else:
                # Step 4 — No match
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