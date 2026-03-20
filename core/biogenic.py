import pandas as pd

BIOGENIC_CARBON_MAP = {
    "GLT, Glued laminated timber": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in glulam timber elements",
        "source": "EN 16485 / co2data.fi"
    },
    "CLT, Cross laminated timber": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in CLT elements",
        "source": "EN 16485 / co2data.fi"
    },
    "LVL, laminated veneer lumber for beams, posts, and panels": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 530,
        "notes": "Carbon stored in LVL elements",
        "source": "EN 16485 / co2data.fi"
    },
    "LVL, laminated veneer lumber for wall studs": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 530,
        "notes": "Carbon stored in LVL wall studs",
        "source": "EN 16485 / co2data.fi"
    },
    "Sawn timber": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in sawn timber",
        "source": "EN 16485 / co2data.fi"
    },
    "Sawn timber, planed": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in planed timber",
        "source": "EN 16485 / co2data.fi"
    },
    "Plywood, spruce, uncoated": {
        "biogenic_kg_co2_per_kg": -0.850,
        "density_kg_m3": 550,
        "notes": "Carbon stored in spruce plywood",
        "source": "EN 16485 / co2data.fi"
    },
    "Plywood, spruce, coated": {
        "biogenic_kg_co2_per_kg": -0.850,
        "density_kg_m3": 550,
        "notes": "Carbon stored in coated spruce plywood",
        "source": "EN 16485 / co2data.fi"
    },
    "Plywood, birch, uncoated": {
        "biogenic_kg_co2_per_kg": -0.870,
        "density_kg_m3": 680,
        "notes": "Carbon stored in birch plywood",
        "source": "EN 16485 / co2data.fi"
    },
    "Plywood, birch, coated": {
        "biogenic_kg_co2_per_kg": -0.870,
        "density_kg_m3": 680,
        "notes": "Carbon stored in coated birch plywood",
        "source": "EN 16485 / co2data.fi"
    },
    "OSB panel": {
        "biogenic_kg_co2_per_kg": -0.880,
        "density_kg_m3": 600,
        "notes": "Carbon stored in OSB panel",
        "source": "EN 16485 / co2data.fi"
    },
    "Chipboard": {
        "biogenic_kg_co2_per_kg": -0.840,
        "density_kg_m3": 650,
        "notes": "Carbon stored in chipboard",
        "source": "EN 16485 / co2data.fi"
    },
    "Fibreboard, medium density, mdf": {
        "biogenic_kg_co2_per_kg": -0.830,
        "density_kg_m3": 750,
        "notes": "Carbon stored in MDF",
        "source": "EN 16485 / co2data.fi"
    },
    "Cellulose insulation board": {
        "biogenic_kg_co2_per_kg": -1.400,
        "density_kg_m3": 50,
        "notes": "High biogenic carbon in cellulose insulation",
        "source": "EN 16485 / co2data.fi"
    },
    "Cellulose insulation, loose-fill": {
        "biogenic_kg_co2_per_kg": -1.400,
        "density_kg_m3": 50,
        "notes": "High biogenic carbon in loose cellulose",
        "source": "EN 16485 / co2data.fi"
    },
    "Solid log wall structure": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in log wall structure",
        "source": "EN 16485 / co2data.fi"
    },
    "Laminated log wall structure": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 500,
        "notes": "Carbon stored in laminated log wall",
        "source": "EN 16485 / co2data.fi"
    },
    "Flooring, parquet": {
        "biogenic_kg_co2_per_kg": -0.900,
        "density_kg_m3": 700,
        "notes": "Carbon stored in parquet flooring",
        "source": "EN 16485 / co2data.fi"
    },
    "GLVL, multiple glued laminated veneer lumber": {
        "biogenic_kg_co2_per_kg": -0.920,
        "density_kg_m3": 530,
        "notes": "Carbon stored in GLVL elements",
        "source": "EN 16485 / co2data.fi"
    },
}

