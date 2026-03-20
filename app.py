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
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
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
            "🤖 AI Recommendations",
            "📄 Building Passport"
        ]
    )
    st.markdown("---")
    st.markdown("**Standard:** EN 15978")
    st.markdown("**Database:** EN 15804 / Ökobaudat")
    st.markdown("**Benchmark:** Finnish MoE 2021")

# --- Session State ---
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

            with st.spinner("Parsing IFC file..."):
                try:
                    st.session_state.ifc_df = parse_ifc(tmp_path)
                    st.success(
                        f"IFC file parsed successfully. "
                        f"{len(st.session_state.ifc_df)} elements found."
                    )
                except Exception as e:
                    st.error(f"Error parsing IFC file: {e}")
                    st.session_state.ifc_df = None

            with st.spinner("Calculating embodied carbon..."):
                try:
                    st.session_state.carbon_df = calculate_carbon(
                        st.session_state.ifc_df
                    )
                except Exception as e:
                    st.error(f"Carbon calculation error: {e}")

            with st.spinner("Scoring circularity..."):
                try:
                    st.session_state.final_df = calculate_circularity(
                        st.session_state.carbon_df
                    )
                except Exception as e:
                    st.error(f"Circularity scoring error: {e}")

            with st.spinner("Running benchmark..."):
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

            with st.spinner("Getting substitution suggestions..."):
                try:
                    st.session_state.substitutions = (
                        get_substitution_suggestions(
                            st.session_state.carbon_df
                        )
                    )
                except Exception as e:
                    st.error(f"Substitution error: {e}")

            os.unlink(tmp_path)

    if st.session_state.final_df is not None:
        st.markdown("---")
        st.subheader("Building Overview")
        total_carbon = st.session_state.carbon_df["carbon_kg_co2e"].sum()
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
        c1.metric("Total Embodied Carbon", f"{total_carbon_t} tCO₂e")
        c2.metric("Carbon Intensity", f"{carbon_per_m2} kgCO₂e/m²")
        c3.metric("Circularity Grade", f"{circ_grade} ({circ_score})")
        c4.metric("Hazardous Flags", str(hazardous))

        if st.session_state.benchmark_result:
            br = st.session_state.benchmark_result
            if br["status"] == "green":
                st.success(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of {br['target_per_m2']} kgCO₂e/m²"
                )
            elif br["status"] == "amber":
                st.warning(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of {br['target_per_m2']} kgCO₂e/m²"
                )
            else:
                st.error(
                    f"Carbon Benchmark: {br['label']} — "
                    f"{br['carbon_per_m2']} kgCO₂e/m² vs "
                    f"Finnish target of {br['target_per_m2']} kgCO₂e/m²"
                )


# ============================================================
# PAGE 2 - IFC PARSER
# ============================================================
elif page == "📦 IFC Parser":
    st.title("📦 IFC Model Parser")
    st.markdown("Extracted elements, materials, volumes and storey assignments.")

    if st.session_state.ifc_df is None:
        st.warning("Please upload an IFC file on the Home page first.")
    else:
        df = st.session_state.ifc_df
        summary = get_summary(df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Elements", summary["total_elements"])
        c2.metric("Unique Materials", summary["unique_materials"])
        c3.metric("Missing Materials", summary["missing_material"])
        c4.metric("Missing Volumes", summary["missing_volume"])

        tab1, tab2, tab3 = st.tabs(
            ["All Elements", "By Type", "Missing Data Flags"]
        )

        with tab1:
            st.dataframe(df, use_container_width=True)

        with tab2:
            by_type = df["element_type"].value_counts().reset_index()
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
                f"**Missing material:** {len(missing_mat)} elements"
            )
            if not missing_mat.empty:
                st.dataframe(missing_mat, use_container_width=True)

            st.markdown(
                f"**Missing volume:** {len(missing_vol)} elements"
            )
            if not missing_vol.empty:
                st.dataframe(missing_vol, use_container_width=True)

            st.markdown(
                f"**Missing storey:** {len(missing_storey)} elements"
            )
            if not missing_storey.empty:
                st.dataframe(missing_storey, use_container_width=True)


