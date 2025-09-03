# streamlit_dashboard_mvp.py
# Streamlit dashboard tailored to tuesday_mvp.csv dataset

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Company Addresses Dashboard",
    page_icon="🏢",
    layout="wide",
)

# -----------------------------
# Data loading
# -----------------------------
@st.cache_data
def load_data(path: str = "final_mvp_latest.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


# -----------------------------
# KPI block
# -----------------------------
def kpi_block(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Addresses", f"{len(df):,}")
    c2.metric("Total Companies", f"{df['Companies_at_Address'].sum():,}")
    c3.metric("Avg Companies per Address", f"{df['Companies_at_Address'].mean():.1f}")
    c4.metric("Max Companies at One Address", f"{df['Companies_at_Address'].max():,}")


# -----------------------------
# Sidebar filters
# -----------------------------
def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    postcodes = st.sidebar.multiselect(
        "Postcodes",
        options=sorted(df["PostCode_clean"].unique()),
        default=sorted(df["PostCode_clean"].unique())[:10],
    )

    ranks = st.sidebar.slider(
        "Rank range",
        int(df["rank"].min()),
        int(df["rank"].max()),
        (int(df["rank"].min()), int(df["rank"].max())),
    )

    fdf = df[df["PostCode_clean"].isin(postcodes)]
    fdf = fdf[fdf["rank"].between(ranks[0], ranks[1])]

    st.sidebar.write(f"**Filtered rows:** {len(fdf):,}")

    st.sidebar.download_button(
        label="Download filtered CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="mvp_filtered.csv",
        mime="text/csv",
    )

    return fdf


# -----------------------------
# Plot sections
# -----------------------------

def plot_plotly(df: pd.DataFrame):
    st.subheader("Companies per Address by Postcode")
    fig = px.scatter(
        df,
        x="rank",
        y="Companies_at_Address",
        color="PostCode_clean",
        size="Companies_at_Address",
        hover_data=["Address_street", "Companies_in_Postcode"],
        height=500,
        labels={"rank": "Address Rank", "Companies_at_Address": "Companies at Address"},
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_seaborn(df: pd.DataFrame):
    st.subheader("Top Addresses with Most Companies")
    top_addresses = df.nlargest(15, "Companies_at_Address")[["Address_street", "PostCode_clean", "Companies_at_Address"]]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top_addresses)), top_addresses["Companies_at_Address"].values)
    ax.set_yticks(range(len(top_addresses)))
    ax.set_yticklabels([f"{row['Address_street'][:30]}... ({row['PostCode_clean']})" 
                        for _, row in top_addresses.iterrows()])
    ax.set_xlabel("Number of Companies")
    ax.set_title("Top 15 Addresses by Company Count")
    
    # Add value labels on bars
    for bar, val in zip(bars, top_addresses["Companies_at_Address"].values):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val), 
                va='center', fontsize=8)
    
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)
    return



def plot_matplotlib(df: pd.DataFrame):
    st.subheader("Distribution Analysis")
    metric = st.selectbox(
        "Select metric",
        ["Companies_at_Address", "Companies_in_Postcode", "Address_share_in_PC"],
        index=0,
    )
    bins = st.slider("Bins", min_value=10, max_value=60, value=30, step=5)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df[metric], bins=bins, alpha=0.85)
    ax.set_xlabel(metric.replace("_", " ").title())
    ax.set_ylabel("Count")
    ax.set_title(f"Histogram of {metric.replace('_', ' ').title()}")
    st.pyplot(fig, clear_figure=True)


# -----------------------------
# Main app
# -----------------------------

def main():
    st.title("🏢 Company Addresses Dashboard")
    st.caption("Insights into companies per address and related metrics.")

    df = load_data()
    fdf = sidebar_filters(df)

    # KPIs
    kpi_block(fdf)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Data", "Plotly", "Seaborn", "Matplotlib"])

    with tab1:
        st.subheader("Data Snapshot")
        st.dataframe(fdf.head(200), use_container_width=True)
        st.markdown("**Grouped by postcode (mean)**")
        grouped = fdf.groupby("PostCode_clean").agg({
            "Companies_at_Address": ["mean", "max", "count"],
            "Companies_in_Postcode": "first"
        }).round(2)
        grouped.columns = ["Avg Companies/Address", "Max Companies/Address", "Total Addresses", "Companies in Postcode"]
        st.dataframe(grouped, use_container_width=True)

    with tab2:
        plot_plotly(fdf)

    with tab3:
        plot_seaborn(fdf)

    with tab4:
        plot_matplotlib(fdf)

    st.markdown("---")
    st.markdown("📍 **Note**: High concentration of companies at a single address may indicate shell companies or fraudulent registrations.")


if __name__ == "__main__":
    main()
