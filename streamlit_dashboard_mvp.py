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

@st.cache_data
def load_baselines_data(path: str = "baselines_final.csv") -> pd.DataFrame:
    import os
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join with the filename to get absolute path
    full_path = os.path.join(script_dir, path)
    df = pd.read_csv(full_path)
    return df


# -----------------------------
# KPI block
# -----------------------------
def kpi_block(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Addresses", f"{len(df):,}")
    c2.metric("Total Companies", f"{df['Companies_at_Address'].sum():,}")
    c3.metric("Avg Dormant Rate", f"{df['dormant_rate'].mean():.2%}")
    c4.metric("Avg No Accounts Rate", f"{df['no_accounts_rate'].mean():.2%}")


# -----------------------------
# Sidebar filters
# -----------------------------
def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    
    # Reset button at the top
    if st.sidebar.button("🔄 Reset All Filters", width="stretch", type="primary"):
        # Clear ALL session state keys to completely reset all filters and search functionality
        st.session_state.clear()
        # Set flag to show empty results after reset
        st.session_state['reset_clicked'] = True
        st.rerun()

    # Address search
    st.sidebar.subheader("🏠 Address Search")
    # No default address search - let users search manually
    
    address_search = st.sidebar.text_input(
        "Search addresses (street name, full address, etc.)",
        placeholder="e.g., 'SHELTON STREET', 'LONDON', 'WC2H'",
        help="Search in both street address and full address fields",
        key="address_search_input"
    )
    
    # Search type selection
    search_type = st.sidebar.radio(
        "Search in:",
        ["Street Address Only", "Full Address Only", "Both (Street + Full)"],
        index=2,
        key="search_type_radio"
    )
    
    # Case sensitivity option
    case_sensitive = st.sidebar.checkbox("Case sensitive search", value=False, key="case_sensitive_checkbox")

    # Company name search
    st.sidebar.subheader("🏢 Company Name Search")
    company_search = st.sidebar.text_input(
        "Search by company name",
        placeholder="e.g., 'GOOGLE', 'MICROSOFT', 'BRITISH'",
        help="Find addresses where specific companies are registered",
        key="company_search_input"
    )
    
    if company_search:
        st.sidebar.info("⚠️ Company search may take a moment due to large dataset")

    # Postcode filter - will be dynamically updated if specific address is selected
    st.sidebar.subheader("📮 Postcode Filter")
    # Initial postcode selection - first 12 postcodes alphabetically  
    # Check if this is a fresh page load (no session state) vs after reset button
    # Fresh page load: show WC2H 9JQ default
    # After reset: show empty (handled by session state flag)
    if 'reset_clicked' in st.session_state:
        # User clicked reset - show no results
        default_postcodes = []
    else:
        # Fresh page load - show default postcode
        default_postcodes = ["WC2H 9JQ"]

    # Rank filter
    st.sidebar.subheader("📊 Rank Filter")
    ranks = st.sidebar.slider(
        "Rank range",
        int(df["rank"].min()),
        int(df["rank"].max()),
        (int(df["rank"].min()), int(df["rank"].max())),
        key="rank_slider"
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
            
            # Create simple address options (avoid pandas serialization issues)
            address_list = []
            for _, row in fdf.head(20).iterrows():  # Limit to 20 for performance
                address_str = f"{row['Address_street']} ({row['PostCode_clean']}) - {int(row['Companies_at_Address'])} companies"
                address_list.append(address_str)
            
            address_options = ["All matching addresses"] + address_list
            
            selected_address = st.sidebar.selectbox(
                "Choose an address:",
                options=address_options,
                help="Select a specific address to focus on",
                index=0
            )
            
            # Filter to selected address if not "All"
            if selected_address != "All matching addresses":
                # Extract the street address from the selected option
                selected_street = selected_address.split(" (")[0]
                fdf = fdf[fdf["Address_street"] == selected_street]
                st.sidebar.success(f"✅ Focused on: {selected_street}")
                
                # Automatically set the postcode for this address
                if len(fdf) > 0:
                    selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
                    st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
        elif len(fdf) == 1:
            st.sidebar.success(f"✅ Exact match: {fdf.iloc[0]['Address_street']}")
            selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
            st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
        else:
            st.sidebar.info("📊 Showing all matching addresses")
    
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
            
            # Add company address selection dropdown if multiple results
            if len(fdf) > 1:
                st.sidebar.subheader("🎯 Select Specific Company Address")
                
                # Create options for dropdown showing address and company count
                company_address_options = ["All matching company addresses"] + [
                    f"{str(row['Address_street'])} ({str(row['PostCode_clean'])}) - {int(row['Companies_at_Address']):,} companies"
                    for _, row in fdf.head(20).iterrows()  # Limit to 20 for performance
                ]
                
                selected_company_address = st.sidebar.selectbox(
                    "Choose a company address:",
                    options=company_address_options,
                    help="Select a specific address where the company is registered",
                    key="company_address_selector"
                )
                
                # Filter to selected company address if not "All"
                if selected_company_address != "All matching company addresses":
                    # Extract the street address from the selected option
                    selected_company_street = selected_company_address.split(" (")[0]
                    fdf = fdf[fdf["Address_street"] == selected_company_street]
                    st.sidebar.success(f"✅ Focused on company address: {selected_company_street}")
                    
                    # Extract the postcode for automatic filter update (same logic as address search)
                    if len(fdf) == 1:
                        if not selected_specific_postcode:  # Only set if not already set by address search
                            selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
                            st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
            elif len(fdf) == 1:
                st.sidebar.success(f"✅ Exact company address match: {fdf.iloc[0]['Address_street']}")
                if not selected_specific_postcode:  # Only set if not already set by address search
                    selected_specific_postcode = fdf.iloc[0]['PostCode_clean']
                    st.sidebar.info(f"📮 Auto-selected postcode: {selected_specific_postcode}")
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
            key="postcode_multiselect"
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
    if len(fdf) >= 1:
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
                    st.dataframe(companies_df[['Index', 'Company Name']], width="stretch", hide_index=True)
                    
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
                                st.dataframe(matches_df[['Match', 'Company Name']], width="stretch", hide_index=True)
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
        st.plotly_chart(fig, width="stretch")
    
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
        st.plotly_chart(fig_box, width="stretch")
    
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
        st.dataframe(stats_all, width="stretch", hide_index=True)
    
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
            st.dataframe(stats_selected, width="stretch", hide_index=True)
            
            # Outlier detection for selected addresses
            outliers = filtered_df[(filtered_df['dormant_rate'] < lower_bound) | 
                                  (filtered_df['dormant_rate'] > upper_bound)]
            if len(outliers) > 0:
                st.warning(f"⚠️ {len(outliers)} addresses in selection are outliers ({len(outliers)/len(filtered_df)*100:.1f}%)")
                st.dataframe(outliers[['Address_street', 'PostCode_clean', 'dormant_rate', 'Companies_at_Address']].head(10), 
                           width="stretch")
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
        st.dataframe(top_addresses, width="stretch", hide_index=True)


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
    st.plotly_chart(fig, width="stretch")


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
# Documentation section
# -----------------------------
def show_documentation():
    """Display documentation including baseline data"""
    st.subheader("📚 Dashboard Documentation")
    
    # Introduction to Companies House and virtual addresses
    st.markdown("""
    ### 🏛️ About Companies House Data
    
    **Companies House** is the UK corporate register. Every active company must file annual accounts; each filing is tagged with an accounts type (e.g., full, micro-entity, dormant, no-accounts-filed). Those tags are what we aggregate into address-level signals.
    
    **What's a "virtual address" in our context?** A registered office that's primarily a mail-drop/formation-agent/forwarding service rather than a trading site. You often see hundreds or thousands of firms using the same address. We call these **hubs** and score them by how their filing mix compares to national baselines.
    
    ### 📊 Key Metrics Explained
    
    **😴 Dormant Companies**
    - **Definition**: A company with no significant transactions in the year files dormant accounts (ultra-minimal, usually just a balance sheet). Nationally, dormants are roughly ~12% of companies.
    - **Why we look at it**: An address with a dormant-rate far above baseline (e.g., 2–4×) is a classic indicator of mail-drop/shelf-company clustering and warrants review; rate + count keeps us from over-weighting tiny samples.
    
    **📋 "No Accounts Filed"**
    - **What it means**: Either (a) the company is new and accounts aren't due yet, or (b) the deadline passed and they're overdue (which triggers penalties and, if persistent, potential strike-off).
    - **Our metric**: `no_accounts_rate = (# companies at the address with "no accounts filed") / (total at the address)`. High rates can be normal at formation hubs with many fresh incorporations, but persistently high rates over time are a red flag for churny, non-compliant entities.
    
    **🎯 How We Use These**
    We benchmark each hub's `dormant_rate` and `no_accounts_rate` against national baselines to surface outliers. "Well above baseline" + large volumes pushes a hub to the top of our triage queue.
    """)
    
    st.divider()
    
    # Load and display baseline data
    try:
        baselines_df = load_baselines_data()
        
        st.markdown("### 📊 Baseline Data")
        st.markdown("This table shows baseline metrics for different company filing types and their occurrence rates in the dataset:")
        
        # Format the baseline data for better display
        display_df = baselines_df.copy()
        
        # Format rate column as percentage if it exists
        if 'rate' in display_df.columns:
            display_df['Rate (%)'] = (display_df['rate'] * 100).round(3)
        
        # Format count column with commas
        if 'count' in display_df.columns:
            display_df['Count'] = display_df['count'].apply(lambda x: f"{x:,}")
            
        # Format denominator column with commas  
        if 'denominator' in display_df.columns:
            display_df['Total'] = display_df['denominator'].apply(lambda x: f"{x:,}")
        
        # Select columns for display
        display_cols = ['metric']
        if 'Count' in display_df.columns:
            display_cols.append('Count')
        if 'Total' in display_df.columns:
            display_cols.append('Total')
        if 'Rate (%)' in display_df.columns:
            display_cols.append('Rate (%)')
            
        st.dataframe(
            display_df[display_cols], 
            width="stretch",
            hide_index=True
        )
        
        st.markdown("### 📖 About This Dashboard")
        st.markdown("""
        **Purpose**: Analyze company registration data by address and postcode to identify patterns in business registration density and characteristics.
        
        **Key Features**:
        - 🏠 **Address Search**: Find specific addresses or street names
        - 🏢 **Company Search**: Search for companies by name
        - 📮 **Postcode Filtering**: Filter data by postal codes
        - 📊 **Rank Analysis**: Filter by address ranking metrics
        - 📈 **Visualizations**: Interactive charts and graphs
        - 🔄 **Reset Filters**: Clear all filters to start fresh
        
        **Data Sources**:
        - Main dataset: Company registration addresses with postcode information
        - Baseline data: Reference metrics for different filing types and company characteristics
        """)
        
        # Add hub distribution visualization
        st.markdown("### 📈 Hub Distribution Analysis")
        create_hub_visualizations()
        
    except FileNotFoundError:
        st.warning("⚠️ Baseline data file not found. Please ensure 'baselines_final.csv' is in the same directory.")
    except Exception as e:
        st.error(f"❌ Error loading baseline data: {str(e)}")

def create_hub_visualizations():
    """Create hub distribution and spike analysis visualizations"""
    try:
        # Configuration
        MIN_HUB_SIZE = 100
        HIST_XMAX = 10_000
        HIST_BINS = 80
        DELTA_DORM_PP = 20
        ABS_DORM_MIN = 0.40
        DELTA_NOACC_PP = 20
        ABS_NOACC_MIN = 0.50
        
        # Load main data
        df = load_data()
        
        # Helper functions
        def to_num(s): 
            return pd.to_numeric(s, errors="coerce")
        
        def get_baseline(metric_name: str):
            try:
                baselines_df = load_baselines_data()
                if "rate" not in baselines_df.columns:
                    baselines_df["count"] = to_num(baselines_df.get("count"))
                    baselines_df["denominator"] = to_num(baselines_df.get("denominator"))
                    baselines_df["rate"] = baselines_df["count"] / baselines_df["denominator"]
                s = baselines_df.loc[baselines_df["metric"].str.lower() == metric_name.lower(), "rate"].dropna()
                return float(s.iloc[0]) if len(s) else None
            except:
                return None
        
        # Prepare data
        for c in ["Companies_at_Address", "dormant_rate", "no_accounts_rate", "dormant_number", "no_accounts_number"]:
            if c in df.columns: 
                df[c] = to_num(df[c])
        
        # Compute rates if missing but counts exist
        if ("dormant_rate" not in df.columns or df["dormant_rate"].isna().all()) and \
           {"dormant_number", "Companies_at_Address"}.issubset(df.columns):
            denom = df["Companies_at_Address"].where(df["Companies_at_Address"] > 0, df["dormant_number"])
            df["dormant_rate"] = (df["dormant_number"] / denom).clip(0, 1)
        
        if ("no_accounts_rate" not in df.columns or df["no_accounts_rate"].isna().all()) and \
           {"no_accounts_number", "Companies_at_Address"}.issubset(df.columns):
            denom = df["Companies_at_Address"].where(df["Companies_at_Address"] > 0, df["no_accounts_number"])
            df["no_accounts_rate"] = (df["no_accounts_number"] / denom).clip(0, 1)
        
        # Create hubs dataset
        hubs = df.loc[df["Companies_at_Address"].fillna(0) >= MIN_HUB_SIZE].copy()
        hubs = hubs.sort_values("Companies_at_Address", ascending=False).reset_index(drop=True)
        hubs["rank"] = np.arange(1, len(hubs) + 1)
        
        if len(hubs) == 0:
            st.warning(f"⚠️ No hubs found with ≥{MIN_HUB_SIZE} companies")
            return
        
        # 1) Hub Distribution Histogram
        st.markdown("#### 🏢 Company Hub Distribution")
        vals = hubs["Companies_at_Address"].dropna().astype(float)
        tail_count = int((vals >= HIST_XMAX).sum())
        tail_max = int(vals.max()) if len(vals) else 0
        
        fig, ax = plt.subplots(figsize=(10, 6))
        clipped_vals = vals.clip(upper=HIST_XMAX)
        display_vals = clipped_vals[vals < HIST_XMAX]
        
        ax.hist(display_vals, bins=HIST_BINS, alpha=0.7, color='skyblue', edgecolor='black')
        ax.set_xlabel("Companies per Hub")
        ax.set_ylabel("Number of Hubs")
        ax.set_title(f"Distribution of Companies per Hub (≥{MIN_HUB_SIZE}) — 0 to {HIST_XMAX:,}")
        
        # Format x-axis with commas
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        if tail_count > 0:
            ax.text(0.98, 0.95, f"{tail_count:,} hubs ≥ {HIST_XMAX:,}\n(max {tail_max:,})",
                   transform=ax.transAxes, ha="right", va="top",
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Hubs", f"{len(hubs):,}")
        with col2:
            st.metric("Median Companies/Hub", f"{vals.median():.0f}")
        with col3:
            st.metric("Mean Companies/Hub", f"{vals.mean():.0f}")
        with col4:
            st.metric("Max Companies/Hub", f"{tail_max:,}")
        
        # 2) Dormant Rate Analysis (if available)
        if "dormant_rate" in hubs.columns and not hubs["dormant_rate"].isna().all():
            st.markdown("#### 😴 Dormant Rate vs Hub Rank")
            
            dormant_baseline = get_baseline("dormant")
            plot_hubs = hubs.head(500).copy()  # Limit for performance
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot raw line
            x_vals = plot_hubs["rank"]
            y_vals = plot_hubs["dormant_rate"] * 100  # Convert to percentage
            ax.plot(x_vals, y_vals, color='blue', alpha=0.7, linewidth=2, label='Dormant Rate')
            
            # Highlight spikes
            if dormant_baseline is not None:
                threshold = max(dormant_baseline + DELTA_DORM_PP/100.0, ABS_DORM_MIN)
                spike_mask = plot_hubs["dormant_rate"] >= threshold
                
                if spike_mask.any():
                    spike_x = x_vals[spike_mask]
                    spike_y = y_vals[spike_mask]
                    ax.scatter(spike_x, spike_y, color='red', s=50, alpha=0.8, 
                             label=f'Spikes (≥{threshold*100:.0f}%)', zorder=5)
                
                # Add baseline reference line
                ax.axhline(y=dormant_baseline*100, color='gray', linestyle='--', alpha=0.5,
                          label=f'Baseline ({dormant_baseline*100:.1f}%)')
            
            ax.set_xlabel("Hub Rank (by company count)")
            ax.set_ylabel("Dormant Rate (%)")
            ax.set_title("Dormant Rate vs Hub Rank")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig, clear_figure=True)
        
        # 3) No Accounts Rate Analysis (if available)
        if "no_accounts_rate" in hubs.columns and not hubs["no_accounts_rate"].isna().all():
            st.markdown("#### 📋 No Accounts Filed Rate vs Hub Rank")
            
            noacc_baseline = get_baseline("no_accounts_filed")
            plot_hubs = hubs.head(500).copy()  # Limit for performance
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot raw line
            x_vals = plot_hubs["rank"]
            y_vals = plot_hubs["no_accounts_rate"] * 100  # Convert to percentage
            ax.plot(x_vals, y_vals, color='green', alpha=0.7, linewidth=2, label='No Accounts Rate')
            
            # Highlight spikes
            if noacc_baseline is not None:
                threshold = max(noacc_baseline + DELTA_NOACC_PP/100.0, ABS_NOACC_MIN)
                spike_mask = plot_hubs["no_accounts_rate"] >= threshold
                
                if spike_mask.any():
                    spike_x = x_vals[spike_mask]
                    spike_y = y_vals[spike_mask]
                    ax.scatter(spike_x, spike_y, color='orange', s=50, alpha=0.8, 
                             label=f'Spikes (≥{threshold*100:.0f}%)', zorder=5)
                
                # Add baseline reference line
                ax.axhline(y=noacc_baseline*100, color='gray', linestyle='--', alpha=0.5,
                          label=f'Baseline ({noacc_baseline*100:.1f}%)')
            
            ax.set_xlabel("Hub Rank (by company count)")
            ax.set_ylabel("No Accounts Filed Rate (%)")
            ax.set_title("No Accounts Filed Rate vs Hub Rank")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig, clear_figure=True)
        
        # Add interactive hover visualizations
        st.markdown("### 🎯 Interactive Analysis with Hover Details")
        create_interactive_hub_analysis(hubs)
            
    except Exception as e:
        st.error(f"❌ Error creating hub visualizations: {str(e)}")
        st.write("Debug info:", str(e))

def create_interactive_hub_analysis(hubs):
    """Create interactive Plotly visualizations with hover tooltips"""
    try:
        # Configuration
        MIN_HUB_SIZE = 100
        DELTA_DORM_PP = 20
        ABS_DORM_MIN = 0.40
        DELTA_NOACC_PP = 20
        ABS_NOACC_MIN = 0.50
        
        # Helper functions
        def get_baseline(metric_name: str):
            try:
                baselines_df = load_baselines_data()
                if "rate" not in baselines_df.columns:
                    baselines_df["count"] = pd.to_numeric(baselines_df.get("count"), errors="coerce")
                    baselines_df["denominator"] = pd.to_numeric(baselines_df.get("denominator"), errors="coerce")
                    baselines_df["rate"] = baselines_df["count"] / baselines_df["denominator"]
                s = baselines_df.loc[baselines_df["metric"].str.lower() == metric_name.lower(), "rate"].dropna()
                return float(s.iloc[0]) if len(s) else None
            except:
                return None
        
        def highlight_mask(series, base, delta_pp, abs_min):
            base = 0.0 if base is None else float(base)
            thr = max(base + delta_pp/100.0, abs_min)
            return series >= thr, thr
        
        def build_label_series(df):
            if "FullAddress_best" in df.columns:
                return df["FullAddress_best"].astype(str)
            elif {"Address_street", "PostCode_clean"}.issubset(df.columns):
                return (df["Address_street"].astype(str) + " | " + df["PostCode_clean"].astype(str))
            else:
                return df.index.astype(str)
        
        # Prepare data
        plot_df = hubs.head(1000).copy()  # Limit for performance
        labels = build_label_series(plot_df)
        
        # Interactive Dormant Rate Analysis
        if "dormant_rate" in plot_df.columns and not plot_df["dormant_rate"].isna().all():
            st.markdown("#### 😴 Interactive Dormant Rate Analysis")
            
            dorm_base = get_baseline("dormant")
            x_vals = plot_df["rank"]
            y_vals = plot_df["dormant_rate"]
            companies = plot_df["Companies_at_Address"]
            
            # Create mask for highlighting outliers
            mask, threshold = highlight_mask(y_vals, dorm_base, DELTA_DORM_PP, ABS_DORM_MIN)
            
            # Create Plotly figure
            fig = go.Figure()
            
            # Main line plot
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals * 100,  # Convert to percentage
                mode='lines',
                name='Dormant Rate',
                line=dict(color='blue', width=2),
                hovertemplate='<b>Rank %{x}</b><br>' +
                             'Dormant Rate: %{y:.1f}%<br>' +
                             '<extra></extra>'
            ))
            
            # Highlight outliers
            outlier_indices = mask[mask].index
            if len(outlier_indices) > 0:
                outlier_x = x_vals[outlier_indices]
                outlier_y = y_vals[outlier_indices] * 100
                outlier_companies = companies[outlier_indices]
                outlier_labels = labels[outlier_indices]
                
                fig.add_trace(go.Scatter(
                    x=outlier_x,
                    y=outlier_y,
                    mode='markers',
                    name=f'Outliers (≥{threshold*100:.0f}%)',
                    marker=dict(color='orange', size=8),
                    text=outlier_labels,
                    customdata=outlier_companies,
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Rank: %{x}<br>' +
                                 'Companies: %{customdata:,}<br>' +
                                 'Dormant Rate: %{y:.1f}%<br>' +
                                 '<extra></extra>'
                ))
            
            # Add baseline reference line
            if dorm_base is not None:
                fig.add_hline(
                    y=dorm_base * 100,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Baseline ({dorm_base*100:.1f}%)"
                )
            
            fig.update_layout(
                title=f"Interactive Dormant Rate by Hub Rank (≥{MIN_HUB_SIZE} companies)",
                xaxis_title="Hub Rank (1 = largest by companies)",
                yaxis_title="Dormant Rate (%)",
                height=500,
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Interactive No Accounts Rate Analysis
        if "no_accounts_rate" in plot_df.columns and not plot_df["no_accounts_rate"].isna().all():
            st.markdown("#### 📋 Interactive No Accounts Filed Rate Analysis")
            
            noacc_base = get_baseline("no_accounts_filed")
            x_vals = plot_df["rank"]
            y_vals = plot_df["no_accounts_rate"]
            companies = plot_df["Companies_at_Address"]
            
            # Create mask for highlighting outliers
            mask, threshold = highlight_mask(y_vals, noacc_base, DELTA_NOACC_PP, ABS_NOACC_MIN)
            
            # Create Plotly figure
            fig = go.Figure()
            
            # Main line plot
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals * 100,  # Convert to percentage
                mode='lines',
                name='No Accounts Rate',
                line=dict(color='green', width=2),
                hovertemplate='<b>Rank %{x}</b><br>' +
                             'No Accounts Rate: %{y:.1f}%<br>' +
                             '<extra></extra>'
            ))
            
            # Highlight outliers
            outlier_indices = mask[mask].index
            if len(outlier_indices) > 0:
                outlier_x = x_vals[outlier_indices]
                outlier_y = y_vals[outlier_indices] * 100
                outlier_companies = companies[outlier_indices]
                outlier_labels = labels[outlier_indices]
                
                fig.add_trace(go.Scatter(
                    x=outlier_x,
                    y=outlier_y,
                    mode='markers',
                    name=f'Outliers (≥{threshold*100:.0f}%)',
                    marker=dict(color='orange', size=8),
                    text=outlier_labels,
                    customdata=outlier_companies,
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Rank: %{x}<br>' +
                                 'Companies: %{customdata:,}<br>' +
                                 'No Accounts Rate: %{y:.1f}%<br>' +
                                 '<extra></extra>'
                ))
            
            # Add baseline reference line
            if noacc_base is not None:
                fig.add_hline(
                    y=noacc_base * 100,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Baseline ({noacc_base*100:.1f}%)"
                )
            
            fig.update_layout(
                title=f"Interactive No Accounts Rate by Hub Rank (≥{MIN_HUB_SIZE} companies)",
                xaxis_title="Hub Rank (1 = largest by companies)",
                yaxis_title="No Accounts Filed Rate (%)",
                height=500,
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary of outliers
        st.markdown("#### 🚨 Outlier Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            if "dormant_rate" in plot_df.columns:
                dorm_base = get_baseline("dormant")
                mask, threshold = highlight_mask(plot_df["dormant_rate"], dorm_base, DELTA_DORM_PP, ABS_DORM_MIN)
                outlier_count = mask.sum()
                st.metric(
                    "Dormant Rate Outliers", 
                    f"{outlier_count:,}",
                    help=f"Hubs with dormant rate ≥{threshold*100:.0f}%"
                )
        
        with col2:
            if "no_accounts_rate" in plot_df.columns:
                noacc_base = get_baseline("no_accounts_filed")
                mask, threshold = highlight_mask(plot_df["no_accounts_rate"], noacc_base, DELTA_NOACC_PP, ABS_NOACC_MIN)
                outlier_count = mask.sum()
                st.metric(
                    "No Accounts Outliers", 
                    f"{outlier_count:,}",
                    help=f"Hubs with no accounts rate ≥{threshold*100:.0f}%"
                )
            
    except Exception as e:
        st.error(f"❌ Error creating interactive visualizations: {str(e)}")
        st.write("Debug info:", str(e))

# -----------------------------
# Main app
# -----------------------------

def main():
    # Top row with title and documentation button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🏢 Company Addresses Dashboard")
        st.caption("Insights into companies per address and related metrics.")
    with col2:
        if st.button("📚 Documentation", type="secondary"):
            st.session_state['show_documentation'] = not st.session_state.get('show_documentation', False)
    
    # Show documentation if toggled
    if st.session_state.get('show_documentation', False):
        show_documentation()
        st.divider()

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
        st.dataframe(fdf.head(200), width="stretch")
        st.markdown("**Grouped by postcode (mean)**")
        grouped = fdf.groupby("PostCode_clean").agg({
            "Companies_at_Address": ["mean", "max", "count"],
            "Companies_in_Postcode": "first"
        }).round(2)
        grouped.columns = ["Avg Companies/Address", "Max Companies/Address", "Total Addresses", "Companies in Postcode"]
        st.dataframe(grouped, width="stretch")

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
