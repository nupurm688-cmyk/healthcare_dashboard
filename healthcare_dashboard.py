"""
Healthcare Analytics Dashboard
--------------------------------
A Streamlit app for exploring patient-level healthcare data.

Run with:
    streamlit run healthcare_dashboard.py

Expected CSV columns (case-insensitive, flexible naming handled below):
    - age
    - gender / sex
    - disease / diagnosis / condition
    - bmi (or height + weight to compute it)
    - height (cm) [optional, used if bmi missing]
    - weight (kg) [optional, used if bmi missing]
    - systolic_bp / bp_systolic
    - diastolic_bp / bp_diastolic
    - patient_id [optional]
"""

import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
COLUMN_ALIASES = {
    "age": ["age", "patient_age", "years"],
    "gender": ["gender", "sex"],
    "disease": ["disease", "diagnosis", "condition", "disease_name"],
    "bmi": ["bmi", "body_mass_index"],
    "height": ["height", "height_cm", "height(cm)"],
    "weight": ["weight", "weight_kg", "weight(kg)"],
    "systolic": ["systolic_bp", "bp_systolic", "systolic", "sbp"],
    "diastolic": ["diastolic_bp", "bp_diastolic", "diastolic", "dbp"],
    "patient_id": ["patient_id", "id", "patientid"],
}


def find_column(df, keys):
    """Find the first matching column (case-insensitive) for a list of alias keys."""
    lower_map = {c.lower().strip(): c for c in df.columns}
    for key in keys:
        if key in lower_map:
            return lower_map[key]
    return None


def standardize_columns(df):
    """Map real dataframe columns to standardized internal names where possible."""
    mapping = {}
    for std_name, aliases in COLUMN_ALIASES.items():
        col = find_column(df, aliases)
        if col:
            mapping[std_name] = col
    return mapping


def bmi_category(bmi):
    if pd.isna(bmi):
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def bp_category(systolic, diastolic):
    if pd.isna(systolic) or pd.isna(diastolic):
        return "Unknown"
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated"
    elif systolic < 140 or diastolic < 90:
        return "Hypertension Stage 1"
    elif systolic < 180 or diastolic < 120:
        return "Hypertension Stage 2"
    else:
        return "Hypertensive Crisis"


def age_group(age):
    if pd.isna(age):
        return "Unknown"
    age = int(age)
    if age < 18:
        return "0-17"
    elif age < 30:
        return "18-29"
    elif age < 45:
        return "30-44"
    elif age < 60:
        return "45-59"
    elif age < 75:
        return "60-74"
    else:
        return "75+"


@st.cache_data
def load_sample_data(n=500):
    rng = np.random.default_rng(42)
    diseases = [
        "Hypertension", "Diabetes", "Asthma", "Cardiovascular Disease",
        "Obesity", "Arthritis", "None", "Chronic Kidney Disease",
    ]
    genders = ["Male", "Female", "Other"]

    age = rng.integers(1, 95, n)
    gender = rng.choice(genders, n, p=[0.48, 0.48, 0.04])
    disease = rng.choice(diseases, n, p=[0.18, 0.15, 0.1, 0.12, 0.15, 0.1, 0.15, 0.05])
    height = rng.normal(168, 10, n).clip(140, 200)
    weight = rng.normal(72, 15, n).clip(35, 160)
    bmi = weight / ((height / 100) ** 2)
    systolic = rng.normal(125, 18, n).clip(85, 200).round(0)
    diastolic = rng.normal(80, 12, n).clip(50, 130).round(0)

    df = pd.DataFrame({
        "patient_id": [f"P{1000+i}" for i in range(n)],
        "age": age,
        "gender": gender,
        "disease": disease,
        "height": height.round(1),
        "weight": weight.round(1),
        "bmi": bmi.round(1),
        "systolic_bp": systolic,
        "diastolic_bp": diastolic,
    })
    return df


def process_dataframe(df):
    """Standardize, derive missing fields, and add category columns."""
    mapping = standardize_columns(df)
    work = pd.DataFrame(index=df.index)

    for std_name in ["patient_id", "age", "gender", "disease", "bmi",
                      "height", "weight", "systolic", "diastolic"]:
        if std_name in mapping:
            work[std_name] = df[mapping[std_name]]

    # numeric coercion
    for col in ["age", "bmi", "height", "weight", "systolic", "diastolic"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")

    # derive BMI if missing but height & weight present
    if "bmi" not in work.columns and {"height", "weight"}.issubset(work.columns):
        h_m = work["height"] / 100.0
        work["bmi"] = (work["weight"] / (h_m ** 2)).round(1)

    if "gender" in work.columns:
        work["gender"] = work["gender"].astype(str).str.strip().str.title()

    if "disease" in work.columns:
        work["disease"] = work["disease"].astype(str).str.strip().str.title()

    if "age" in work.columns:
        work["age_group"] = work["age"].apply(age_group)

    if "bmi" in work.columns:
        work["bmi_category"] = work["bmi"].apply(bmi_category)

    if {"systolic", "diastolic"}.issubset(work.columns):
        work["bp_category"] = work.apply(
            lambda r: bp_category(r["systolic"], r["diastolic"]), axis=1
        )

    return work, mapping


# ----------------------------------------------------------------------------
# Sidebar — Data Upload
# ----------------------------------------------------------------------------
st.sidebar.title("🩺 Healthcare Dashboard")
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Patient Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload patient CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    help="File should include columns like age, gender, disease, bmi, blood pressure, etc.",
)

