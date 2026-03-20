import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import tempfile
import os
from dotenv import load_dotenv

from core.ifc_parser import parse_ifc, get_summary
from core.carbon_calc import calculate_carbon, get_hotspots, get_carbon_by_storey, get_carbon_by_type, get_benchmark_result, FINNISH_BENCHMARKS
from core.circularity import calculate_circularity, get_building_circularity_grade, get_circularity_by_material, get_low_circularity_flags
from core.substitution import get_substitution_suggestions
from core.ai_agent import get_ai_recommendations
from core.biogenic import get_biogenic_summary
from output.report import generate_passport

load_dotenv()

st.set_page_config(
    page_title="GreenBIM",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border: 0.5px solid #e0e0e0;
    }
    .section-header {
        color: #1D9E75;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .status-green {
        background: #EAF3DE;
        color: #3B6D11;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }
    .status-amber {
        background: #FAEEDA;
        color: #854F0B;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }
    .status-red {
        background: #FCEBEB;
        color: #A32D2D;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }
    .quality-badge-green {
        background: #EAF3DE;
        color: #3B6D11;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .quality-badge-amber {
        background: #FAEEDA;
        color: #854F0B;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .quality-badge-red {
        background: #FCEBEB;
        color: #A32D2D;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🌿 GreenBIM")
    st.markdown("*Sustainable Building Intelligence*")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Home & Upload",
            "📦 IFC Parser",
            "🔥 Embodied Carbon",
            "♻️ Circularity Score",
            "🎯 Carbon Benchmark",
            "💡 Carbon Saving Potential",
            "🌲 Biogenic Carbon",
            "🤖 AI Recommendations",
            "📄 Building Passport"
        ]
    )
    st.markdown("---")
    st.markdown("**Standard:** EN 15978")
    st.markdown("**Database:** co2data.fi / EN 15804")
    st.markdown("**Benchmark:** Finnish MoE 2021")

if "ifc_df" not in st.session_state:
    st.session_state.ifc_df = None
if "carbon_df" not in st.session_state:
    st.session_state.carbon_df = None
if "final_df" not in st.session_state:
    st.session_state.final_df = None
if "benchmark_result" not in st.session_state:
    st.session_state.benchmark_result = None
if "substitutions" not in st.session_state:
    st.session_state.substitutions = None
if "ai_recommendations" not in st.session_state:
    st.session_state.ai_recommendations = None
if "project_name" not in st.session_state:
    st.session_state.project_name = "My Building"
if "project_location" not in st.session_state:
    st.session_state.project_location = "Finland"
if "building_type" not in st.session_state:
    st.session_state.building_type = "Residential apartment block"
if "floor_area" not in st.session_state:
    st.session_state.floor_area = 1000


# ============================================================
# PAGE 1 - HOME & UPLOAD
# ============================================================
if page == "🏠 Home & Upload":
    st.title("🌿 GreenBIM — Sustainable Building Intelligence")
    st.markdown(
        "Upload your IFC building model to assess embodied carbon, "
        "material circularity, and sustainability performance against "
        "Finnish and EU standards."
    )
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Building Information")
        st.session_state.project_name = st.text_input(
            "Project name", value=st.session_state.project_name
        )
        st.session_state.project_location = st.text_input(
            "Location", value=st.session_state.project_location
        )
        st.session_state.building_type = st.selectbox(
            "Building type",
            list(FINNISH_BENCHMARKS.keys())
        )
        st.session_state.floor_area = st.number_input(
            "Gross floor area (m²)",
            min_value=1,
            max_value=500000,
            value=st.session_state.floor_area
        )

    with col2:
        st.subheader("Upload IFC File")
        uploaded_file = st.file_uploader(
            "Drag and drop or browse",
            type=["ifc"],
            help="Supports IFC 2x3 and IFC4 format"
        )

        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".ifc"
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            progress = st.progress(0)
            status = st.empty()

            status.markdown("Parsing IFC file...")
            progress.progress(20)
            try:
                st.session_state.ifc_df = parse_ifc(tmp_path)
                st.success(
                    f"IFC file parsed successfully. "
                    f"{len(st.session_state.ifc_df)} elements found."
                )
            except Exception as e:
                st.error(f"Error parsing IFC file: {e}")
                st.session_state.ifc_df = None

            status.markdown("Calculating embodied carbon...")
            progress.progress(40)
            try:
                st.session_state.carbon_df = calculate_carbon(
                    st.session_state.ifc_df
                )
            except Exception as e:
                st.error(f"Carbon calculation error: {e}")

            status.markdown("Scoring circularity...")
            progress.progress(60)
            try:
                st.session_state.final_df = calculate_circularity(
                    st.session_state.carbon_df
                )
            except Exception as e:
                st.error(f"Circularity scoring error: {e}")

            status.markdown("Running benchmark...")
            progress.progress(80)
            try:
                total_carbon = st.session_state.carbon_df[
                    "carbon_kg_co2e"
                ].sum()
                st.session_state.benchmark_result = get_benchmark_result(
                    total_carbon,
                    st.session_state.floor_area,
                    st.session_state.building_type
                )
            except Exception as e:
                st.error(f"Benchmark error: {e}")

            status.markdown("Getting substitution suggestions...")
            progress.progress(95)
            try:
                st.session_state.substitutions = (
                    get_substitution_suggestions(
                        st.session_state.carbon_df
                    )
                )
            except Exception as e:
                st.error(f"Substitution error: {e}")

            progress.progress(100)
            status.markdown("")
            os.unlink(tmp_path)

    if st.session_state.final_df is not None:
        st.markdown("---")
        st.subheader("Building Overview")
        total_carbon = st.session_state.carbon_df[
            "carbon_kg_co2e"
        ].sum()
        total_carbon_t = round(total_carbon / 1000, 2)
        carbon_per_m2 = round(
            total_carbon / st.session_state.floor_area, 1
        )
        circ_grade, circ_score = get_building_circularity_grade(
            st.session_state.final_df
        )
        hazardous = int(
            st.session_state.final_df["hazardous_flag"].sum()
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Total Embodied Carbon", f"{total_carbon_t} tCO₂e"
        )
        c2.metric(
            "Carbon Intensity", f"{carbon_per_m2} kgCO₂e/m²"
        )
        c3.metric(
            "Circularity Grade", f"{circ_grade} ({circ_score})"
        )
        c4.metric("Hazardous Flags", str(hazardous))

        if st.session_state.benchmark_result:
            br = st.session_state.benchmark_result
            if br["status"] == "green":
                st.success(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of "
                    f"{br['target_per_m2']} kgCO₂e/m²"
                )
            elif br["status"] == "amber":
                st.warning(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of "
                    f"{br['target_per_m2']} kgCO₂e/m²"
                )
            else:
                st.error(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of "
                    f"{br['target_per_m2']} kgCO₂e/m²"
                )

        if st.session_state.carbon_df is not None:
            df_home = st.session_state.carbon_df
            verified = len(
                df_home[
                    df_home["match_status"] == "matched_co2data"
                ]
            )
            total_home = len(df_home)
            verified_pct = round(
                verified / total_home * 100
            ) if total_home > 0 else 0
            st.caption(
                f"Data quality: {verified_pct}% of elements "
                f"use Finnish verified EPD data from co2data.fi "
                f"/ Finnish Environment Institute Syke"
            )


# ============================================================
# PAGE 2 - IFC PARSER
# ============================================================
elif page == "📦 IFC Parser":
    st.title("📦 IFC Model Parser")
    st.markdown(
        "Extracted elements, materials, volumes "
        "and storey assignments."
    )

    if st.session_state.ifc_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        df = st.session_state.ifc_df
        summary = get_summary(df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Elements", summary["total_elements"])
        c2.metric("Unique Materials", summary["unique_materials"])
        c3.metric(
            "Missing Materials", summary["missing_material"]
        )
        c4.metric("Missing Volumes", summary["missing_volume"])

        tab1, tab2, tab3 = st.tabs(
            ["All Elements", "By Type", "Missing Data Flags"]
        )

        with tab1:
            st.dataframe(df, use_container_width=True)

        with tab2:
            by_type = (
                df["element_type"].value_counts().reset_index()
            )
            by_type.columns = ["Element Type", "Count"]
            fig = px.bar(
                by_type,
                x="Element Type",
                y="Count",
                color="Count",
                color_continuous_scale="Teal",
                title="Elements by Type"
            )
            st.plotly_chart(fig, use_container_width=True)

            vol_by_type = (
                df.groupby("element_type")["volume_m3"]
                .sum()
                .reset_index()
            )
            vol_by_type.columns = ["Element Type", "Volume m³"]
            fig2 = px.bar(
                vol_by_type,
                x="Element Type",
                y="Volume m³",
                color="Volume m³",
                color_continuous_scale="Blues",
                title="Volume by Element Type (m³)"
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            missing_mat = df[df["material"] == "Unknown"]
            missing_vol = df[df["volume_m3"] == 0]
            missing_storey = df[df["storey"] == "Unknown"]

            st.markdown(
                f"**Missing material:** "
                f"{len(missing_mat)} elements"
            )
            if not missing_mat.empty:
                st.dataframe(
                    missing_mat, use_container_width=True
                )

            st.markdown(
                f"**Missing volume:** "
                f"{len(missing_vol)} elements"
            )
            if not missing_vol.empty:
                st.dataframe(
                    missing_vol, use_container_width=True
                )

            st.markdown(
                f"**Missing storey:** "
                f"{len(missing_storey)} elements"
            )
            if not missing_storey.empty:
                st.dataframe(
                    missing_storey, use_container_width=True
                )


# ============================================================
# PAGE 3 - EMBODIED CARBON
# ============================================================
elif page == "🔥 Embodied Carbon":
    st.title("🔥 Embodied Carbon Assessment")
    st.markdown(
        "Lifecycle stages A1–A3 — Product stage embodied carbon "
        "per element, material and floor. Standard: EN 15978 / "
        "co2data.fi / Finnish Environment Institute Syke"
    )

    if st.session_state.carbon_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        df = st.session_state.carbon_df
        total_carbon = df["carbon_kg_co2e"].sum()
        total_carbon_t = round(total_carbon / 1000, 2)
        carbon_per_m2 = round(
            total_carbon / st.session_state.floor_area, 1
        )
        unmatched = int(
            (df["match_status"] == "unmatched").sum()
        )
        verified = len(
            df[df["match_status"] == "matched_co2data"]
        )
        verified_pct = round(
            verified / len(df) * 100
        ) if len(df) > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Total Carbon A1-A3", f"{total_carbon_t} tCO₂e"
        )
        c2.metric(
            "Carbon Intensity", f"{carbon_per_m2} kgCO₂e/m²"
        )
        c3.metric("Total Elements", len(df))
        c4.metric("Unmatched Elements", unmatched)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "By Material",
            "By Floor",
            "By Element Type",
            "Hotspots",
            "Data Quality"
        ])

        with tab1:
            mat_carbon = (
                df.groupby("matched_material")["carbon_kg_co2e"]
                .sum()
                .reset_index()
                .sort_values(
                    "carbon_kg_co2e", ascending=False
                )
            )
            mat_carbon["carbon_tCO2e"] = (
                mat_carbon["carbon_kg_co2e"] / 1000
            ).round(2)
            fig = px.bar(
                mat_carbon,
                x="matched_material",
                y="carbon_tCO2e",
                color="carbon_tCO2e",
                color_continuous_scale="Reds",
                labels={
                    "matched_material": "Material",
                    "carbon_tCO2e": "tCO₂e"
                },
                title="Embodied Carbon by Material (tCO₂e)"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            storey_carbon = get_carbon_by_storey(df)
            storey_carbon["carbon_tCO2e"] = (
                storey_carbon["carbon_kg_co2e"] / 1000
            ).round(2)
            fig2 = px.bar(
                storey_carbon,
                x="storey",
                y="carbon_tCO2e",
                color="carbon_tCO2e",
                color_continuous_scale="Oranges",
                labels={
                    "storey": "Floor",
                    "carbon_tCO2e": "tCO₂e"
                },
                title=(
                    "Embodied Carbon by Building Storey (tCO₂e)"
                )
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            type_carbon = get_carbon_by_type(df)
            type_carbon["carbon_tCO2e"] = (
                type_carbon["carbon_kg_co2e"] / 1000
            ).round(2)
            fig3 = px.pie(
                type_carbon,
                values="carbon_tCO2e",
                names="element_type",
                title="Carbon Distribution by Element Type",
                color_discrete_sequence=(
                    px.colors.sequential.Reds_r
                )
            )
            st.plotly_chart(fig3, use_container_width=True)

        with tab4:
            st.subheader("Top Carbon Hotspots")
            hotspots = get_hotspots(df)
            if not hotspots.empty:
                for _, row in hotspots.iterrows():
                    with st.expander(
                        f"{row['matched_material']} — "
                        f"{round(row['total_carbon']/1000, 2)}"
                        f" tCO₂e "
                        f"({row['carbon_pct']}% of total)"
                    ):
                        h1, h2, h3 = st.columns(3)
                        h1.metric(
                            "Total Carbon",
                            f"{round(row['total_carbon']/1000, 2)}"
                            f" tCO₂e"
                        )
                        h2.metric(
                            "Share of Total",
                            f"{row['carbon_pct']}%"
                        )
                        h3.metric(
                            "Elements",
                            str(int(row["element_count"]))
                        )
            else:
                st.info("No hotspot data available.")

        with tab5:
            st.subheader("Data Quality Report")
            st.markdown(
                "Shows the source and reliability of carbon "
                "data for each element."
            )

            total = len(df)
            generic = len(
                df[df["match_status"] == "matched_csv"]
            )
            generic_pct = round(
                generic / total * 100
            ) if total > 0 else 0
            unmatched_pct = round(
                unmatched / total * 100
            ) if total > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Finnish Verified EPD",
                f"{verified} elements",
                f"{verified_pct}% of total"
            )
            col2.metric(
                "Generic EN 15804",
                f"{generic} elements",
                f"{generic_pct}% of total"
            )
            col3.metric(
                "No Match",
                f"{unmatched} elements",
                f"{unmatched_pct}% of total"
            )

            if verified_pct >= 80:
                st.success(
                    f"High data quality — {verified_pct}% of "
                    f"elements use Finnish verified EPD data "
                    f"from co2data.fi / Finnish Environment "
                    f"Institute Syke"
                )
            elif verified_pct >= 50:
                st.warning(
                    f"Medium data quality — {verified_pct}% "
                    f"Finnish verified. Consider using standard "
                    f"material names in your BIM model."
                )
            else:
                st.error(
                    f"Low data quality — only {verified_pct}% "
                    f"Finnish verified. Assign standard material "
                    f"names in Archicad or Revit for better "
                    f"results."
                )

            st.markdown("---")
            st.markdown("**Element level data quality:**")

            quality_df = df[[
                "element_type",
                "storey",
                "material",
                "matched_material",
                "carbon_kg_co2e",
                "data_quality",
                "source"
            ]].copy()
            quality_df["carbon_tCO2e"] = (
                quality_df["carbon_kg_co2e"] / 1000
            ).round(4)
            quality_df = quality_df.drop(
                columns=["carbon_kg_co2e"]
            )

            def color_quality(val):
                if val == "Finnish verified EPD":
                    return "background-color: #EAF3DE"
                elif val == "Generic EN 15804":
                    return "background-color: #FAEEDA"
                else:
                    return "background-color: #FCEBEB"

            st.dataframe(
                quality_df.style.applymap(
                    color_quality,
                    subset=["data_quality"]
                ),
                use_container_width=True
            )

            st.markdown("---")
            st.markdown("**How to improve data quality:**")
            st.markdown(
                "- In **Archicad**: Building Materials → "
                "assign Finnish supplier names like "
                "Rudus C25/30, SSAB S355, Paroc Extra"
            )
            st.markdown(
                "- In **Revit**: Materials → use standard "
                "names matching Finnish suppliers"
            )
            st.markdown(
                "- In **Tekla**: Material catalogue → "
                "use standard Finnish material names"
            )

            fig_quality = px.pie(
                values=[verified, generic, unmatched],
                names=[
                    "Finnish Verified EPD",
                    "Generic EN 15804",
                    "No Match"
                ],
                color_discrete_sequence=[
                    "#1D9E75", "#EF9F27", "#D85A30"
                ],
                title="Data Quality Distribution"
            )
            st.plotly_chart(
                fig_quality, use_container_width=True
            )


# ============================================================
# PAGE 4 - CIRCULARITY
# ============================================================
elif page == "♻️ Circularity Score":
    st.title("♻️ Circularity Score")
    st.markdown(
        "Material recyclability, recycled content, disassembly "
        "potential and end of life pathways. Based on EU Level(s) "
        "framework Indicator 2.2 and EN 15978."
    )

    if st.session_state.final_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        df = st.session_state.final_df
        circ_grade, circ_score = get_building_circularity_grade(
            df
        )
        hazardous = int(df["hazardous_flag"].sum())
        low_circ = get_low_circularity_flags(df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Grade", circ_grade)
        c2.metric("Overall Score", str(circ_score))
        c3.metric("Hazardous Flags", str(hazardous))
        c4.metric(
            "Low Circularity Elements", str(len(low_circ))
        )

        tab1, tab2, tab3 = st.tabs(
            ["By Material", "Detailed Breakdown", "Flags"]
        )

        with tab1:
            circ_by_mat = get_circularity_by_material(df)
            fig = px.bar(
                circ_by_mat,
                x="matched_material",
                y="avg_score",
                color="avg_score",
                color_continuous_scale="Greens",
                range_y=[0, 1],
                labels={
                    "matched_material": "Material",
                    "avg_score": "Circularity Score"
                },
                title="Circularity Score by Material (0-1)"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            scored = df[df["circularity_score"].notna()]
            detail = (
                scored.groupby("matched_material")
                .agg(
                    score=("circularity_score", "mean"),
                    grade=("circularity_grade", "first"),
                    recyclability=("recyclability", "mean"),
                    recycled_content=(
                        "recycled_content", "mean"
                    ),
                    disassembly=("disassembly", "mean"),
                    pathway=(
                        "end_of_life_pathway", "first"
                    )
                )
                .reset_index()
                .sort_values("score", ascending=False)
            )
            st.dataframe(detail, use_container_width=True)

        with tab3:
            if hazardous > 0:
                st.error(
                    f"{hazardous} hazardous material "
                    f"flags detected"
                )
                haz = df[df["hazardous_flag"] == True]
                st.dataframe(haz, use_container_width=True)
            else:
                st.success("No hazardous materials detected")

            if len(low_circ) > 0:
                st.warning(
                    f"{len(low_circ)} elements with low "
                    f"circularity score below 0.40"
                )
                st.dataframe(
                    low_circ, use_container_width=True
                )
            else:
                st.success(
                    "No low circularity elements detected"
                )


# ============================================================
# PAGE 5 - CARBON BENCHMARK
# ============================================================
elif page == "🎯 Carbon Benchmark":
    st.title("🎯 Carbon Budget Benchmark")
    st.markdown(
        "Comparison against Finnish Ministry of Environment "
        "carbon targets. Standard: Finnish MoE 2021 / EN 15978. "
        "Reference period: 50 years."
    )

    if st.session_state.carbon_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        br = st.session_state.benchmark_result

        if br:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Your Carbon Intensity",
                f"{br['carbon_per_m2']} kgCO₂e/m²"
            )
            c2.metric(
                "Finnish Target",
                f"{br['target_per_m2']} kgCO₂e/m²"
            )
            c3.metric(
                "Difference",
                f"{br['difference_per_m2']:+.1f} kgCO₂e/m²"
            )
            c4.metric(
                "% of Target",
                f"{br['percentage_of_target']}%"
            )

            if br["status"] == "green":
                st.success(f"Status: {br['label']}")
            elif br["status"] == "amber":
                st.warning(f"Status: {br['label']}")
            else:
                st.error(f"Status: {br['label']}")

            tab1, tab2 = st.tabs(
                ["Visual Comparison", "All Benchmarks"]
            )

            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Your building",
                    x=["Your building"],
                    y=[br["carbon_per_m2"]],
                    marker_color="#D85A30"
                ))
                fig.add_trace(go.Bar(
                    name="Finnish target",
                    x=["Finnish target"],
                    y=[br["target_per_m2"]],
                    marker_color="#1D9E75"
                ))
                fig.update_layout(
                    title=(
                        f"Carbon Intensity vs Finnish Target "
                        f"(kgCO₂e/m²) — {br['building_type']}"
                    ),
                    yaxis_title="kgCO₂e/m²",
                    barmode="group"
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                benchmark_df = pd.DataFrame([
                    {
                        "Building Type": k,
                        "Target kgCO₂e/m²": v["target"],
                        "Reference Years": v["reference_years"],
                        "Standard": (
                            "Finnish MoE 2021 / EN 15978"
                        )
                    }
                    for k, v in FINNISH_BENCHMARKS.items()
                ])
                st.dataframe(
                    benchmark_df, use_container_width=True
                )


# ============================================================
# PAGE 6 - CARBON SAVING POTENTIAL
# ============================================================
elif page == "💡 Carbon Saving Potential":
    st.title("💡 Carbon Saving Potential")
    st.markdown(
        "Shows the potential carbon reduction if material "
        "substitutions are applied. Based on EN 15804 aligned "
        "alternatives from Finnish and EU databases."
    )

    if st.session_state.carbon_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    elif not st.session_state.substitutions:
        st.warning(
            "No substitution suggestions available for "
            "this building."
        )
    else:
        df = st.session_state.carbon_df
        subs = st.session_state.substitutions

        total_current = df["carbon_kg_co2e"].sum()
        total_current_t = round(total_current / 1000, 2)

        total_saving_kg = sum(
            s["carbon_saving_kg"] for s in subs
            if s["carbon_saving_kg"] > 0
        )
        total_saving_t = round(total_saving_kg / 1000, 2)
        total_after_t = round(
            total_current_t - total_saving_t, 2
        )
        saving_pct = round(
            total_saving_kg / total_current * 100
        ) if total_current > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Current Total Carbon",
            f"{total_current_t} tCO₂e"
        )
        c2.metric(
            "Potential Saving",
            f"{total_saving_t} tCO₂e",
            f"-{saving_pct}%"
        )
        c3.metric(
            "Carbon After Substitutions",
            f"{total_after_t} tCO₂e"
        )
        c4.metric(
            "Substitutions Available",
            str(len(subs))
        )

        if saving_pct >= 30:
            st.success(
                f"High saving potential — applying all "
                f"substitutions reduces embodied carbon by "
                f"{saving_pct}% ({total_saving_t} tCO₂e)"
            )
        elif saving_pct >= 15:
            st.warning(
                f"Medium saving potential — applying all "
                f"substitutions reduces embodied carbon by "
                f"{saving_pct}% ({total_saving_t} tCO₂e)"
            )
        else:
            st.info(
                f"Modest saving potential — applying all "
                f"substitutions reduces embodied carbon by "
                f"{saving_pct}% ({total_saving_t} tCO₂e)"
            )

        st.markdown("---")
        st.subheader("Before and After Comparison")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Current carbon",
            x=["Current design"],
            y=[total_current_t],
            marker_color="#D85A30",
            text=[f"{total_current_t} tCO₂e"],
            textposition="outside"
        ))
        fig.add_trace(go.Bar(
            name="After substitutions",
            x=["With substitutions"],
            y=[total_after_t],
            marker_color="#1D9E75",
            text=[f"{total_after_t} tCO₂e"],
            textposition="outside"
        ))
        if st.session_state.benchmark_result:
            br = st.session_state.benchmark_result
            target_total_t = round(
                br["target_per_m2"] *
                st.session_state.floor_area / 1000, 2
            )
            fig.add_trace(go.Bar(
                name="Finnish MoE 2021 target",
                x=["Finnish target"],
                y=[target_total_t],
                marker_color="#378ADD",
                text=[f"{target_total_t} tCO₂e"],
                textposition="outside"
            ))
        fig.update_layout(
            title=(
                "Total Embodied Carbon — "
                "Before vs After (tCO₂e)"
            ),
            yaxis_title="tCO₂e",
            barmode="group",
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Substitution Breakdown")

        for s in subs:
            if s["carbon_saving_kg"] > 0:
                with st.expander(
                    f"#{s['rank']} — "
                    f"{s['current_material']} → "
                    f"{s['alternative_material']} "
                    f"— saves {s['carbon_saving_t']} tCO₂e "
                    f"({s['carbon_saving_pct']}%)"
                ):
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Current Carbon",
                        f"{s['current_carbon_t']} tCO₂e"
                    )
                    col2.metric(
                        "After Substitution",
                        f"{s['alternative_carbon_t']} tCO₂e"
                    )
                    col3.metric(
                        "Carbon Saving",
                        f"{s['carbon_saving_t']} tCO₂e",
                        f"-{s['carbon_saving_pct']}%"
                    )
                    saving_fig = go.Figure()
                    saving_fig.add_trace(go.Bar(
                        name="Current",
                        x=["Current"],
                        y=[s["current_carbon_t"]],
                        marker_color="#D85A30"
                    ))
                    saving_fig.add_trace(go.Bar(
                        name="Alternative",
                        x=["Alternative"],
                        y=[s["alternative_carbon_t"]],
                        marker_color="#1D9E75"
                    ))
                    saving_fig.update_layout(
                        title=(
                            f"{s['current_material']} "
                            f"substitution impact (tCO₂e)"
                        ),
                        yaxis_title="tCO₂e",
                        barmode="group",
                        height=300
                    )
                    st.plotly_chart(
                        saving_fig,
                        use_container_width=True
                    )
                    st.info(f"Reason: {s['reason']}")
                    st.caption(f"Standard: {s['standard']}")

        st.markdown("---")
        st.subheader("Cumulative Carbon Reduction")

        labels = ["Current carbon"]
        values = [total_current_t]
        measures = ["absolute"]

        for s in subs:
            if s["carbon_saving_kg"] > 0:
                labels.append(
                    f"Replace {s['current_material'][:25]}"
                )
                values.append(-s["carbon_saving_t"])
                measures.append("relative")

        labels.append("Final carbon")
        values.append(total_after_t)
        measures.append("total")

        waterfall_fig = go.Figure(go.Waterfall(
            name="Carbon reduction pathway",
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            connector={"line": {"color": "#888780"}},
            decreasing={"marker": {"color": "#1D9E75"}},
            increasing={"marker": {"color": "#D85A30"}},
            totals={"marker": {"color": "#378ADD"}}
        ))
        waterfall_fig.update_layout(
            title=(
                "Carbon Reduction Pathway — "
                "Step by Step (tCO₂e)"
            ),
            yaxis_title="tCO₂e",
            showlegend=False
        )
        st.plotly_chart(
            waterfall_fig, use_container_width=True
        )