# ============================================================
# PAGE 3 - EMBODIED CARBON
# ============================================================
elif page == "🔥 Embodied Carbon":
    st.title("🔥 Embodied Carbon Assessment")
    st.markdown(
        "Lifecycle stages A1–A3 — Product stage embodied carbon "
        "per element, material and floor. Standard: EN 15978 / "
        "EN 15804 / Ökobaudat"
    )

    if st.session_state.carbon_df is None:
        st.warning("Please upload an IFC file on the Home page first.")
    else:
        df = st.session_state.carbon_df
        total_carbon = df["carbon_kg_co2e"].sum()
        total_carbon_t = round(total_carbon / 1000, 2)
        carbon_per_m2 = round(
            total_carbon / st.session_state.floor_area, 1
        )
        unmatched = int((df["match_status"] == "unmatched").sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Carbon A1-A3", f"{total_carbon_t} tCO₂e")
        c2.metric("Carbon Intensity", f"{carbon_per_m2} kgCO₂e/m²")
        c3.metric("Total Elements", len(df))
        c4.metric("Unmatched Elements", unmatched)

        tab1, tab2, tab3, tab4 = st.tabs(
            ["By Material", "By Floor", "By Element Type", "Hotspots"]
        )

        with tab1:
            mat_carbon = (
                df.groupby("matched_material")["carbon_kg_co2e"]
                .sum()
                .reset_index()
                .sort_values("carbon_kg_co2e", ascending=False)
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
                title="Embodied Carbon by Building Storey (tCO₂e)"
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
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            st.plotly_chart(fig3, use_container_width=True)

        with tab4:
            st.subheader("Top Carbon Hotspots")
            hotspots = get_hotspots(df)
            for _, row in hotspots.iterrows():
                with st.expander(
                    f"{row['matched_material']} — "
                    f"{round(row['total_carbon']/1000, 2)} tCO₂e "
                    f"({row['carbon_pct']}% of total)"
                ):
                    h1, h2, h3 = st.columns(3)
                    h1.metric(
                        "Total Carbon",
                        f"{round(row['total_carbon']/1000, 2)} tCO₂e"
                    )
                    h2.metric(
                        "Share of Total",
                        f"{row['carbon_pct']}%"
                    )
                    h3.metric(
                        "Elements",
                        str(int(row["element_count"]))
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
        st.warning("Please upload an IFC file on the Home page first.")
    else:
        df = st.session_state.final_df
        circ_grade, circ_score = get_building_circularity_grade(df)
        hazardous = int(df["hazardous_flag"].sum())
        low_circ = get_low_circularity_flags(df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Grade", circ_grade)
        c2.metric("Overall Score", str(circ_score))
        c3.metric("Hazardous Flags", str(hazardous))
        c4.metric("Low Circularity Elements", str(len(low_circ)))

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
                    recycled_content=("recycled_content", "mean"),
                    disassembly=("disassembly", "mean"),
                    pathway=("end_of_life_pathway", "first")
                )
                .reset_index()
                .sort_values("score", ascending=False)
            )
            st.dataframe(detail, use_container_width=True)

        with tab3:
            if hazardous > 0:
                st.error(
                    f"{hazardous} hazardous material flags detected"
                )
                haz = df[df["hazardous_flag"] == True]
                st.dataframe(haz, use_container_width=True)
            else:
                st.success("No hazardous materials detected")

            if len(low_circ) > 0:
                st.warning(
                    f"{len(low_circ)} elements with low circularity "
                    f"score below 0.40"
                )
                st.dataframe(low_circ, use_container_width=True)
            else:
                st.success("No low circularity elements detected")


# ============================================================
# PAGE 5 - CARBON BENCHMARK
# ============================================================
elif page == "🎯 Carbon Benchmark":
    st.title("🎯 Carbon Budget Benchmark")
    st.markdown(
        "Comparison against Finnish Ministry of Environment carbon "
        "targets. Standard: Finnish MoE 2021 / EN 15978. "
        "Reference period: 50 years."
    )

    if st.session_state.carbon_df is None:
        st.warning("Please upload an IFC file on the Home page first.")
    else:
        br = st.session_state.benchmark_result

        if br:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Your Carbon Intensity", f"{br['carbon_per_m2']} kgCO₂e/m²")
            c2.metric("Finnish Target", f"{br['target_per_m2']} kgCO₂e/m²")
            c3.metric("Difference", f"{br['difference_per_m2']:+.1f} kgCO₂e/m²")
            c4.metric("% of Target", f"{br['percentage_of_target']}%")

            if br["status"] == "green":
                st.success(f"Status: {br['label']}")
            elif br["status"] == "amber":
                st.warning(f"Status: {br['label']}")
            else:
                st.error(f"Status: {br['label']}")

            tab1, tab2 = st.tabs(["Visual Comparison", "All Benchmarks"])

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
                        "Standard": "Finnish MoE 2021 / EN 15978"
                    }
                    for k, v in FINNISH_BENCHMARKS.items()
                ])
                st.dataframe(benchmark_df, use_container_width=True)


