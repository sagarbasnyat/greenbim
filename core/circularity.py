import pandas as pd
from difflib import get_close_matches

def load_circularity_db(db_path="data/circularity_db.csv"):
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

def grade(score):
    if score >= 0.80:
        return "A"
    elif score >= 0.65:
        return "B"
    elif score >= 0.50:
        return "C"
    elif score >= 0.35:
        return "D"
    else:
        return "E"

def grade_color(grade_letter):
    colors = {
        "A": "#1D9E75",
        "B": "#639922",
        "C": "#EF9F27",
        "D": "#D85A30",
        "E": "#A32D2D",
        "Unknown": "#888780"
    }
    return colors.get(grade_letter, "#888780")

def calculate_circularity(carbon_df, db_path="data/circularity_db.csv"):
    db = load_circularity_db(db_path)
    results = []

    for _, row in carbon_df.iterrows():
        match = match_material(str(row["material"]), db)

        if match is not None:
            score = round(
                0.40 * float(match["recyclability"]) +
                0.30 * float(match["disassembly"]) +
                0.20 * float(match["recycled_content"]) +
                0.10 * float(1 - match["hazardous"]),
                3
            )
            grade_letter = grade(score)
            results.append({
                **row.to_dict(),
                "circularity_score": score,
                "circularity_grade": grade_letter,
                "grade_color": grade_color(grade_letter),
                "recyclability": float(match["recyclability"]),
                "recycled_content": float(match["recycled_content"]),
                "disassembly": float(match["disassembly"]),
                "hazardous_flag": bool(match["hazardous"]),
                "end_of_life_pathway": match["end_of_life_pathway"],
                "circularity_notes": match["notes"]
            })
        else:
            results.append({
                **row.to_dict(),
                "circularity_score": None,
                "circularity_grade": "Unknown",
                "grade_color": "#888780",
                "recyclability": None,
                "recycled_content": None,
                "disassembly": None,
                "hazardous_flag": False,
                "end_of_life_pathway": "Unknown",
                "circularity_notes": "Material not found in database"
            })

    return pd.DataFrame(results)

def get_building_circularity_grade(final_df):
    scored = final_df[final_df["circularity_score"].notna()]
    if scored.empty:
        return "Unknown", 0.0
    avg_score = scored["circularity_score"].mean()
    return grade(avg_score), round(avg_score, 3)

def get_circularity_by_material(final_df):
    scored = final_df[final_df["circularity_score"].notna()]
    return (
        scored.groupby("matched_material")
        .agg(
            avg_score=("circularity_score", "mean"),
            avg_recyclability=("recyclability", "mean"),
            avg_recycled_content=("recycled_content", "mean"),
            avg_disassembly=("disassembly", "mean"),
            element_count=("element_id", "count")
        )
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )

def get_hazardous_elements(final_df):
    return final_df[final_df["hazardous_flag"] == True]

def get_low_circularity_flags(final_df, threshold=0.40):
    scored = final_df[final_df["circularity_score"].notna()]
    return scored[scored["circularity_score"] < threshold].sort_values(
        "circularity_score"
    )