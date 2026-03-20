import json
import os
from groq import Groq
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
            f"{s['alternative_material']} saving "
            f"{s['carbon_saving_t']} tCO2e "
            f"({s['carbon_saving_pct']}%)"
        )

    benchmark_text = ""
    if benchmark_result:
        benchmark_text = (
            f"FINNISH CARBON BENCHMARK:\n"
            f"Building type: {benchmark_result['building_type']}\n"
            f"Carbon intensity: {benchmark_result['carbon_per_m2']} kgCO2e/m2\n"
            f"Finnish target: {benchmark_result['target_per_m2']} kgCO2e/m2\n"
            f"Status: {benchmark_result['label']}\n"
            f"Difference: {benchmark_result['difference_per_m2']} kgCO2e/m2\n"
            f"Reference period: {benchmark_result['reference_years']} years"
        )

    summary = (
        f"GREENBIM BUILDING SUSTAINABILITY ASSESSMENT\n"
        f"============================================\n"
        f"Location context: Finland (EU)\n"
        f"Assessment standard: EN 15978 / Finnish MoE 2021\n"
        f"Carbon database: EN 15804 / Okobaudat\n\n"
        f"BUILDING DATA:\n"
        f"Total elements analysed: {total_elements}\n"
        f"Unmatched elements: {unmatched}\n"
        f"Total embodied carbon A1-A3: {total_carbon_t} tCO2e\n"
        f"Average circularity score: "
        f"{round(avg_circularity, 3) if avg_circularity else 'N/A'} / 1.0\n"
        f"Hazardous material flags: {hazardous_count}\n\n"
        f"TOP CARBON MATERIALS (kgCO2e):\n"
        f"{json.dumps(top_materials, indent=2)}\n\n"
        f"CARBON BY ELEMENT TYPE (kgCO2e):\n"
        f"{json.dumps(by_type, indent=2)}\n\n"
        f"CARBON BY BUILDING STOREY (kgCO2e):\n"
        f"{json.dumps(by_storey, indent=2)}\n\n"
        f"{benchmark_text}\n\n"
        f"MATERIAL SUBSTITUTION OPPORTUNITIES:\n"
        f"{sub_text}"
    )
    return summary


def get_ai_recommendations(
    carbon_df, final_df, substitutions, benchmark_result
):
    summary = build_building_summary(
        carbon_df, final_df, substitutions, benchmark_result
    )

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = (
        f"You are a sustainability consultant specialising in "
        f"embodied carbon and circular economy in construction. "
        f"You are working in Finland and follow EU and Finnish "
        f"building regulations including EN 15978, EN 15804, and "
        f"the Finnish Ministry of Environment carbon assessment "
        f"method 2021.\n\n"
        f"Below is a sustainability assessment of a building "
        f"extracted from its IFC model:\n\n"
        f"{summary}\n\n"
        f"Based on this specific building data, provide exactly 3 "
        f"clear, specific and actionable recommendations to reduce "
        f"embodied carbon and improve circularity. Each "
        f"recommendation must be directly based on the data "
        f"provided above.\n\n"
        f"Format your response exactly like this:\n\n"
        f"RECOMMENDATION 1: [Short title]\n"
        f"[2-3 sentences explaining what to do, why it matters "
        f"for this specific building, and the approximate carbon "
        f"impact. Reference relevant Finnish or EU standards "
        f"where appropriate.]\n\n"
        f"RECOMMENDATION 2: [Short title]\n"
        f"[2-3 sentences explaining what to do, why it matters "
        f"for this specific building, and the approximate carbon "
        f"impact. Reference relevant Finnish or EU standards "
        f"where appropriate.]\n\n"
        f"RECOMMENDATION 3: [Short title]\n"
        f"[2-3 sentences explaining what to do, why it matters "
        f"for this specific building, and the approximate carbon "
        f"impact. Reference relevant Finnish or EU standards "
        f"where appropriate.]\n\n"
        f"Be specific to the building data. "
        f"Do not give generic advice. "
        f"Always reference Finnish or EU standards."
    )

    response = client.chat.completions.create(
        model=model="llama3-groq-70b-8192-tool-use-preview",,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000,
        temperature=0.3
    )

    return response.choices[0].message.content