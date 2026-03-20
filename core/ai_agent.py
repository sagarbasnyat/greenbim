import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

def build_building_summary(carbon_df, final_df, substitutions, benchmark_result):
    total_carbon = carbon_df["carbon_kg_co2e"].sum()
    total_carbon_t = round(total_carbon / 1000, 2)
    avg_circularity = final_df["circularity_score"].mean()
    hazardous_count = int(final_df["hazardous_flag"].sum())
    total_elements = len(carbon_df)
    unmatched = int((carbon_df["match_status"] == "unmatched").sum())

    top_materials = (
        carbon_df.groupby("matched_material")["carbon_kg_co2e"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .round(1)
        .to_dict()
    )

    by_type = (
        carbon_df.groupby("element_type")["carbon_kg_co2e"]
        .sum()
        .round(1)
        .to_dict()
    )

    by_storey = (
        carbon_df.groupby("storey")["carbon_kg_co2e"]
        .sum()
        .round(1)
        .to_dict()
    )

    sub_text = ""
    for s in substitutions:
        sub_text += (
            f"\n- {s['current_material']} can be replaced with "
            f"{s['alternative_material']} saving {s['carbon_saving_t']} "
            f"tCO2e ({s['carbon_saving_pct']}%)"
        )

    benchmark_text = ""
    if benchmark_result:
        benchmark_text = f"""
FINNISH CARBON BENCHMARK (Ministry of Environment 2021 / EN 15978):
Building type: {benchmark_result['building_type']}
Carbon intensity: {benchmark_result['carbon_per_m2']} kgCO2e/m2
Finnish target: {benchmark_result['target_per_m2']} kgCO2e/m2
Status: {benchmark_result['label']}
Difference: {benchmark_result['difference_per_m2']} kgCO2e/m2
Reference period: {benchmark_result['reference_years']} years
"""

    summary = f"""
GREENBIM BUILDING SUSTAINABILITY ASSESSMENT
============================================
Location context: Finland (EU)
Assessment standard: EN 15978 / Finnish Ministry of Environment 2021
Carbon database: EN 15804 / Okobaudat

BUILDING DATA:
Total elements analysed: {total_elements}
Unmatched elements: {unmatched}
Total embodied carbon A1-A3: {total_carbon_t} tCO2e
Average circularity score: {round(avg_circularity, 3) if avg_circularity else 'N/A'} / 1.0
Hazardous material flags: {hazardous_count}

TOP CARBON MATERIALS (kgCO2e):
{json.dumps(top_materials, indent=2)}

CARBON BY ELEMENT TYPE (kgCO2e):
{json.dumps(by_type, indent=2)}

CARBON BY BUILDING STOREY (kgCO2e):
{json.dumps(by_storey, indent=2)}

{benchmark_text}

MATERIAL SUBSTITUTION OPPORTUNITIES:
{sub_text}
"""
    return summary


def get_ai_recommendations(carbon_df, final_df, substitutions, benchmark_result):
    summary = build_building_summary(
        carbon_df, final_df, substitutions, benchmark_result
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
You are a sustainability consultant specialising in embodied carbon 
and circular economy in construction. You are working in Finland 
and follow EU and Finnish building regulations including EN 15978, 
EN 15804, and the Finnish Ministry of Environment carbon assessment 
method 2021.

Below is a sustainability assessment of a building extracted from 
its IFC model:

{summary}

Based on this specific building data, provide exactly 3 clear, 
specific and actionable recommendations to reduce embodied carbon 
and improve circularity. Each recommendation must be directly 
based on the data provided above.

Format your response exactly like this:

RECOMMENDATION 1: [Short title]
[2-3 sentences explaining what to do, why it matters for this 
specific building, and the approximate carbon impact. Reference 
relevant Finnish or EU standards where appropriate.]

RECOMMENDATION 2: [Short title]
[2-3 sentences explaining what to do, why it matters for this 
specific building, and the approximate carbon impact. Reference 
relevant Finnish or EU standards where appropriate.]

RECOMMENDATION 3: [Short title]
[2-3 sentences explaining what to do, why it matters for this 
specific building, and the approximate carbon impact. Reference 
relevant Finnish or EU standards where appropriate.]

Be specific to the building data. Do not give generic advice. 
Always reference Finnish or EU standards.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text