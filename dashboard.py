import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Global Seismic Trends",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background: #f5f7fb;
    }

    /* Main title */
    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #64748b;
        margin-bottom: 25px;
    }

    /* KPI cards */
    .kpi-card {
        background: white;
        padding: 22px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        min-height: 125px;
    }

    .kpi-title {
        color: #64748b;
        font-size: 15px;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        margin-top: 8px;
        color: #0f172a;
    }

    .section-title {
        font-size: 23px;
        font-weight: 750;
        margin-top: 15px;
        margin-bottom: 8px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff;
    }

    /* Download button */
    .download-btn {
        margin-top: 10px;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    data = pd.read_excel("25 Days-xls.xlsx")

    # Clean column names
    data.columns = (
        data.columns
        .str.strip()
        .str.lower()
    )

    # Numeric columns
    numeric_columns = [
        "latitude",
        "longitude",
        "depth",
        "mag"
    ]

    for col in numeric_columns:

        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

    # Date/time
    if "time" in data.columns:

        data["time"] = pd.to_datetime(
            data["time"],
            errors="coerce",
            utc=True
        )

        data["event_date"] = data["time"].dt.date

    # Missing values
    if "magtype" in data.columns:
        data["magtype"] = (
            data["magtype"]
            .fillna("Unknown")
            .astype(str)
        )

    if "place" in data.columns:
        data["place"] = (
            data["place"]
            .fillna("Unknown")
            .astype(str)
        )

    return data


try:

    df = load_data()

except Exception as e:

    st.error("Unable to load the Excel file.")
    st.exception(e)
    st.stop()


# =========================================================
# CHECK REQUIRED COLUMNS
# =========================================================

required_columns = [
    "latitude",
    "longitude",
    "depth",
    "mag"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"Missing columns in Excel file: {missing_columns}"
    )

    st.write("Available columns:")
    st.write(df.columns.tolist())

    st.stop()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🌍 Global Seismic Trends</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Interactive Earthquake Monitoring & Analysis Dashboard'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🎛️ Dashboard Filters")

st.sidebar.markdown(
    "Use the filters below to explore the earthquake dataset."
)


# -----------------------------
# Magnitude filter
# -----------------------------

min_mag = float(df["mag"].min())
max_mag = float(df["mag"].max())

selected_mag = st.sidebar.slider(
    "🌋 Magnitude Range",
    min_value=min_mag,
    max_value=max_mag,
    value=(min_mag, max_mag),
    step=0.1
)


# -----------------------------
# Depth filter
# -----------------------------

min_depth = float(df["depth"].min())
max_depth = float(df["depth"].max())

selected_depth = st.sidebar.slider(
    "📏 Depth Range (km)",
    min_value=min_depth,
    max_value=max_depth,
    value=(min_depth, max_depth),
    step=1.0
)


# -----------------------------
# Magnitude type
# -----------------------------

if "magtype" in df.columns:

    available_magtypes = sorted(
        df["magtype"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_magtypes = st.sidebar.multiselect(
        "📡 Magnitude Type",
        options=available_magtypes,
        default=available_magtypes
    )

else:

    selected_magtypes = []


# -----------------------------
# Date filter
# -----------------------------

if "event_date" in df.columns:

    valid_dates = df["event_date"].dropna()

    if len(valid_dates) > 0:

        min_date = min(valid_dates)
        max_date = max(valid_dates)

        selected_dates = st.sidebar.date_input(
            "📅 Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        # Handle single date selection
        if isinstance(selected_dates, tuple):

            if len(selected_dates) == 2:
                start_date = selected_dates[0]
                end_date = selected_dates[1]

            else:
                start_date = min_date
                end_date = max_date

        else:

            start_date = selected_dates
            end_date = selected_dates

    else:

        start_date = None
        end_date = None

else:

    start_date = None
    end_date = None


# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()


# Magnitude
filtered_df = filtered_df[
    (filtered_df["mag"] >= selected_mag[0]) &
    (filtered_df["mag"] <= selected_mag[1])
]


# Depth
filtered_df = filtered_df[
    (filtered_df["depth"] >= selected_depth[0]) &
    (filtered_df["depth"] <= selected_depth[1])
]


# Magnitude type
if "magtype" in filtered_df.columns:

    filtered_df = filtered_df[
        filtered_df["magtype"].isin(selected_magtypes)
    ]


# Date
if (
    start_date is not None
    and end_date is not None
    and "event_date" in filtered_df.columns
):

    filtered_df = filtered_df[
        (filtered_df["event_date"] >= start_date) &
        (filtered_df["event_date"] <= end_date)
    ]


# =========================================================
# KPI CALCULATIONS
# =========================================================

total_earthquakes = len(filtered_df)


if total_earthquakes > 0:

    average_magnitude = filtered_df["mag"].mean()

    maximum_magnitude = filtered_df["mag"].max()

    minimum_magnitude = filtered_df["mag"].min()

    average_depth = filtered_df["depth"].mean()

else:

    average_magnitude = 0
    maximum_magnitude = 0
    minimum_magnitude = 0
    average_depth = 0


# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4 = st.columns(4)


with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">🌎 Total Earthquakes</div>
            <div class="kpi-value">{total_earthquakes}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">📊 Average Magnitude</div>
            <div class="kpi-value">{average_magnitude:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">⚡ Maximum Magnitude</div>
            <div class="kpi-value">{maximum_magnitude:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">🌋 Average Depth</div>
            <div class="kpi-value">{average_depth:.2f} km</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# =========================================================
# FILTER SUMMARY
# =========================================================

st.info(
    f"Showing **{total_earthquakes}** earthquake records "
    f"from the selected filters."
)


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🌍 Global Map",
        "📊 Analytics",
        "📈 Trends",
        "📋 Data"
    ]
)


# =========================================================
# TAB 1 — GLOBAL MAP
# =========================================================

with tab1:

    st.markdown(
        '<div class="section-title">'
        '🌍 Global Earthquake Locations'
        '</div>',
        unsafe_allow_html=True
    )

    map_df = filtered_df.dropna(
        subset=[
            "latitude",
            "longitude",
            "mag"
        ]
    )

    if len(map_df) > 0:

        fig_map = px.scatter_geo(
            map_df,
            lat="latitude",
            lon="longitude",
            size="mag",
            color="mag",
            hover_name="place"
            if "place" in map_df.columns
            else None,
            hover_data={
                "latitude": ":.2f",
                "longitude": ":.2f",
                "mag": ":.2f",
                "depth": ":.2f",
            },
            projection="natural earth",
            color_continuous_scale="Turbo",
            size_max=28,
            title="Earthquake Distribution Across the Globe"
        )

        fig_map.update_geos(
            showland=True,
            showcountries=True,
            showocean=True,
            coastlinecolor="gray"
        )

        fig_map.update_layout(
            height=650,
            margin=dict(
                l=0,
                r=0,
                t=60,
                b=0
            )
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True
        )

    else:

        st.warning(
            "No earthquake locations match the selected filters."
        )


# =========================================================
# TAB 2 — ANALYTICS
# =========================================================

with tab2:

    # -----------------------------
    # Magnitude Distribution
    # -----------------------------

    left, right = st.columns(2)


    with left:

        st.markdown(
            '<div class="section-title">'
            '📊 Magnitude Distribution'
            '</div>',
            unsafe_allow_html=True
        )

        if len(filtered_df) > 0:

            fig_mag = px.histogram(
                filtered_df,
                x="mag",
                nbins=10,
                title="Earthquakes by Magnitude",
                labels={
                    "mag": "Magnitude",
                    "count": "Number of Earthquakes"
                }
            )

            fig_mag.update_layout(
                height=420,
                bargap=0.08
            )

            st.plotly_chart(
                fig_mag,
                use_container_width=True
            )


    # -----------------------------
    # Depth vs Magnitude
    # -----------------------------

    with right:

        st.markdown(
            '<div class="section-title">'
            '📈 Magnitude vs Depth'
            '</div>',
            unsafe_allow_html=True
        )

        if len(filtered_df) > 0:

            fig_depth = px.scatter(
                filtered_df,
                x="depth",
                y="mag",
                size="mag",
                color="mag",
                hover_name="place"
                if "place" in filtered_df.columns
                else None,
                color_continuous_scale="Turbo",
                title="Magnitude vs Earthquake Depth",
                labels={
                    "depth": "Depth (km)",
                    "mag": "Magnitude"
                }
            )

            fig_depth.update_layout(
                height=420
            )

            st.plotly_chart(
                fig_depth,
                use_container_width=True
            )


    # -----------------------------
    # Magnitude Type
    # -----------------------------

    st.markdown(
        '<div class="section-title">'
        '📡 Magnitude Type Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    if len(filtered_df) > 0 and "magtype" in filtered_df.columns:

        type_count = (
            filtered_df["magtype"]
            .value_counts()
            .reset_index()
        )

        type_count.columns = [
            "Magnitude Type",
            "Count"
        ]

        fig_type = px.bar(
            type_count,
            x="Magnitude Type",
            y="Count",
            text="Count",
            title="Earthquakes by Magnitude Measurement Type"
        )

        fig_type.update_traces(
            textposition="outside"
        )

        fig_type.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_type,
            use_container_width=True
        )


# =========================================================
# TAB 3 — TRENDS
# =========================================================

with tab3:

    st.markdown(
        '<div class="section-title">'
        '📅 Earthquake Activity Over Time'
        '</div>',
        unsafe_allow_html=True
    )

    if (
        "event_date" in filtered_df.columns
        and filtered_df["event_date"].notna().any()
    ):

        daily_count = (
            filtered_df
            .dropna(subset=["event_date"])
            .groupby("event_date")
            .size()
            .reset_index(name="earthquakes")
        )

        daily_count["event_date"] = pd.to_datetime(
            daily_count["event_date"]
        )

        fig_trend = px.line(
            daily_count,
            x="event_date",
            y="earthquakes",
            markers=True,
            title="Daily Earthquake Count",
            labels={
                "event_date": "Date",
                "earthquakes": "Earthquakes"
            }
        )

        fig_trend.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_trend,
            use_container_width=True
        )


        # -----------------------------
        # Average magnitude by day
        # -----------------------------

        daily_mag = (
            filtered_df
            .dropna(subset=["event_date"])
            .groupby("event_date")["mag"]
            .mean()
            .reset_index()
        )

        daily_mag["event_date"] = pd.to_datetime(
            daily_mag["event_date"]
        )

        fig_daily_mag = px.line(
            daily_mag,
            x="event_date",
            y="mag",
            markers=True,
            title="Average Magnitude by Day",
            labels={
                "event_date": "Date",
                "mag": "Average Magnitude"
            }
        )

        fig_daily_mag.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_daily_mag,
            use_container_width=True
        )

    else:

        st.info(
            "Date information is not available for trend analysis."
        )


# =========================================================
# TAB 4 — DATA
# =========================================================

with tab4:

    st.markdown(
        '<div class="section-title">'
        '📋 Earthquake Records'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Displaying **{len(filtered_df)}** filtered records."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # DOWNLOAD
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '📥 Download Data'
        '</div>',
        unsafe_allow_html=True
    )

    csv_data = filtered_df.to_csv(
        index=False
    )

    st.download_button(
        label="⬇️ Download Filtered CSV",
        data=csv_data,
        file_name="filtered_earthquake_data.csv",
        mime="text/csv"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🌍 Global Seismic Trends | "
    "Interactive Earthquake Analysis Dashboard"
)