# ============================================================
# PAGE 7 - BIOGENIC CARBON
# ============================================================
elif page == "🌲 Biogenic Carbon":
    st.title("🌲 Biogenic Carbon Tracker")
    st.markdown(
        "Timber elements store biogenic carbon absorbed from "
        "the atmosphere during tree growth. This offsets "
        "embodied carbon and can make timber buildings "
        "carbon negative. Standard: EN 16485 / EN 15978."
    )

    if st.session_state.carbon_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        summary = get_biogenic_summary(
            st.session_state.carbon_df
        )

        if not summary["has_timber"]:
            st.info(
                "No timber elements detected in this IFC "
                "model. Biogenic carbon analysis requires "
                "timber structural elements such as glulam, "
                "CLT, LVL or sawn timber."
            )
        else:
            total_embodied_t = summary[
                "total_embodied_carbon_t"
            ]
            total_biogenic_t = summary[
                "total_biogenic_carbon_t"
            ]
            total_net_t = summary["total_net_carbon_t"]
            offset_pct = summary["biogenic_offset_pct"]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Timber Elements",
                str(summary["timber_elements"])
            )
            c2.metric(
                "Total Embodied Carbon",
                f"{total_embodied_t} tCO₂e"
            )
            c3.metric(
                "Biogenic Carbon Stored",
                f"{total_biogenic_t} tCO₂e"
            )
            c4.metric(
                "Net Carbon Balance",
                f"{total_net_t} tCO₂e",
                f"{offset_pct}% offset"
            )

            if summary["is_carbon_negative"]:
                st.success(
                    f"This building is carbon negative — "
                    f"biogenic carbon storage "
                    f"({abs(total_biogenic_t)} tCO₂e) "
                    f"exceeds total embodied carbon "
                    f"({total_embodied_t} tCO₂e). "
                    f"Net carbon: {total_net_t} tCO₂e"
                )
            elif offset_pct >= 50:
                st.success(
                    f"High biogenic offset — timber elements "
                    f"store enough carbon to offset "
                    f"{offset_pct}% of total embodied carbon"
                )
            elif offset_pct >= 20:
                st.warning(
                    f"Moderate biogenic offset — timber "
                    f"elements offset {offset_pct}% of "
                    f"total embodied carbon. Consider "
                    f"increasing timber use."
                )
            else:
                st.info(
                    f"Low biogenic offset — timber elements "
                    f"offset {offset_pct}% of total embodied "
                    f"carbon. Increasing timber use would "
                    f"significantly improve net carbon balance."
                )

            st.markdown("---")

            tab1, tab2, tab3 = st.tabs([
                "Carbon Balance Chart",
                "Timber Elements",
                "What Is Biogenic Carbon"
            ])

            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Embodied carbon (A1-A3)",
                    x=["Carbon balance"],
                    y=[total_embodied_t],
                    marker_color="#D85A30",
                    text=[f"{total_embodied_t} tCO₂e"],
                    textposition="outside"
                ))
                fig.add_trace(go.Bar(
                    name="Biogenic carbon stored",
                    x=["Carbon balance"],
                    y=[total_biogenic_t],
                    marker_color="#1D9E75",
                    text=[f"{total_biogenic_t} tCO₂e"],
                    textposition="outside"
                ))
                fig.add_trace(go.Bar(
                    name="Net carbon balance",
                    x=["Net balance"],
                    y=[total_net_t],
                    marker_color=(
                        "#378ADD"
                        if total_net_t > 0
                        else "#1D9E75"
                    ),
                    text=[f"{total_net_t} tCO₂e"],
                    textposition="outside"
                ))
                fig.update_layout(
                    title=(
                        "Embodied vs Biogenic Carbon "
                        "Balance (tCO₂e)"
                    ),
                    yaxis_title="tCO₂e",
                    barmode="group"
                )
                st.plotly_chart(
                    fig, use_container_width=True
                )

                biogenic_df = summary["biogenic_df"]
                by_material = (
                    biogenic_df.groupby("matched_material")
                    .agg(
                        embodied=(
                            "embodied_carbon_kg", "sum"
                        ),
                        biogenic=(
                            "biogenic_carbon_kg", "sum"
                        ),
                        net=("net_carbon_kg", "sum")
                    )
                    .reset_index()
                )
                by_material["embodied_t"] = (
                    by_material["embodied"] / 1000
                ).round(3)
                by_material["biogenic_t"] = (
                    by_material["biogenic"] / 1000
                ).round(3)
                by_material["net_t"] = (
                    by_material["net"] / 1000
                ).round(3)

                fig2 = px.bar(
                    by_material,
                    x="matched_material",
                    y=["embodied_t", "biogenic_t", "net_t"],
                    barmode="group",
                    color_discrete_map={
                        "embodied_t": "#D85A30",
                        "biogenic_t": "#1D9E75",
                        "net_t": "#378ADD"
                    },
                    labels={
                        "matched_material": "Material",
                        "value": "tCO₂e",
                        "variable": "Carbon type"
                    },
                    title=(
                        "Carbon Balance by Timber Material"
                    )
                )
                st.plotly_chart(
                    fig2, use_container_width=True
                )

            with tab2:
                biogenic_df = summary["biogenic_df"]
                display_df = biogenic_df[[
                    "element_type",
                    "storey",
                    "matched_material",
                    "volume_m3",
                    "mass_kg",
                    "embodied_carbon_kg",
                    "biogenic_carbon_kg",
                    "net_carbon_kg",
                    "source"
                ]].copy()
                display_df["embodied_tCO2e"] = (
                    display_df["embodied_carbon_kg"] / 1000
                ).round(4)
                display_df["biogenic_tCO2e"] = (
                    display_df["biogenic_carbon_kg"] / 1000
                ).round(4)
                display_df["net_tCO2e"] = (
                    display_df["net_carbon_kg"] / 1000
                ).round(4)
                display_df = display_df.drop(columns=[
                    "embodied_carbon_kg",
                    "biogenic_carbon_kg",
                    "net_carbon_kg"
                ])
                st.dataframe(
                    display_df, use_container_width=True
                )

            with tab3:
                st.markdown("""
**What is biogenic carbon?**

When trees grow they absorb CO₂ from the atmosphere
through photosynthesis and store it as carbon in their
wood. This is called biogenic carbon. When timber is
harvested and used in a building that carbon remains
locked in the wood for the entire life of the building.

**Why does it matter?**

Under EN 15978 and EN 16485 biogenic carbon stored in
timber products is reported as a negative value meaning
it reduces the net carbon footprint of the building. A
building with significant timber structure can have a
net carbon balance close to zero or even negative.

**How is it calculated?**

Each kilogram of dry timber stores approximately
0.92 kg of CO₂ equivalent. This value is multiplied
by the mass of each timber element to give the total
biogenic carbon stored.

**Finnish context**

Finland has one of the highest rates of timber
construction in Europe. Finnish timber from Metsä Wood,
Stora Enso, and Versowood comes from sustainably managed
forests certified under PEFC or FSC. This makes Finnish
timber construction one of the most carbon effective
building methods available.

**Standard references**

- EN 16485: Round and sawn timber — EPDs — rules for
  category for wood and wood-based products
- EN 15978: Sustainability of construction works —
  assessment of environmental performance of buildings
- Finnish Ministry of Environment carbon assessment
  method 2021 — biogenic carbon module D reporting
                """)

        st.markdown("---")
        st.caption(
            "Biogenic carbon data based on EN 16485 and "
            "co2data.fi Finnish Environment Institute Syke. "
            "Conservative factor 1.2 applied per Finnish "
            "MoE 2021 method."
        )


