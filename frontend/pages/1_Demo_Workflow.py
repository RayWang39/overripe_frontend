import streamlit as st
import os
import pandas as pd
from neo4j import GraphDatabase

# Database connection
URI = os.getenv('NEO4J_URI', 'neo4j+s://iyp.christyquinn.com:7687')
USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD', 'lewagon25omgbbq')
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_page():
    # Neon ASCII banner
    st.markdown("<br>", unsafe_allow_html=True)
    banner_text = r"""
   ____                  ____  ________  ______
  / __ \_   _____  _____/ __ \/  _/ __ \/ ____/
 / / / / | / / _ \/ ___/ /_/ // // /_/ / __/
/ /_/ /| |/ /  __/ /  / _, _// // ____/ /___
\____/ |___/\___/_/  /_/ |_/___/_/   /_____/
    """
    st.markdown(
        f"""
        <style>
        @keyframes flicker {{
            0%   {{ opacity:1; }}
            50%  {{ opacity:0.85; }}
            100% {{ opacity:1; }}
        }}
        .banner-text {{
            font-family: 'Courier New', Courier, monospace;
            white-space: pre;
            font-size: 80px;
            color: #0ff;
            text-align: center;
            line-height: 1.1;
            animation: flicker 1.5s infinite;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(f"<p class='banner-text'>{banner_text}</p>", unsafe_allow_html=True)

    st.title("🧪 Demo Workflow")
    st.markdown("This page lets you run Cypher queries and view results as a graph or table.")

    st.subheader("🕸️ Graph Query")
    st.caption("Visualize your Cypher query results as an interactive network graph.")
    graph_query = st.text_area(
        "Enter Cypher query for graph visualization:",
        value=(
            "CALL {\n"
            " MATCH (o:Organization)-[:BASED_IN]->(:Suspected_VirtualOffice)\n"
            " MATCH (o)-[:MANAGED_BY]-(a:AS)\n"
            " WITH o, collect(DISTINCT a) AS ases\n"
            " WHERE size(ases) > 1\n"
            " WITH o, ases, size(ases) AS total_managed_ases\n"
            " UNWIND ases AS a\n"
            " OPTIONAL MATCH (a)-[:ORIGINATE]->(p:Prefix)\n"
            " OPTIONAL MATCH (p)-[:COUNTRY]->(c:Country)\n"
            " WITH\n"
            " o, total_managed_ases, a,\n"
            " count(DISTINCT p) AS total_prefixes,\n"
            " count(DISTINCT CASE WHEN c IS NOT NULL THEN p END) AS geolocated_prefixes,\n"
            " count(DISTINCT CASE WHEN c.country_code <> 'GB' THEN p END) AS non_uk_prefixes\n"
            " WHERE geolocated_prefixes > 0\n"
            " AND 1.0 * non_uk_prefixes / geolocated_prefixes > 0.5\n"
            " WITH o, total_managed_ases, collect(DISTINCT a.asn) AS qualifying_asns\n"
            " WITH o, total_managed_ases, qualifying_asns, size(qualifying_asns) AS num_qualifying_asns\n"
            " ORDER BY total_managed_ases DESC, num_qualifying_asns DESC, o.name\n"
            " LIMIT 10\n"
            " RETURN o, total_managed_ases, num_qualifying_asns, qualifying_asns\n"
            "}\n"
            "UNWIND qualifying_asns AS qasn\n"
            "MATCH p = (o)-[:MANAGED_BY]-(qa:AS {asn: qasn})\n"
            "RETURN\n"
            " p,\n"
            " o.name AS organization,\n"
            " o.Accounts_AccountCategory AS account_category,\n"
            " total_managed_ases,\n"
            " num_qualifying_asns\n"
            "ORDER BY total_managed_ases DESC, num_qualifying_asns DESC, organization\n"
            "LIMIT 1000;"
        ),
        height=200,
        key="graph_query_input"
    )
    graph_max_records = st.number_input(
        "Max Records (Graph):",
        value=50,
        min_value=1,
        max_value=1000,
        key="graph_max_records"
    )
    if st.button("▶️ Run Graph Query"):
        with st.spinner("Running graph query..."):
            results = run_query(graph_query, driver=driver, max_records=graph_max_records)
            if results:
                nodes, relationships, _ = extract_graph_data(results)
                create_graph_visualization(nodes, relationships)
            else:
                st.warning("No results found for your graph query.")

    st.markdown("---")

    st.subheader("📋 Table Query")
    st.caption("View your Cypher query results in a sortable, filterable table.")
    table_query = st.text_area(
        "Enter Cypher query for table view:",
        value=(
            "MATCH (o:Organization)-[:BASED_IN]->(:Suspected_VirtualOffice)\n"
            "MATCH (o)-[:MANAGED_BY]-(a:AS)\n"
            "WITH o, collect(DISTINCT a) AS ases\n"
            "WHERE size(ases) > 1\n"
            "WITH o, ases, size(ases) AS total_managed_ases\n"
            "UNWIND ases AS a\n"
            "OPTIONAL MATCH (a)-[:ORIGINATE]->(p:Prefix)\n"
            "OPTIONAL MATCH (p)-[:COUNTRY]->(c:Country)\n"
            "WITH\n"
            "  o, total_managed_ases, a,\n"
            "  count(DISTINCT p) AS total_prefixes,\n"
            "  count(DISTINCT CASE WHEN c IS NOT NULL THEN p END) AS geolocated_prefixes,\n"
            "  count(DISTINCT CASE WHEN c.country_code <> 'GB' THEN p END) AS non_uk_prefixes\n"
            "WHERE geolocated_prefixes > 0\n"
            "  AND (1.0 * non_uk_prefixes / geolocated_prefixes) > 0.5\n"
            "WITH\n"
            "  o, total_managed_ases,\n"
            "  collect(DISTINCT a.asn) AS qualifying_asns\n"
            "WITH\n"
            "  o, total_managed_ases, qualifying_asns,\n"
            "  size(qualifying_asns) AS num_qualifying_asns\n"
            "RETURN\n"
            "  o.name AS organization,\n"
            "  o.Accounts_AccountCategory AS account_category,\n"
            "  o.address_lines AS address_lines,\n"
            "  total_managed_ases,\n"
            "  num_qualifying_asns,\n"
            "  qualifying_asns\n"
            "ORDER BY total_managed_ases DESC, num_qualifying_asns DESC, organization\n"
            "LIMIT 10;"
        ),
        height=200,
        key="table_query_input"
    )
    table_max_records = st.number_input(
        "Max Records (Table):",
        value=50,
        min_value=1,
        max_value=1000,
        key="table_max_records"
    )
    if st.button("📊 Run Table Query"):
        with st.spinner("Running table query..."):
            results = run_query(table_query, driver=driver, max_records=table_max_records)
            if results:
                _, _, table_data = extract_graph_data(results)
                show_data_table(table_data)
            else:
                st.warning("No results found for your table query.")

    # --- Sidebar legend and info ---
    with st.sidebar:
        st.header("🎨 Node & Relationship Types")
        st.markdown("""
        <div style="line-height: 2.2;">
        <span style="color:#ff6b6b; font-size:22px;">▲</span> <b>AS</b>: Autonomous Systems<br>
        <span style="color:#4ecdc4; font-size:22px;">■</span> <b>Organization</b>: Organizations<br>
        <span style="color:#45b7d1; font-size:22px;">●</span> <b>Country</b>: Countries<br>
        <span style="color:#96ceb4; font-size:22px;">◆</span> <b>Prefix</b>: IP Prefixes<br>
        <span style="color:#feca57; font-size:22px;">★</span> <b>IXP</b>: Internet Exchange Points<br>
        <span style="color:#9b59b6; font-size:22px;">●</span> <b>Data</b>: Data nodes
        </div>
        <br>
        <b>Relationship Types:</b><br>
        - ORIGINATE: AS → Prefix<br>
        - COUNTRY: Entity → Country<br>
        - MEMBER_OF: AS → IXP
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "<div style='color:#0ff; font-size:1.1rem;'><b>💡 Tip:</b> "
            "Try editing the queries or max records to explore different parts of the graph!</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='color:#4a9eff; font-size:1.1rem;'>"
            "This is a <b>demo workflow</b> for experimenting with Cypher queries.<br>"
            "Use the <b>Graph Query</b> to visualize, or the <b>Table Query</b> to inspect data in detail.<br>"
            "Enjoy exploring! 🚀"
            "</div>",
            unsafe_allow_html=True
        )

# Ensure the page runs when selected in Streamlit multipage
if __name__ == "__main__" or True:
    run_page()
