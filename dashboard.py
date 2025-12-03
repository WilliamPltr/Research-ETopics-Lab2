import os
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Steel Plants Dashboard", layout="wide")
st.title("Steel Plants Dashboard")
st.write("Explore plants, capacity, and geography. Use the sidebar to filter.")


# --- Data loading ---
@st.cache_data(show_spinner=False)
def load_data():
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Clean column names
        df.columns = [c.strip() for c in df.columns]

        # Drop leading unnamed/index column if present
        if len(df.columns) and (
            df.columns[0] == "" or df.columns[0].lower().startswith("unnamed")
        ):
            df = df.drop(columns=[df.columns[0]])

        # Normalize latitude/longitude (your CSV has "Latitude"/"Longitude")
        if "Latitude" in df.columns and "latitude" not in df.columns:
            df = df.rename(columns={"Latitude": "latitude"})
        if "Longitude" in df.columns and "longitude" not in df.columns:
            df = df.rename(columns={"Longitude": "longitude"})

        # If only "Coordinates" exists (e.g., "41.09, 20.02"), extract lat/lon
        if "Coordinates" in df.columns and (
            ("latitude" not in df.columns) or ("longitude" not in df.columns)
        ):

            def _extract_lat_lon(value):
                if pd.isna(value):
                    return pd.NA, pd.NA
                if isinstance(value, str) and "," in value:
                    parts = value.split(",")
                    if len(parts) == 2:
                        try:
                            return float(parts[0].strip()), float(parts[1].strip())
                        except Exception:
                            return pd.NA, pd.NA
                return pd.NA, pd.NA

            latlon = df["Coordinates"].apply(_extract_lat_lon)
            if "latitude" not in df.columns:
                df["latitude"] = latlon.apply(lambda t: t[0])
            if "longitude" not in df.columns:
                df["longitude"] = latlon.apply(lambda t: t[1])

        # Build "Total capacity (ttpa)" by summing any *capacity* columns
        cap_cols = [c for c in df.columns if "capacity" in c.lower()]
        if cap_cols:
            df["Total capacity (ttpa)"] = (
                df[cap_cols]
                .apply(pd.to_numeric, errors="coerce")
                .sum(axis=1, min_count=1)
            )

        return df

    def _aggregate_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        # Prefer Plant ID as the grouping key
        if "Plant ID" in df.columns:
            key = ["Plant ID"]
        else:
            key = [
                c
                for c in [
                    "Plant name (English)",
                    "Owner",
                    "latitude",
                    "longitude",
                    "Country/Area",
                ]
                if c in df.columns
            ] or [df.columns[0]]

        # Numeric columns to sum (capacity family); workforce = max
        numeric_sum = []
        if "Total capacity (ttpa)" in df.columns:
            numeric_sum.append("Total capacity (ttpa)")
        numeric_sum += [
            c
            for c in df.columns
            if ("capacity" in c.lower()) and c != "Total capacity (ttpa)"
        ]

        agg = {c: "first" for c in df.columns if c not in key}
        for c in numeric_sum:
            agg[c] = "sum"
        if "Workforce size" in df.columns:
            agg["Workforce size"] = "max"

        # Keep first non-null for key text fields
        for c in [
            "Plant name (English)",
            "Owner",
            "Location address",
            "Country/Area",
            "Region",
            "Coordinates",
            "Announced date",
            "Start date",
            "latitude",
            "longitude",
        ]:
            if c in agg:
                agg[c] = "first"

        return df.groupby(key, dropna=False, as_index=False).agg(agg)

    # Load only plants_processed.csv
    if not os.path.exists("plants_processed.csv"):
        raise FileNotFoundError(
            "plants_processed.csv not found. Please place the file next to the app."
        )

    df = pd.read_csv("plants_processed.csv")
    df = _standardize_columns(df)
    df = _aggregate_duplicates(df)
    return df


df = load_data()
if df.empty:
    st.stop()

# --- Sidebar filters ---
st.sidebar.header("Filters")
company_col = "Owner" if "Owner" in df.columns else None
region_col = "Region" if "Region" in df.columns else None
country_col = (
    "Country/Area" if "Country/Area" in df.columns else None
)  # ← this was the broken line
capacity_col = (
    "Total capacity (ttpa)" if "Total capacity (ttpa)" in df.columns else None
)

if company_col:
    companies = sorted(df[company_col].dropna().unique().tolist())
    selected_companies = st.sidebar.multiselect("Company", companies)
else:
    selected_companies = []

if region_col:
    regions = sorted(df[region_col].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect("Region", regions)
else:
    selected_regions = []

if country_col:
    countries = sorted(df[country_col].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Country", countries)
else:
    selected_countries = []

if capacity_col and df[capacity_col].notna().any():
    cap_series = pd.to_numeric(df[capacity_col], errors="coerce")
    cmin = float(cap_series.min())
    cmax = float(cap_series.max())
    cap_range = st.sidebar.slider(
        "Capacity range (ttpa)",
        min_value=0.0,
        max_value=max(cmax, 0.0),
        value=(max(cmin, 0.0), max(cmax, 0.0)),
    )
else:
    cap_range = None

# --- Apply filters ---
f = df.copy()
if selected_companies and company_col:
    f = f[f[company_col].isin(selected_companies)]
if selected_regions and region_col:
    f = f[f[region_col].isin(selected_regions)]
if selected_countries and country_col:
    f = f[f[country_col].isin(selected_countries)]
if cap_range and capacity_col:
    lo, hi = cap_range
    f = f[pd.to_numeric(f[capacity_col], errors="coerce").between(lo, hi)]

# --- KPIs ---
left, mid, right = st.columns(3)
with left:
    st.metric("Total plants", value=int(len(f)))
with mid:
    total_cap = (
        pd.to_numeric(f[capacity_col], errors="coerce").sum() if capacity_col else 0
    )
    st.metric("Total capacity (ttpa)", value=f"{total_cap:,.0f}")
with right:
    n_companies = f[company_col].nunique(dropna=True) if company_col else 0
    st.metric("Distinct companies", value=int(n_companies))

# --- Map ---
latlon_available = {"latitude", "longitude"}.issubset(f.columns)
if latlon_available and f[["latitude", "longitude"]].notna().any().any():
    color_by = region_col or country_col or company_col
    fig = px.scatter_geo(
        f.dropna(subset=["latitude", "longitude"]),
        lat="latitude",
        lon="longitude",
        color=color_by if color_by in f.columns else None,
        size=capacity_col if capacity_col in f.columns else None,
        hover_name="Plant name (English)"
        if "Plant name (English)" in f.columns
        else None,
        hover_data=[
            c for c in [company_col, country_col, region_col] if c and c in f.columns
        ],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No coordinates available to render the map.")

# --- Data table ---
st.subheader("Plant data")
st.dataframe(f, use_container_width=True)

# --- Footer ---
st.caption(
    "Data source: Global Iron and Steel Tracker (GEM). This dashboard is for educational purposes."
)