# ============================================================
# PAGE 8 - AI RECOMMENDATIONS
# ============================================================
elif page == "🤖 AI Recommendations":
    st.title("🤖 AI Sustainability Recommendations")
    st.markdown(
        "AI-generated recommendations based on your building's "
        "specific assessment data. Aligned with Finnish and EU "
        "sustainability standards."
    )

    if st.session_state.carbon_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        tab1, tab2 = st.tabs(
            ["AI Recommendations", "Material Substitutions"]
        )

        with tab1:
            if st.session_state.ai_recommendations:
                st.markdown(st.session_state.ai_recommendations)
            else:
                if st.button(
                    "Generate AI Recommendations",
                    type="primary"
                ):
                    with st.spinner(
                        "Claude is analysing your building..."
                    ):
                        try:
                            st.session_state.ai_recommendations = (
                                get_ai_recommendations(
                                    st.session_state.carbon_df,
                                    st.session_state.final_df,
                                    st.session_state.substitutions,
                                    st.session_state.benchmark_result
                                )
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"AI agent error: {e}")
                            st.info(
                                "Check your GROQ_API_KEY "
                                "in the .env file."
                            )

        with tab2:
            if st.session_state.substitutions:
                for s in st.session_state.substitutions:
                    with st.expander(
                        f"#{s['rank']} — "
                        f"{s['current_material']} → "
                        f"{s['alternative_material']} "
                        f"(saves {s['carbon_saving_pct']}%)"
                    ):
                        s1, s2, s3 = st.columns(3)
                        s1.metric(
                            "Current Carbon",
                            f"{s['current_carbon_t']} tCO₂e"
                        )
                        s2.metric(
                            "Alternative Carbon",
                            f"{s['alternative_carbon_t']} tCO₂e"
                        )
                        s3.metric(
                            "Saving",
                            f"{s['carbon_saving_t']} tCO₂e"
                        )
                        st.info(f"Reason: {s['reason']}")
                        st.caption(
                            f"Standard: {s['standard']}"
                        )
            else:
                st.info(
                    "No substitution suggestions available."
                )


