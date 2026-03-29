from difflib import get_close_matches

MATERIAL_CATEGORIES = {
    "CONCRETE": ["concrete", "betoni", "cement", "grout"],
    "STEEL": ["steel", "teräs", "aluminium", "metal"],
    "TIMBER": ["timber", "wood", "puu", "glulam", "clt", "lvl"],
    "MASONRY": ["brick", "tiili", "block", "harkko", "masonry", "stone", "calcium silicate", "kalkkihiekka"],
    "INSULATION": ["insulation", "wool", "villa", "eps", "xps", "pur", "foam", "eriste"],
    "GYPSUM": ["gypsum", "plasterboard", "kipsilevy"],
}

def _get_material_category(material_name):
    name_lower = material_name.lower()
    for category, keywords in MATERIAL_CATEGORIES.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return None

SUBSTITUTION_DB = {
    "Concrete (general C25/30)": {
        "alternative": "Concrete (low carbon 50% GGBS)",
        "alt_ec_factor": 0.080,
        "alt_density": 2400,
        "carbon_reduction_pct": 50,
        "reason": "Replacing 50% of cement clinker with GGBS (Ground Granulated Blast Furnace Slag) reduces embodied carbon by approximately 50%. GGBS is widely available in Finland and compliant with EN 15804.",
        "standard": "EN 15804 / Finnish Ministry of Environment 2021"
    },
    "Concrete (reinforced C30/37 1%)": {
        "alternative": "Concrete (low carbon 50% GGBS)",
        "alt_ec_factor": 0.095,
        "alt_density": 2500,
        "carbon_reduction_pct": 48,
        "reason": "Supplementary cementitious materials such as GGBS or fly ash reduce clinker content and embodied carbon significantly while maintaining structural performance to EN 1992 Eurocode 2.",
        "standard": "EN 15804 / Eurocode 2"
    },
    "Concrete (reinforced C35/45 2%)": {
        "alternative": "Concrete (low carbon 50% GGBS)",
        "alt_ec_factor": 0.100,
        "alt_density": 2600,
        "carbon_reduction_pct": 45,
        "reason": "High strength concrete with GGBS replacement maintains C35/45 performance while significantly reducing embodied carbon. Approved under Finnish building regulations.",
        "standard": "EN 15804 / RakMk"
    },
    "Steel (structural section S355)": {
        "alternative": "Steel (recycled EAF route)",
        "alt_ec_factor": 0.510,
        "alt_density": 7850,
        "carbon_reduction_pct": 67,
        "reason": "Electric Arc Furnace steel uses approximately 90% recycled scrap metal reducing embodied carbon by 67%. EAF steel meets EN 10025 structural steel standards and is widely available in Finland.",
        "standard": "EN 15804 / EN 10025"
    },
    "Steel (hot rolled section)": {
        "alternative": "Steel (recycled EAF route)",
        "alt_ec_factor": 0.510,
        "alt_density": 7850,
        "carbon_reduction_pct": 65,
        "reason": "Specifying EAF route steel for hot rolled sections reduces embodied carbon by 65% with no structural performance compromise. Compliant with EN 10025.",
        "standard": "EN 15804 / EN 10025"
    },
    "Aluminium (general primary)": {
        "alternative": "Aluminium (recycled secondary)",
        "alt_ec_factor": 0.680,
        "alt_density": 2700,
        "carbon_reduction_pct": 90,
        "reason": "Recycled aluminium requires 95% less energy than primary smelting. Secondary aluminium meets the same EN 573 standards as primary and is the preferred specification under EU Taxonomy guidelines.",
        "standard": "EN 15804 / EU Taxonomy"
    },
    "Insulation (EPS expanded)": {
        "alternative": "Insulation (wood fibre)",
        "alt_ec_factor": 0.420,
        "alt_density": 50,
        "carbon_reduction_pct": 87,
        "reason": "Wood fibre insulation is a bio-based alternative with significantly lower embodied carbon than EPS. It is vapour permeable and suitable for Finnish climate conditions. Compliant with EN 13171.",
        "standard": "EN 15804 / EN 13171"
    },
    "Polystyrene (XPS)": {
        "alternative": "Insulation (cellulose)",
        "alt_ec_factor": 0.250,
        "alt_density": 50,
        "carbon_reduction_pct": 93,
        "reason": "Cellulose insulation made from recycled paper has very low embodied carbon and high recycled content. Suitable for Finnish building conditions and compliant with EN 15101.",
        "standard": "EN 15804 / EN 15101"
    },
    "Brick (clay fired)": {
        "alternative": "Calcium silicate block (low carbon)",
        "alt_ec_factor": 0.130,
        "alt_density": 1800,
        "carbon_reduction_pct": 40,
        "reason": "Calcium silicate blocks have lower embodied carbon than clay-fired brick and provide equivalent load-bearing and acoustic performance. Widely used in Finnish construction and compliant with EN 771-2.",
        "standard": "EN 15804 / EN 771-2"
    },
    "Gypsum board (standard)": {
        "alternative": "Gypsum board (recycled)",
        "alt_ec_factor": 0.210,
        "alt_density": 950,
        "carbon_reduction_pct": 45,
        "reason": "Recycled content gypsum board uses post-industrial and post-consumer gypsum waste reducing embodied carbon by 45%. Recycling infrastructure exists in Finland and complies with EN 15283.",
        "standard": "EN 15804 / EN 15283"
    },
}

def get_substitution_suggestions(carbon_df, top_n=3):
    material_carbon = (
        carbon_df.groupby("matched_material")
        .agg(
            total_carbon=("carbon_kg_co2e", "sum"),
            total_mass=("mass_kg", "sum"),
            ec_factor=("ec_factor", "mean"),
            element_count=("element_id", "count")
        )
        .reset_index()
        .sort_values("total_carbon", ascending=False)
    )

    suggestions = []
    db_keys = list(SUBSTITUTION_DB.keys())

    for _, row in material_carbon.iterrows():
        if len(suggestions) >= top_n:
            break

        material_name = row["matched_material"]
        if material_name == "Unknown":
            continue

        matches = get_close_matches(
            material_name.lower(),
            [k.lower() for k in db_keys],
            n=1,
            cutoff=0.4
        )

        if matches:
            original_key = db_keys[
                [k.lower() for k in db_keys].index(matches[0])
            ]
            sub = SUBSTITUTION_DB[original_key]

            current_category = _get_material_category(material_name)
            alternative_category = _get_material_category(sub["alternative"])
            if current_category != alternative_category or current_category is None:
                continue

            current_carbon = row["total_carbon"]
            alt_carbon = row["total_mass"] * sub["alt_ec_factor"]
            saving = current_carbon - alt_carbon
            saving_pct = (
                saving / current_carbon * 100
            ) if current_carbon > 0 else 0

            if saving_pct > 80:
                continue

            suggestions.append({
                "rank": len(suggestions) + 1,
                "current_material": material_name,
                "current_carbon_kg": round(current_carbon, 1),
                "current_carbon_t": round(current_carbon / 1000, 2),
                "alternative_material": sub["alternative"],
                "alternative_carbon_kg": round(alt_carbon, 1),
                "alternative_carbon_t": round(alt_carbon / 1000, 2),
                "carbon_saving_kg": round(saving, 1),
                "carbon_saving_t": round(saving / 1000, 2),
                "carbon_saving_pct": round(saving_pct, 1),
                "reason": sub["reason"],
                "standard": sub["standard"],
                "element_count": int(row["element_count"])
            })

    return suggestions