TIMBER_KEYWORDS = [
    "timber", "wood", "glulam", "clt", "lvl", "kerto",
    "plywood", "osb", "chipboard", "mdf", "fibreboard",
    "cellulose", "log", "parquet", "sahatavara", "puu",
    "liimapuu", "ristikkoliimapuu", "viilupuu", "vaneri",
    "glt", "glvl", "sawn", "softwood", "hardwood"
]


def is_timber_material(material_name):
    name_lower = material_name.lower()
    return any(kw in name_lower for kw in TIMBER_KEYWORDS)


def get_biogenic_factor(matched_material_name):
    if matched_material_name in BIOGENIC_CARBON_MAP:
        return BIOGENIC_CARBON_MAP[matched_material_name]
    name_lower = matched_material_name.lower()
    for kw in TIMBER_KEYWORDS:
        if kw in name_lower:
            return {
                "biogenic_kg_co2_per_kg": -0.920,
                "density_kg_m3": 500,
                "notes": "Estimated biogenic carbon for timber",
                "source": "EN 16485 estimate"
            }
    return None


def calculate_biogenic_carbon(carbon_df):
    results = []
    for _, row in carbon_df.iterrows():
        matched = str(row.get("matched_material", ""))
        volume = row.get("volume_m3", 0)
        mass = row.get("mass_kg", 0)

        biogenic_data = get_biogenic_factor(matched)

        if biogenic_data and volume > 0:
            if mass == 0:
                mass = volume * biogenic_data["density_kg_m3"]
            biogenic_carbon = round(
                mass * biogenic_data["biogenic_kg_co2_per_kg"],
                2
            )
            results.append({
                "element_id": row.get("element_id", ""),
                "element_type": row.get("element_type", ""),
                "storey": row.get("storey", "Unknown"),
                "material": row.get("material", ""),
                "matched_material": matched,
                "volume_m3": volume,
                "mass_kg": round(mass, 2),
                "embodied_carbon_kg": round(
                    row.get("carbon_kg_co2e", 0), 2
                ),
                "biogenic_carbon_kg": biogenic_carbon,
                "net_carbon_kg": round(
                    row.get("carbon_kg_co2e", 0) +
                    biogenic_carbon, 2
                ),
                "source": biogenic_data["source"],
                "notes": biogenic_data["notes"]
            })

    return pd.DataFrame(results)


def get_biogenic_summary(carbon_df):
    biogenic_df = calculate_biogenic_carbon(carbon_df)

    if biogenic_df.empty:
        return {
            "has_timber": False,
            "timber_elements": 0,
            "total_embodied_carbon_kg": 0,
            "total_biogenic_carbon_kg": 0,
            "total_net_carbon_kg": 0,
            "biogenic_offset_pct": 0,
            "is_carbon_negative": False,
            "biogenic_df": biogenic_df
        }

    total_embodied = carbon_df["carbon_kg_co2e"].sum()
    total_biogenic = biogenic_df["biogenic_carbon_kg"].sum()
    total_net = total_embodied + total_biogenic

    offset_pct = round(
        abs(total_biogenic) / total_embodied * 100
    ) if total_embodied > 0 else 0

    return {
        "has_timber": True,
        "timber_elements": len(biogenic_df),
        "total_embodied_carbon_kg": round(total_embodied, 2),
        "total_biogenic_carbon_kg": round(total_biogenic, 2),
        "total_net_carbon_kg": round(total_net, 2),
        "total_embodied_carbon_t": round(
            total_embodied / 1000, 3
        ),
        "total_biogenic_carbon_t": round(
            total_biogenic / 1000, 3
        ),
        "total_net_carbon_t": round(total_net / 1000, 3),
        "biogenic_offset_pct": offset_pct,
        "is_carbon_negative": total_net < 0,
        "biogenic_df": biogenic_df
    }