# ============================================================
# PAGE 9 - BUILDING PASSPORT
# ============================================================
elif page == "📄 Building Passport":
    st.title("📄 Digital Building Passport")
    st.markdown(
        "EU-aligned Digital Building Passport with full material "
        "inventory, carbon assessment, circularity scores and "
        "AI recommendations. Aligned with EN 15978 and Finnish "
        "Ministry of Environment 2021."
    )

    if st.session_state.final_df is None:
        st.warning(
            "Please upload an IFC file on the Home page first."
        )
    else:
        circ_grade, circ_score = get_building_circularity_grade(
            st.session_state.final_df
        )

        st.subheader("Passport Summary")
        p1, p2 = st.columns(2)

        with p1:
            st.markdown("**Building Identity**")
            st.write(
                f"Project: {st.session_state.project_name}"
            )
            st.write(
                f"Location: "
                f"{st.session_state.project_location}"
            )
            st.write(
                f"Type: {st.session_state.building_type}"
            )
            st.write(
                f"Floor area: "
                f"{st.session_state.floor_area} m²"
            )

        with p2:
            st.markdown("**Sustainability Summary**")
            total_carbon_t = round(
                st.session_state.carbon_df[
                    "carbon_kg_co2e"
                ].sum() / 1000, 2
            )
            st.write(f"Total carbon: {total_carbon_t} tCO₂e")
            st.write(
                f"Circularity grade: "
                f"{circ_grade} ({circ_score})"
            )
            if st.session_state.benchmark_result:
                st.write(
                    f"Benchmark: "
                    f"{st.session_state.benchmark_result['label']}"
                )
            verified = len(
                st.session_state.carbon_df[
                    st.session_state.carbon_df[
                        "match_status"
                    ] == "matched_co2data"
                ]
            )
            total_els = len(st.session_state.carbon_df)
            verified_pct = round(
                verified / total_els * 100
            ) if total_els > 0 else 0
            st.write(
                f"Data quality: "
                f"{verified_pct}% Finnish verified EPD"
            )

        st.markdown("---")
        st.subheader("Generate and Download Passport")

        if st.button(
            "Generate Building Passport PDF", type="primary"
        ):
            with st.spinner("Generating PDF passport..."):
                try:
                    output_path = os.path.join(
                        tempfile.gettempdir(),
                        "greenbim_passport.pdf"
                    )
                    generate_passport(
                        output_path=output_path,
                        project_name=(
                            st.session_state.project_name
                        ),
                        project_location=(
                            st.session_state.project_location
                        ),
                        building_type=(
                            st.session_state.building_type
                        ),
                        floor_area=(
                            st.session_state.floor_area
                        ),
                        carbon_df=st.session_state.carbon_df,
                        final_df=st.session_state.final_df,
                        benchmark_result=(
                            st.session_state.benchmark_result
                        ),
                        substitutions=(
                            st.session_state.substitutions
                            or []
                        ),
                        ai_recommendations=(
                            st.session_state.ai_recommendations
                            or "Not generated yet."
                        ),
                        circularity_grade=circ_grade,
                        circularity_score=circ_score
                    )
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label=(
                                "Download Building Passport PDF"
                            ),
                            data=f,
                            file_name=(
                                f"GreenBIM_Passport_"
                                f"{st.session_state.project_name}"
                                f".pdf"
                            ),
                            mime="application/pdf"
                        )
                    st.success(
                        "Passport generated successfully."
                    )
                except Exception as e:
                    st.error(f"PDF generation error: {e}")