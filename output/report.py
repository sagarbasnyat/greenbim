from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

GREEN = colors.HexColor("#1D9E75")
DARK = colors.HexColor("#2C2C2A")
LIGHT_GRAY = colors.HexColor("#F1EFE8")
AMBER = colors.HexColor("#EF9F27")
RED = colors.HexColor("#D85A30")
WHITE = colors.white


def get_grade_color(grade):
    grade_colors = {
        "A": colors.HexColor("#1D9E75"),
        "B": colors.HexColor("#639922"),
        "C": colors.HexColor("#EF9F27"),
        "D": colors.HexColor("#D85A30"),
        "E": colors.HexColor("#A32D2D"),
        "Unknown": colors.HexColor("#888780")
    }
    return grade_colors.get(grade, colors.HexColor("#888780"))


def get_status_color(status):
    if status == "green":
        return colors.HexColor("#1D9E75")
    elif status == "amber":
        return colors.HexColor("#EF9F27")
    else:
        return colors.HexColor("#D85A30")


def generate_passport(
    output_path,
    project_name,
    project_location,
    building_type,
    floor_area,
    carbon_df,
    final_df,
    benchmark_result,
    substitutions,
    ai_recommendations,
    circularity_grade,
    circularity_score
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "title",
        fontSize=22,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=4
    )
    style_h2 = ParagraphStyle(
        "h2",
        fontSize=13,
        textColor=GREEN,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6
    )
    style_body = ParagraphStyle(
        "body",
        fontSize=9,
        textColor=DARK,
        fontName="Helvetica",
        spaceAfter=4,
        leading=14
    )
    style_small = ParagraphStyle(
        "small",
        fontSize=8,
        textColor=colors.HexColor("#5F5E5A"),
        fontName="Helvetica",
        spaceAfter=2
    )

    story = []

    # Header banner
    header_data = [[
        Paragraph("GreenBIM", style_title),
    ]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN),
        ("ROUNDEDCORNERS", [8]),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Digital Building Passport — Sustainability Assessment Report",
        ParagraphStyle(
            "sub",
            fontSize=11,
            textColor=DARK,
            alignment=TA_CENTER,
            fontName="Helvetica"
        )
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}  |  "
        f"Standard: EN 15978 / Finnish Ministry of Environment 2021",
        ParagraphStyle(
            "meta",
            fontSize=8,
            textColor=colors.HexColor("#888780"),
            alignment=TA_CENTER,
            fontName="Helvetica"
        )
    ))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=GREEN
    ))
    story.append(Spacer(1, 0.3*cm))

    # Section 1 - Building Identity
    story.append(Paragraph("1. Building Identity", style_h2))
    identity_data = [
        ["Project name", project_name],
        ["Location", project_location],
        ["Building type", building_type],
        ["Gross floor area", f"{floor_area} m²"],
        ["Total elements assessed", str(len(carbon_df))],
        ["Assessment date", datetime.now().strftime(
            "%d %B %Y"
        )],
        ["IFC standard", "IFC 2x3 / IFC4"],
        ["Carbon database",
         "co2data.fi / Finnish Environment Institute Syke / EN 15804"],
        ["Assessment method",
         "EN 15978 / Finnish MoE 2021"],
    ]
    identity_table = Table(
        identity_data, colWidths=[7*cm, 10*cm]
    )
    identity_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1),
         colors.HexColor("#5F5E5A")),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3,
         colors.HexColor("#D3D1C7")),
    ]))
    story.append(identity_table)
    story.append(Spacer(1, 0.3*cm))

    # Section 2 - Sustainability Summary
    story.append(Paragraph(
        "2. Sustainability Summary", style_h2
    ))
    total_carbon = carbon_df["carbon_kg_co2e"].sum()
    total_carbon_t = round(total_carbon / 1000, 2)
    carbon_per_m2 = round(
        total_carbon / floor_area, 1
    ) if floor_area > 0 else 0
    hazardous = int(final_df["hazardous_flag"].sum())
    unmatched = int(
        (carbon_df["match_status"] == "unmatched").sum()
    )
    verified = len(
        carbon_df[
            carbon_df["match_status"] == "matched_co2data"
        ]
    )
    verified_pct = round(
        verified / len(carbon_df) * 100
    ) if len(carbon_df) > 0 else 0

    benchmark_status = "N/A"
    target = "N/A"
    if benchmark_result:
        benchmark_status = benchmark_result["label"]
        target = (
            f"{benchmark_result['target_per_m2']} kgCO2e/m²"
        )

    summary_data = [
        ["Metric", "Value", "Reference"],
        [
            "Total embodied carbon (A1-A3)",
            f"{total_carbon_t} tCO2e",
            "EN 15978"
        ],
        [
            "Carbon intensity",
            f"{carbon_per_m2} kgCO2e/m²",
            "EN 15978"
        ],
        [
            "Finnish carbon target",
            target,
            "Finnish MoE 2021"
        ],
        [
            "Benchmark status",
            benchmark_status,
            "Finnish MoE 2021"
        ],
        [
            "Overall circularity grade",
            f"{circularity_grade} ({circularity_score})",
            "EN 15978 / Level(s)"
        ],
        [
            "Finnish verified EPD data",
            f"{verified_pct}% of elements",
            "co2data.fi / Syke"
        ],
        [
            "Hazardous material flags",
            str(hazardous),
            "EU Construction Waste Directive"
        ],
        [
            "Unmatched elements",
            str(unmatched),
            "Manual review required"
        ],
    ]
    summary_table = Table(
        summary_data,
        colWidths=[7*cm, 5*cm, 5*cm]
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3,
         colors.HexColor("#D3D1C7")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*cm))

    # Section 3 - Material Inventory
    story.append(Paragraph(
        "3. Material Inventory", style_h2
    ))
    mat_summary = (
        carbon_df.groupby("matched_material")
        .agg(
            total_volume=("volume_m3", "sum"),
            total_mass=("mass_kg", "sum"),
            total_carbon=("carbon_kg_co2e", "sum"),
            element_count=("element_id", "count"),
            data_quality=("data_quality", "first")
        )
        .reset_index()
        .sort_values("total_carbon", ascending=False)
    )

    inventory_data = [
        [
            "Material", "Elements",
            "Volume m³", "Mass t",
            "Carbon tCO2e", "Data Quality"
        ]
    ]
    for _, row in mat_summary.iterrows():
        inventory_data.append([
            str(row["matched_material"]),
            str(int(row["element_count"])),
            str(round(row["total_volume"], 1)),
            str(round(row["total_mass"] / 1000, 2)),
            str(round(row["total_carbon"] / 1000, 2)),
            str(row["data_quality"])
        ])

    inventory_table = Table(
        inventory_data,
        colWidths=[5*cm, 2*cm, 2*cm, 2*cm, 2.5*cm, 3.5*cm]
    )
    inventory_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3,
         colors.HexColor("#D3D1C7")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(inventory_table)
    story.append(Spacer(1, 0.3*cm))

    # Section 4 - Circularity
    story.append(Paragraph(
        "4. Circularity Assessment", style_h2
    ))
    circ_data = (
        final_df[final_df["circularity_score"].notna()]
        .groupby("matched_material")
        .agg(
            avg_score=("circularity_score", "mean"),
            grade=("circularity_grade", "first"),
            pathway=("end_of_life_pathway", "first")
        )
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )

    circ_table_data = [
        ["Material", "Score", "Grade", "End of Life Pathway"]
    ]
    for _, row in circ_data.iterrows():
        circ_table_data.append([
            str(row["matched_material"]),
            str(round(row["avg_score"], 2)),
            str(row["grade"]),
            str(row["pathway"])
        ])

    circ_table = Table(
        circ_table_data,
        colWidths=[5.5*cm, 2*cm, 2*cm, 7.5*cm]
    )
    circ_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3,
         colors.HexColor("#D3D1C7")),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
    ]))
    story.append(circ_table)
    story.append(Spacer(1, 0.3*cm))

    # Section 5 - AI Recommendations
    story.append(Paragraph(
        "5. AI Sustainability Recommendations", style_h2
    ))
    story.append(Paragraph(
        "The following recommendations are generated by AI "
        "based on the specific assessment data of this "
        "building and aligned with Finnish and EU "
        "sustainability standards.",
        style_small
    ))
    story.append(Spacer(1, 0.2*cm))
    if ai_recommendations:
        for line in ai_recommendations.split("\n"):
            if line.strip():
                if line.startswith("RECOMMENDATION"):
                    story.append(Paragraph(
                        line,
                        ParagraphStyle(
                            "rec_title",
                            fontSize=9,
                            textColor=GREEN,
                            fontName="Helvetica-Bold",
                            spaceBefore=8,
                            spaceAfter=2
                        )
                    ))
                else:
                    story.append(
                        Paragraph(line, style_body)
                    )

    story.append(Spacer(1, 0.3*cm))

    # Section 6 - Material Substitutions
    story.append(Paragraph(
        "6. Material Substitution Suggestions", style_h2
    ))
    if substitutions:
        for s in substitutions:
            sub_data = [
                [
                    f"#{s['rank']} — "
                    f"{s['current_material']} → "
                    f"{s['alternative_material']}"
                ],
                [
                    f"Carbon saving: "
                    f"{s['carbon_saving_t']} tCO2e "
                    f"({s['carbon_saving_pct']}%) | "
                    f"Standard: {s['standard']}"
                ],
                [s["reason"]]
            ]
            sub_table = Table(
                sub_data, colWidths=[17*cm]
            )
            sub_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                 LIGHT_GRAY),
                ("FONTNAME", (0, 0), (-1, 0),
                 "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1),
                 "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3,
                 colors.HexColor("#D3D1C7")),
            ]))
            story.append(sub_table)
            story.append(Spacer(1, 0.15*cm))
    else:
        story.append(Paragraph(
            "No substitution suggestions available.",
            style_body
        ))

    # Section 7 - Data Quality
    story.append(Paragraph(
        "7. Data Quality Summary", style_h2
    ))
    verified_count = len(
        carbon_df[
            carbon_df["match_status"] == "matched_co2data"
        ]
    )
    generic_count = len(
        carbon_df[
            carbon_df["match_status"] == "matched_csv"
        ]
    )
    unmatched_count = len(
        carbon_df[carbon_df["match_status"] == "unmatched"]
    )
    total_count = len(carbon_df)

    quality_data = [
        ["Data Source", "Elements", "Percentage"],
        [
            "Finnish verified EPD (co2data.fi / Syke)",
            str(verified_count),
            f"{round(verified_count/total_count*100)}%"
            if total_count > 0 else "0%"
        ],
        [
            "Generic EN 15804 (CSV fallback)",
            str(generic_count),
            f"{round(generic_count/total_count*100)}%"
            if total_count > 0 else "0%"
        ],
        [
            "No match (manual review needed)",
            str(unmatched_count),
            f"{round(unmatched_count/total_count*100)}%"
            if total_count > 0 else "0%"
        ],
    ]
    quality_table = Table(
        quality_data,
        colWidths=[10*cm, 3.5*cm, 3.5*cm]
    )
    quality_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3,
         colors.HexColor("#D3D1C7")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(quality_table)
    story.append(Spacer(1, 0.3*cm))

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=GREEN
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "GreenBIM — Sustainable Building Intelligence Platform  |  "
        "Assessment based on EN 15978 and Finnish Ministry of "
        "Environment Carbon Assessment Method 2021  |  "
        "Carbon data source: co2data.fi / "
        "Finnish Environment Institute Syke / EN 15804",
        ParagraphStyle(
            "footer",
            fontSize=7,
            textColor=colors.HexColor("#888780"),
            alignment=TA_CENTER,
            fontName="Helvetica"
        )
    ))

    doc.build(story)
    return output_path