# ============================================================
# PAGE 6 - AI RECOMMENDATIONS
# ============================================================
elif page == "🤖 AI Recommendations":
    st.title("🤖 AI Sustainability Recommendations")
    st.markdown(
        "AI-generated recommendations based on your building's "
        "specific assessment data. Aligned with Finnish and EU "
        "sustainability standards."
    )

    if st.session_state.carbon_df is None:
        st.warning("Please upload an IFC file on the Home page first.")
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
                                "Check your ANTHROPIC_API_KEY "
                                "in the .env file."
                            )

        with tab2:
            if st.session_state.substitutions:
                for s in st.session_state.substitutions:
                    with st.expander(
                        f"#{s['rank']} — {s['current_material']} → "
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
                        st.caption(f"Standard: {s['standard']}")
            else:
                st.info("No substitution suggestions available.")


# ============================================================
# PAGE 7 - BUILDING PASSPORT
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
        st.warning("Please upload an IFC file on the Home page first.")
    else:
        circ_grade, circ_score = get_building_circularity_grade(
            st.session_state.final_df
        )

        st.subheader("Passport Summary")
        p1, p2 = st.columns(2)

        with p1:
            st.markdown("**Building Identity**")
            st.write(f"Project: {st.session_state.project_name}")
            st.write(f"Location: {st.session_state.project_location}")
            st.write(f"Type: {st.session_state.building_type}")
            st.write(f"Floor area: {st.session_state.floor_area} m²")

        with p2:
            st.markdown("**Sustainability Summary**")
            total_carbon_t = round(
                st.session_state.carbon_df["carbon_kg_co2e"].sum() / 1000,
                2
            )
            st.write(f"Total carbon: {total_carbon_t} tCO₂e")
            st.write(
                f"Circularity grade: {circ_grade} ({circ_score})"
            )
            if st.session_state.benchmark_result:
                st.write(
                    f"Benchmark: "
                    f"{st.session_state.benchmark_result['label']}"
                )

        st.markdown("---")
        st.subheader("Generate and Download Passport")

        if st.button("Generate Building Passport PDF", type="primary"):
            with st.spinner("Generating PDF passport..."):
                try:
                    output_path = os.path.join(
                        tempfile.gettempdir(),
                        "greenbim_passport.pdf"
                    )
                    generate_passport(
                        output_path=output_path,
                        project_name=st.session_state.project_name,
                        project_location=st.session_state.project_location,
                        building_type=st.session_state.building_type,
                        floor_area=st.session_state.floor_area,
                        carbon_df=st.session_state.carbon_df,
                        final_df=st.session_state.final_df,
                        benchmark_result=st.session_state.benchmark_result,
                        substitutions=st.session_state.substitutions or [],
                        ai_recommendations=st.session_state.ai_recommendations or "Not generated yet.",
                        circularity_grade=circ_grade,
                        circularity_score=circ_score
                    )
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Download Building Passport PDF",
                            data=f,
                            file_name=f"GreenBIM_Passport_{st.session_state.project_name}.pdf",
                            mime="application/pdf"
                        )
                    st.success("Passport generated successfully.")
                except Exception as e:
                    st.error(f"PDF generation error: {e}")