use_sample = st.sidebar.checkbox("Use sample demo data", value=uploaded_file is None)

raw_df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
        st.sidebar.success(f"Loaded {len(raw_df)} records from {uploaded_file.name}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

if raw_df is None and use_sample:
    raw_df = load_sample_data()
    st.sidebar.info("Using generated sample dataset (500 patients).")

if raw_df is None:
    st.title("🩺 Healthcare Analytics Dashboard")
    st.info("👈 Upload a patient data file from the sidebar, or check 'Use sample demo data' to explore the dashboard.")
    st.stop()

df, colmap = process_dataframe(raw_df)

with st.sidebar.expander("🔎 Detected column mapping"):
    if colmap:
        for std, real in colmap.items():
            st.write(f"**{std}** → `{real}`")
    else:
        st.write("No recognizable columns found.")

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")

filtered = df.copy()

if "gender" in df.columns:
    genders = sorted(df["gender"].dropna().unique().tolist())
    selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)
    filtered = filtered[filtered["gender"].isin(selected_genders)]

if "disease" in df.columns:
    diseases = sorted(df["disease"].dropna().unique().tolist())
    selected_diseases = st.sidebar.multiselect("Disease / Condition", diseases, default=diseases)
    filtered = filtered[filtered["disease"].isin(selected_diseases)]

if "age" in df.columns and df["age"].notna().any():
    min_age, max_age = int(df["age"].min()), int(df["age"].max())
    age_range = st.sidebar.slider("Age range", min_age, max_age, (min_age, max_age))
    filtered = filtered[(filtered["age"] >= age_range[0]) & (filtered["age"] <= age_range[1])]

