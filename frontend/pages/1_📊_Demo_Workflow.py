import streamlit as st
import sys, os, json, pandas as pd
from neo4j import GraphDatabase

# Import utilities from parent directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from utils import run_query, extract_graph_data, create_graph_visualization, show_data_table
except ImportError:
    # Fallback for Streamlit Cloud deployment
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from utils import run_query, extract_graph_data, create_graph_visualization, show_data_table
    except ImportError:
        st.error("Unable to import required utilities. Please check the deployment configuration.")
        st.stop()

# Database connection
URI = os.getenv('NEO4J_URI', 'neo4j+s://iyp.christyquinn.com:7687')
USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD', 'lewagon25omgbbq')
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_page():
    st.title("🧪 Demo Workflow")
    st.markdown("This page shows a simplified workflow with preset Cypher queries and allows custom queries.")

    # --- Custom Cypher Query Section ---
    st.subheader("🔄 Custom Cypher Query")
    query_input = st.text_area(
        "Enter your Cypher query here:",
        placeholder="MATCH (n) RETURN n LIMIT 10",
        height=100,
        key="custom_query_input"
    )

    max_records_input = st.number_input(
        "Max Records:",
        value=50,
        min_value=1,
        max_value=1000,
        key="custom_max_records"
    )

    if st.button("▶️ Run Custom Query", key="run_custom_query"):
        with st.spinner("Running custom query..."):
            if query_input.strip():
                results = run_query(query_input, driver=driver, max_records=max_records_input)
                if results:
                    nodes, relationships, table_data = extract_graph_data(results)
                    st.metric("Nodes", len(nodes))
                    st.metric("Relationships", len(relationships))
                    st.metric("Records", len(table_data))
                    create_graph_visualization(nodes, relationships)
                    show_data_table(table_data)
                else:
                    st.warning("No results found for your query.")
            else:
                st.warning("Please enter a Cypher query first.")

    st.markdown("---")
    st.subheader("📊 Preset Demo Queries")

    # Preset queries
    preset_query_graph = """
CALL {
  MATCH (o:Organization)-[:BASED_IN]->(:Suspected_VirtualOffice)
  MATCH (o)-[:MANAGED_BY]-(a:AS)
  WITH o, collect(DISTINCT a) AS ases
  WHERE size(ases) > 1
  WITH o, ases, size(ases) AS total_managed_ases
  UNWIND ases AS a
  OPTIONAL MATCH (a)-[:ORIGINATE]->(p:Prefix)
  OPTIONAL MATCH (p)-[:COUNTRY]->(c:Country)
  WITH o, total_managed_ases, a,
       count(DISTINCT p) AS total_prefixes,
       count(DISTINCT CASE WHEN c IS NOT NULL THEN p END) AS geolocated_prefixes,
       count(DISTINCT CASE WHEN c.country_code <> 'GB' THEN p END) AS non_uk_prefixes
  WHERE geolocated_prefixes > 0
    AND 1.0 * non_uk_prefixes / geolocated_prefixes > 0.5
  RETURN o, total_managed_ases, collect(DISTINCT a) AS qualifying_ases
  ORDER BY total_managed_ases DESC
  LIMIT 10
}

UNWIND qualifying_ases AS qa
MATCH path = (o)-[r:MANAGED_BY]->(qa)
RETURN path
LIMIT 1000;
"""

    preset_query_table = """
MATCH (o:Organization)-[:BASED_IN]->(:Suspected_VirtualOffice)
MATCH (o)-[:MANAGED_BY]-(a:AS)
WITH o, collect(DISTINCT a) AS ases
WHERE size(ases) > 1
WITH o, ases, size(ases) AS total_managed_ases
UNWIND ases AS a
OPTIONAL MATCH (a)-[:ORIGINATE]->(p:Prefix)
OPTIONAL MATCH (p)-[:COUNTRY]->(c:Country)
WITH
  o, total_managed_ases, a,
  count(DISTINCT p) AS total_prefixes,
  count(DISTINCT CASE WHEN c IS NOT NULL THEN p END) AS geolocated_prefixes,
  count(DISTINCT CASE WHEN c.country_code <> 'GB' THEN p END) AS non_uk_prefixes
WHERE geolocated_prefixes > 0
  AND (1.0 * non_uk_prefixes / geolocated_prefixes) > 0.5
WITH
  o, total_managed_ases,
  collect(DISTINCT a.asn) AS qualifying_asns
WITH
  o, total_managed_ases, qualifying_asns,
  size(qualifying_asns) AS num_qualifying_asns
RETURN
  o.name AS organization,
  o.Accounts_AccountCategory AS account_category,
  o.address_lines AS address_lines,
  total_managed_ases,
  num_qualifying_asns,
  qualifying_asns
ORDER BY total_managed_ases DESC, num_qualifying_asns DESC, organization
LIMIT 10;
"""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Run Graph Demo Query", key="preset_graph"):
            with st.spinner("Running graph demo query..."):
                results = run_query(preset_query_graph, driver=driver, max_records=1000)
                if results:
                    nodes, relationships, table_data = extract_graph_data(results)
                    st.metric("Nodes", len(nodes))
                    st.metric("Relationships", len(relationships))
                    st.metric("Records", len(table_data))
                    create_graph_visualization(nodes, relationships)
                    show_data_table(table_data)
                else:
                    st.warning("No results found for graph query.")

    with col2:
        if st.button("📊 Run Table Demo Query", key="preset_table"):
            with st.spinner("Running table demo query..."):
                results = run_query(preset_query_table, driver=driver, max_records=10)
                if results:
                    _, _, table_data = extract_graph_data(results)
                    st.metric("Records", len(table_data))
                    show_data_table(table_data)
                else:
                    st.warning("No results found for table query.")

# Execute the page function when the script runs
if __name__ == "__main__":
    run_page()
else:
    # For Streamlit pages, the function needs to be called directly
    run_page()
