# streamlit_dashboard_mvp.py
# Streamlit dashboard tailored to tuesday_mvp.csv dataset

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import ast

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
def load_data(path: str = "tuesday_mvp.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


# -----------------------------
# KPI block
# -----------------------------
def kpi_block(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Addresses", f"{len(df):,}")
    c2.metric("Total Companies", f"{df['Companies_at_Address'].sum():,}")
    c3.metric("Avg Dormant Rate", f"{df['dormant_rate'].mean():.2%}")
    c4.metric("Avg Micro Entity Rate", f"{df['micro_entity_rate'].mean():.2%}")


# -----------------------------
# Sidebar filters
# -----------------------------
def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    # Address search
    st.sidebar.subheader("🏠 Address Search")
    address_search = st.sidebar.text_input(
        "Search addresses (street name, full address, etc.)",
        placeholder="e.g., 'SHELTON STREET', 'LONDON', 'WC2H'",
        help="Search in both street address and full address fields"
    )
    
    # Search type selection
    search_type = st.sidebar.radio(
        "Search in:",
        ["Street Address Only", "Full Address Only", "Both (Street + Full)"],
        index=2
    )
    
    # Case sensitivity option
    case_sensitive = st.sidebar.checkbox("Case sensitive search", value=False)

    # Company name search
    st.sidebar.subheader("🏢 Company Name Search")
    company_search = st.sidebar.text_input(
        "Search by company name",
        placeholder="e.g., 'GOOGLE', 'MICROSOFT', 'BRITISH'",
        help="Find addresses where specific companies are registered"
    )
    
    if company_search:
        st.sidebar.info("⚠️ Company search may take a moment due to large dataset")

    # Postcode filter - will be dynamically updated if specific address is selected
    st.sidebar.subheader("📮 Postcode Filter")
    # Initial postcode selection
    default_postcodes = sorted(df["PostCode_clean"].unique())[:10]

    # Rank filter
    st.sidebar.subheader("📊 Rank Filter")
    ranks = st.sidebar.slider(
        "Rank range",
        int(df["rank"].min()),
        int(df["rank"].max()),
        (int(df["rank"].min()), int(df["rank"].max())),
    )

    # Apply filters
    fdf = df.copy()
    selected_specific_postcode = None  # Track if a specific address was selected
    
    # Apply address search filter
    if address_search:
        search_term = address_search if case_sensitive else address_search.lower()
        
        if search_type == "Street Address Only":
            if case_sensitive:
                mask = fdf["Address_street"].str.contains(search_term, na=False, regex=False)
            else:
                mask = fdf["Address_street"].str.lower().str.contains(search_term, na=False, regex=False)
        elif search_type == "Full Address Only":
            if case_sensitive:
                mask = fdf["FullAddress_best"].str.contains(search_term, na=False, regex=False)
            else:
                mask = fdf["FullAddress_best"].str.lower().str.contains(search_term, na=False, regex=False)
        else:  # Both
            if case_sensitive:
                mask = (fdf["Address_street"].str.contains(search_term, na=False, regex=False) |
                       fdf["FullAddress_best"].str.contains(search_term, na=False, regex=False))
            else:
                mask = (fdf["Address_street"].str.lower().str.contains(search_term, na=False, regex=False) |
                       fdf["FullAddress_best"].str.lower().str.contains(search_term, na=False, regex=False))
        
        fdf = fdf[mask]
        st.sidebar.info(f"🔍 Found {len(fdf):,} addresses matching '{address_search}'")
        
        # Add address selection dropdown if multiple results
        if len(fdf) > 1:
            st.sidebar.subheader("🎯 Select Specific Address")
            
            # Create options for dropdown
            address_options = ["All matching addresses"] + [
                f"{row['Address_street']} ({row['PostCode_clean']}) - {row['Companies_at_Address']:,} companies"
                for _, row in fdf.head(20).iterrows()  # Limit to 20 for performance
            ]
            
            selected_address = st.sidebar.selectbox(
                "Choose an address:",
                options=address_options,
                help="Select a specific address to focus on, or keep 'All' to see all matches"
            )
            
            # Filter to selected address if not "All"
            if selected_address != "All matching addresses":
                # Extract the street address from the selected option
                selected_street = selected_address.split(" (")[0]
                fdf = fdf[fdf["Address_street"] == selected_street]
                st.sidebar.success(f"✅ Focused on: {selected_street}")
                
                # Extract the postcode for automatic filter update
                if len(fdf) == 1:
                    selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
                    st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
        elif len(fdf) == 1:
            st.sidebar.success(f"✅ Exact match: {fdf.iloc[0]['Address_street']}")
            selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
            st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
    
    # Apply company name search filter
    if company_search:
        company_term = company_search if case_sensitive else company_search.upper()
        
        def contains_company(names_list_str):
            try:
                names_list = ast.literal_eval(names_list_str)
                if case_sensitive:
                    return any(company_term in name for name in names_list)
                else:
                    return any(company_term in name.upper() for name in names_list)
            except:
                return False
        
        # Apply company search filter
        company_mask = fdf['company_names_list'].apply(contains_company)
        fdf = fdf[company_mask]
        
        if len(fdf) > 0:
            st.sidebar.success(f"🏢 Found {len(fdf):,} addresses with companies matching '{company_search}'")
        else:
            st.sidebar.error(f"🏢 No companies found matching '{company_search}'")
    
    # Apply postcode filter - either auto-selected or manual
    if selected_specific_postcode:
        # If a specific address was selected, automatically filter to its postcode
        postcodes = [selected_specific_postcode]
        # Show the postcode filter as disabled/info only
        st.sidebar.multiselect(
            "Postcodes (auto-selected)",
            options=sorted(df["PostCode_clean"].unique()),
            default=[selected_specific_postcode],
            disabled=True,
            help="Postcode automatically selected based on chosen address"
        )
    else:
        # Normal postcode selection
        postcodes = st.sidebar.multiselect(
            "Postcodes",
            options=sorted(df["PostCode_clean"].unique()),
            default=default_postcodes,
        )
    
    # Apply the postcode filter
    fdf = fdf[fdf["PostCode_clean"].isin(postcodes)]
    
    # Apply rank filter
    fdf = fdf[fdf["rank"].between(ranks[0], ranks[1])]

    # Show filter summary
    st.sidebar.write("---")
    st.sidebar.write(f"**📋 Results: {len(fdf):,} addresses**")
    if len(fdf) < len(df):
        st.sidebar.write(f"*Filtered from {len(df):,} total addresses*")
    
    # Show top matches if address search is active
    if address_search and len(fdf) > 0:
        st.sidebar.write("**🎯 Top Address Matches:**")
        top_matches = fdf.nlargest(3, 'Companies_at_Address')[['Address_street', 'Companies_at_Address']]
        for _, row in top_matches.iterrows():
            st.sidebar.write(f"• {row['Address_street'][:40]}{'...' if len(row['Address_street']) > 40 else ''} ({row['Companies_at_Address']:,} companies)")
    
    # Show company search results
    if company_search and len(fdf) > 0:
        st.sidebar.write("**🏢 Company Search Results:**")
        
        # Find specific companies at each address
        company_results = []
        company_term_upper = company_search.upper()
        
        for _, row in fdf.head(5).iterrows():  # Limit to first 5 addresses for performance
            try:
                names_list = ast.literal_eval(row['company_names_list'])
                matching_companies = []
                
                for company in names_list:
                    if (case_sensitive and company_search in company) or \
                       (not case_sensitive and company_term_upper in company.upper()):
                        matching_companies.append(company)
                        if len(matching_companies) >= 3:  # Limit to 3 per address
                            break
                
                if matching_companies:
                    company_results.append({
                        'address': row['Address_street'],
                        'postcode': row['PostCode_clean'],
                        'companies': matching_companies,
                        'total_companies': row['Companies_at_Address']
                    })
            except:
                continue
        
        # Display results
        for result in company_results[:3]:  # Show top 3 addresses
            st.sidebar.write(f"**📍 {result['address'][:30]}{'...' if len(result['address']) > 30 else ''}**")
            st.sidebar.write(f"   📮 {result['postcode']}")
            st.sidebar.write(f"   🏢 Matching companies:")
            for company in result['companies']:
                st.sidebar.write(f"      • {company[:35]}{'...' if len(company) > 35 else ''}")
            st.sidebar.write(f"   📊 {result['total_companies']:,} total companies")
            st.sidebar.write("---")

    st.sidebar.download_button(
        label="📥 Download filtered CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="mvp_filtered.csv",
        mime="text/csv",
    )

    return fdf


# -----------------------------
# Plot sections
# -----------------------------

def display_selected_address_info(fdf: pd.DataFrame):
    """Display detailed information about selected addresses"""
    if len(fdf) == 1:
        # Single address selected - show detailed info
        address = fdf.iloc[0]
        
        st.markdown("### 🏠 Selected Address Details")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**📍 Street Address:** {address['Address_street']}")
            st.markdown(f"**📮 Postcode:** {address['PostCode_clean']}")
            st.markdown(f"**🏢 Full Address:** {address['FullAddress_best']}")
            
        with col2:
            st.metric("Companies at Address", f"{address['Companies_at_Address']:,}")
            st.metric("Address Rank", f"#{address['rank']:,}")
            if 'dormant_rate' in address:
                st.metric("Dormancy Rate", f"{address['dormant_rate']:.1%}")
        
        # Show company details if available
        if 'company_names_list' in address and pd.notna(address['company_names_list']):
            st.markdown("#### 🏢 Companies at This Address")
            
            try:
                companies = ast.literal_eval(address['company_names_list'])
                
                # Show statistics
                total_companies = len(companies)
                st.write(f"**Total Companies:** {total_companies:,}")
                
                if total_companies > 0:
                    # Show first 20 companies
                    display_count = min(20, total_companies)
                    st.write(f"**Showing first {display_count} companies:**")
                    
                    companies_df = pd.DataFrame({
                        'Company Name': companies[:display_count],
                        'Index': range(1, display_count + 1)
                    })
                    st.dataframe(companies_df[['Index', 'Company Name']], use_container_width=True, hide_index=True)
                    
                    if total_companies > 20:
                        st.info(f"... and {total_companies - 20:,} more companies. Use company name search to find specific companies.")
                        
                        # Add a search box for this specific address
                        company_filter = st.text_input(
                            "🔍 Search companies at this address:",
                            placeholder="Enter company name to search within this address",
                            key="address_company_search"
                        )
                        
                        if company_filter:
                            filtered_companies = [c for c in companies if company_filter.upper() in c.upper()]
                            if filtered_companies:
                                st.write(f"**Found {len(filtered_companies)} matching companies:**")
                                matches_df = pd.DataFrame({
                                    'Company Name': filtered_companies[:50],  # Limit to 50 results
                                    'Match': range(1, min(51, len(filtered_companies) + 1))
                                })
                                st.dataframe(matches_df[['Match', 'Company Name']], use_container_width=True, hide_index=True)
                                if len(filtered_companies) > 50:
                                    st.info(f"Showing first 50 of {len(filtered_companies)} matches")
                            else:
                                st.warning(f"No companies found matching '{company_filter}'")
                    
            except Exception as e:
                st.error(f"Error loading company data: {e}")
        
        st.markdown("---")
    
    elif len(fdf) > 1 and len(fdf) <= 10:
        # Multiple addresses (but not too many) - show summary
        st.markdown(f"### 📍 Selected Addresses Summary ({len(fdf)} addresses)")
        
        for _, address in fdf.iterrows():
            with st.expander(f"🏠 {address['Address_street']} ({address['PostCode_clean']}) - {address['Companies_at_Address']:,} companies"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Full Address:** {address['FullAddress_best']}")
                with col2:
                    st.metric("Companies", f"{address['Companies_at_Address']:,}")
                with col3:
                    if 'dormant_rate' in address:
                        st.metric("Dormancy Rate", f"{address['dormant_rate']:.1%}")
        
        st.markdown("---")


def plot_dormancy_analysis(filtered_df: pd.DataFrame, full_df: pd.DataFrame):
    st.subheader("🔍 Dormancy Rate Distribution & Outlier Analysis")
    
    # Add explanatory note about the distribution
    st.info("""
    📊 **Distribution Characteristics**: Dormancy rates are heavily right-skewed with many addresses having 0% dormancy. 
    The IQR method produces a negative lower bound (-7.54%) which is clamped to 0% since rates cannot be negative.
    This means only high dormancy rates (>27.4%) are considered outliers.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate statistics
        mean_rate = full_df['dormant_rate'].mean()
        median_rate = full_df['dormant_rate'].median()
        std_rate = full_df['dormant_rate'].std()
        
        # Define outlier thresholds (using IQR method, clamped to valid range)
        Q1 = full_df['dormant_rate'].quantile(0.25)
        Q3 = full_df['dormant_rate'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound_raw = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Clamp lower bound to 0 since dormancy rates cannot be negative
        lower_bound = max(0.0, lower_bound_raw)
        
        # Create histogram with Plotly
        fig = go.Figure()
        
        # Add histogram for all data
        fig.add_trace(go.Histogram(
            x=full_df['dormant_rate'],
            nbinsx=50,
            name='All Addresses',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        # Add histogram for filtered data
        if len(filtered_df) > 0:
            fig.add_trace(go.Histogram(
                x=filtered_df['dormant_rate'],
                nbinsx=50,
                name='Selected Addresses',
                marker_color='red',
                opacity=0.7
            ))
        
        # Add mean and median lines
        fig.add_vline(x=mean_rate, line_dash="dash", line_color="green", 
                      annotation_text=f"Mean: {mean_rate:.2%}")
        fig.add_vline(x=median_rate, line_dash="dash", line_color="orange", 
                      annotation_text=f"Median: {median_rate:.2%}")
        
        # Add outlier bounds
        if lower_bound > 0:
            fig.add_vline(x=lower_bound, line_dash="dot", line_color="red", 
                          annotation_text=f"Lower Outlier: {lower_bound:.2%}")
        fig.add_vline(x=upper_bound, line_dash="dot", line_color="red", 
                      annotation_text=f"Upper Outlier: {upper_bound:.2%}")
        
        # Add 0% line for reference
        fig.add_vline(x=0, line_dash="solid", line_color="gray", line_width=1,
                      annotation_text="0% (No Dormant Companies)")
        
        fig.update_layout(
            title="Dormancy Rate Distribution",
            xaxis_title="Dormancy Rate",
            yaxis_title="Count",
            barmode='overlay',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Box plot for better outlier visualization
        fig_box = go.Figure()
        
        # Add box plot for all data
        fig_box.add_trace(go.Box(
            y=full_df['dormant_rate'],
            name='All Addresses',
            marker_color='lightblue',
            boxpoints='outliers'
        ))
        
        # Add box plot for filtered data
        if len(filtered_df) > 0:
            fig_box.add_trace(go.Box(
                y=filtered_df['dormant_rate'],
                name='Selected Addresses',
                marker_color='red',
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ))
        
        fig_box.update_layout(
            title="Dormancy Rate Box Plot (Outlier Detection)",
            yaxis_title="Dormancy Rate",
            height=400
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Statistics table
    st.markdown("### 📊 Statistical Summary")
    col1_stats, col2_stats = st.columns(2)
    
    with col1_stats:
        st.markdown("**All Addresses:**")
        stats_all = pd.DataFrame({
            'Metric': ['Mean', 'Median', 'Std Dev', 'Q1 (25%)', 'Q3 (75%)', 
                      'IQR Method Lower', 'Effective Lower Bound', 'Upper Outlier Bound'],
            'Value': [f"{mean_rate:.2%}", f"{median_rate:.2%}", f"{std_rate:.2%}", 
                     f"{Q1:.2%}", f"{Q3:.2%}", f"{lower_bound_raw:.2%}", 
                     f"{lower_bound:.2%}", f"{upper_bound:.2%}"]
        })
        st.dataframe(stats_all, use_container_width=True, hide_index=True)
    
    with col2_stats:
        if len(filtered_df) > 0:
            st.markdown("**Selected Addresses:**")
            selected_mean = filtered_df['dormant_rate'].mean()
            selected_median = filtered_df['dormant_rate'].median()
            selected_std = filtered_df['dormant_rate'].std()
            
            
            stats_selected = pd.DataFrame({
                'Metric': ['Mean', 'Median', 'Std Dev', 'Sample Size'],
                'Value': [f"{selected_mean:.2%}", f"{selected_median:.2%}", 
                         f"{selected_std:.2%}", f"{len(filtered_df)}"]
            })
            st.dataframe(stats_selected, use_container_width=True, hide_index=True)
            
            # Outlier detection for selected addresses
            outliers = filtered_df[(filtered_df['dormant_rate'] < lower_bound) | 
                                  (filtered_df['dormant_rate'] > upper_bound)]
            if len(outliers) > 0:
                st.warning(f"⚠️ {len(outliers)} addresses in selection are outliers ({len(outliers)/len(filtered_df)*100:.1f}%)")
                st.dataframe(outliers[['Address_street', 'PostCode_clean', 'dormant_rate', 'Companies_at_Address']].head(10), 
                           use_container_width=True)
            else:
                st.success("✅ No outliers detected in selected addresses")
    
    # Percentile ranking for top addresses
    st.markdown("### 🎯 Percentile Ranking of Selected Addresses")
    if len(filtered_df) > 0:
        top_addresses = filtered_df.nlargest(10, 'dormant_rate')[['Address_street', 'PostCode_clean', 'dormant_rate', 'Companies_at_Address']].copy()
        top_addresses['Percentile'] = top_addresses['dormant_rate'].apply(
            lambda x: f"{(x <= full_df['dormant_rate']).mean() * 100:.1f}%"
        )
        top_addresses['Is Outlier'] = top_addresses['dormant_rate'].apply(
            lambda x: '🔴 Yes' if x > upper_bound else '🟢 No'
        )
        st.dataframe(top_addresses, use_container_width=True, hide_index=True)


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

    # Show selected address information
    display_selected_address_info(fdf)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Data", "Dormancy Analysis", "Plotly", "Bar Chart", "Distribution"])

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
        plot_dormancy_analysis(fdf, df)

    with tab3:
        plot_plotly(fdf)

    with tab4:
        plot_seaborn(fdf)

    with tab5:
        plot_matplotlib(fdf)

    st.markdown("---")
    st.markdown("📍 **Note**: High concentration of companies at a single address may indicate shell companies or fraudulent registrations.")


if __name__ == "__main__":
    main()