if filtered.empty:
    st.warning("No records match the current filters. Adjust filters in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------------
# Header + KPI Cards
# ----------------------------------------------------------------------------
st.title("🩺 Healthcare Analytics Dashboard")
st.caption("Interactive overview of patient demographics, conditions, and vitals.")

st.markdown("### 📊 Key Performance Indicators")

kpi_cols = st.columns(5)

total_patients = len(filtered)
avg_age = filtered["age"].mean() if "age" in filtered.columns else np.nan
avg_bmi = filtered["bmi"].mean() if "bmi" in filtered.columns else np.nan
avg_sys = filtered["systolic"].mean() if "systolic" in filtered.columns else np.nan
avg_dia = filtered["diastolic"].mean() if "diastolic" in filtered.columns else np.nan

if "disease" in filtered.columns:
    non_healthy = filtered[~filtered["disease"].isin(["None", "Nan", "N/A", ""])]
    pct_with_condition = 100 * len(non_healthy) / total_patients if total_patients else 0
else:
    pct_with_condition = np.nan

with kpi_cols[0]:
    st.metric("Total Patients", f"{total_patients:,}")
with kpi_cols[1]:
    st.metric("Average Age", f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "N/A")
with kpi_cols[2]:
    st.metric("Average BMI", f"{avg_bmi:.1f}" if pd.notna(avg_bmi) else "N/A")
with kpi_cols[3]:
    bp_str = f"{avg_sys:.0f}/{avg_dia:.0f}" if pd.notna(avg_sys) and pd.notna(avg_dia) else "N/A"
    st.metric("Avg Blood Pressure", bp_str)
with kpi_cols[4]:
    st.metric("% With a Condition", f"{pct_with_condition:.1f}%" if pd.notna(pct_with_condition) else "N/A")

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 1: Age Distribution + Gender Analysis
# ----------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("👥 Age Distribution")
    if "age" in filtered.columns:
        fig = px.histogram(
            filtered, x="age", nbins=20,
            color_discrete_sequence=["#2E86AB"],
            labels={"age": "Age"},
        )
        fig.update_layout(bargap=0.05, yaxis_title="Number of Patients")
        st.plotly_chart(fig, use_container_width=True)

        if "age_group" in filtered.columns:
            age_grp_counts = filtered["age_group"].value_counts().reindex(
                ["0-17", "18-29", "30-44", "45-59", "60-74", "75+"]
            ).dropna()
            fig2 = px.bar(
                age_grp_counts, x=age_grp_counts.index, y=age_grp_counts.values,
                labels={"x": "Age Group", "y": "Patients"},
                color=age_grp_counts.values, color_continuous_scale="Blues",
            )
            fig2.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No age column found in data.")

with row1_col2:
    st.subheader("⚧ Gender Analysis")
    if "gender" in filtered.columns:
        gender_counts = filtered["gender"].value_counts()
        fig = px.pie(
            gender_counts, names=gender_counts.index, values=gender_counts.values,
            hole=0.45, color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

        if "age" in filtered.columns:
            fig2 = px.box(
                filtered, x="gender", y="age", color="gender",
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={"age": "Age", "gender": "Gender"},
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No gender column found in data.")

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 2: Disease Distribution
# ----------------------------------------------------------------------------
st.subheader("🦠 Disease Distribution")
if "disease" in filtered.columns:
    dcol1, dcol2 = st.columns([1.3, 1])

    disease_counts = filtered["disease"].value_counts()

    with dcol1:
        fig = px.bar(
            disease_counts, x=disease_counts.values, y=disease_counts.index,
            orientation="h",
            labels={"x": "Number of Patients", "y": "Disease / Condition"},
            color=disease_counts.values, color_continuous_scale="Teal",
        )
        fig.update_layout(coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with dcol2:
        fig2 = px.pie(
            disease_counts, names=disease_counts.index, values=disease_counts.values,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_traces(textinfo="percent")
        st.plotly_chart(fig2, use_container_width=True)

    if "gender" in filtered.columns:
        st.markdown("**Disease by Gender**")
        cross = pd.crosstab(filtered["disease"], filtered["gender"])
        fig3 = px.bar(cross, barmode="group", labels={"value": "Patients", "disease": "Disease"})
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No disease/condition column found in data.")

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 3: BMI Analysis
# ----------------------------------------------------------------------------
st.subheader("⚖️ BMI Analysis")
if "bmi" in filtered.columns:
    bcol1, bcol2 = st.columns(2)

    with bcol1:
        fig = px.histogram(
            filtered, x="bmi", nbins=25, color_discrete_sequence=["#F18F01"],
            labels={"bmi": "BMI"},
        )
        fig.add_vline(x=18.5, line_dash="dash", line_color="gray")
        fig.add_vline(x=25, line_dash="dash", line_color="gray")
        fig.add_vline(x=30, line_dash="dash", line_color="gray")
        fig.update_layout(yaxis_title="Number of Patients")
        st.plotly_chart(fig, use_container_width=True)

    with bcol2:
        bmi_cat_counts = filtered["bmi_category"].value_counts().reindex(
            ["Underweight", "Normal", "Overweight", "Obese"]
        ).dropna()
        fig2 = px.pie(
            bmi_cat_counts, names=bmi_cat_counts.index, values=bmi_cat_counts.values,
            color=bmi_cat_counts.index,
            color_discrete_map={
                "Underweight": "#89CFF0", "Normal": "#90EE90",
                "Overweight": "#FFD580", "Obese": "#FF6961",
            },
            hole=0.4,
        )
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    if "gender" in filtered.columns:
        fig3 = px.violin(
            filtered, x="gender", y="bmi", color="gender", box=True, points="outliers",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"bmi": "BMI", "gender": "Gender"},
        )
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No BMI (or height/weight) columns found in data.")

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 4: Blood Pressure Analysis
# ----------------------------------------------------------------------------
st.subheader("❤️ Blood Pressure Analysis")
if {"systolic", "diastolic"}.issubset(filtered.columns):
    pcol1, pcol2 = st.columns(2)

    with pcol1:
        fig = px.scatter(
            filtered, x="systolic", y="diastolic",
            color="bp_category" if "bp_category" in filtered.columns else None,
            labels={"systolic": "Systolic (mmHg)", "diastolic": "Diastolic (mmHg)"},
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        st.plotly_chart(fig, use_container_width=True)

    with pcol2:
        if "bp_category" in filtered.columns:
            bp_counts = filtered["bp_category"].value_counts().reindex(
                ["Normal", "Elevated", "Hypertension Stage 1",
                 "Hypertension Stage 2", "Hypertensive Crisis"]
            ).dropna()
            fig2 = px.bar(
                bp_counts, x=bp_counts.index, y=bp_counts.values,
                color=bp_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={"x": "BP Category", "y": "Patients"},
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Average Systolic vs Diastolic Over Age Groups**")
    if "age_group" in filtered.columns:
        bp_by_age = filtered.groupby("age_group")[["systolic", "diastolic"]].mean().reindex(
            ["0-17", "18-29", "30-44", "45-59", "60-74", "75+"]
        ).dropna()
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=bp_by_age.index, y=bp_by_age["systolic"],
                                   mode="lines+markers", name="Systolic"))
        fig3.add_trace(go.Scatter(x=bp_by_age.index, y=bp_by_age["diastolic"],
                                   mode="lines+markers", name="Diastolic"))
        fig3.update_layout(xaxis_title="Age Group", yaxis_title="mmHg")
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No blood pressure columns found in data.")

st.markdown("---")

# ----------------------------------------------------------------------------
# Raw Data Table
# ----------------------------------------------------------------------------
with st.expander("📄 View Filtered Patient Data Table"):
    st.dataframe(filtered, use_container_width=True)
    csv_buffer = io.StringIO()
    filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=csv_buffer.getvalue(),
        file_name="filtered_patient_data.csv",
        mime="text/csv",
    )

st.caption("Built with Streamlit · For demonstration/analytics purposes only, not a substitute for clinical judgment.")
