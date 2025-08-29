import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd
import json
import requests
from typing import Any, Dict, List, Set, Tuple

# Database connection settings
URI = "neo4j+s://iyp.christyquinn.com:7687"
USERNAME = "neo4j"
PASSWORD = "lewagon25omgbbq"

# Connect to Neo4j
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Method Chain Translation API
API_BASE = "http://localhost:8001"

def translate_method_chain(method_chain: str, parameters: dict = None):
    """Translate method chain to Cypher using the translation API"""
    if parameters is None:
        parameters = {}
    
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/translate/method-chain",
            json={
                "method_chain": method_chain,
                "parameters": parameters
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
def run_query(query, max_records=100):
    """Run a Cypher query against Neo4j and return results"""
    try:
        with driver.session() as session:
            # Strip semicolons and whitespace
            query = query.strip().rstrip(';')

            # Add LIMIT to query if not already present
            if "LIMIT" not in query.upper():
                query = f"{query} LIMIT {max_records}"

            results = session.run(query)
            return list(results)
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return []

def get_node_display_info(node):
    """Get the display label and relevant properties for different node types"""
    labels = list(node.labels) if hasattr(node, 'labels') else []
    properties = dict(node) if hasattr(node, 'items') or hasattr(node, '__iter__') else {}

    # Default values
    display_label = "Unknown"
    relevant_props = {}

    # Handle different node types based on labels
    if "Organization" in labels:
        display_label = properties.get('name', f"Organization {node.id}")
        relevant_props = {'name': properties.get('name', 'N/A')}

    elif "AS" in labels:
        asn = properties.get('asn', properties.get('number', 'Unknown'))
        display_label = f"AS{asn}"
        relevant_props = {'asn': asn}

    elif "Country" in labels:
        country_name = properties.get('name', properties.get('country', f"Country {node.id}"))
        display_label = country_name
        relevant_props = {'name': country_name}

    elif "Prefix" in labels:
        prefix = properties.get('prefix', properties.get('name', f"Prefix {node.id}"))
        display_label = prefix
        relevant_props = {'prefix': prefix}

    elif "IXP" in labels:
        ixp_name = properties.get('name', f"IXP {node.id}")
        display_label = ixp_name
        relevant_props = {'name': ixp_name}

    else:
        # For any other node types, use first label or generic name
        if labels:
            display_label = labels[0]
            relevant_props = {'type': labels[0]}
        else:
            display_label = f"Node {node.id}"

    return display_label, relevant_props, labels

def extract_graph_data(results):
    """Extract nodes and relationships from Neo4j query results"""
    nodes = {}  # Store by ID to avoid duplicates
    relationships = []
    table_data = []

    for record in results:
        row_data = {}

        for key in record.keys():
            value = record.get(key)

            if value is None:
                row_data[key] = None
                continue

            # Handle Node objects
            if hasattr(value, "labels") and hasattr(value, "id"):
                display_label, props, labels = get_node_display_info(value)

                nodes[value.id] = {
                    'id': value.id,
                    'display_label': display_label,
                    'labels': labels,
                    'relevant_properties': props,
                    'all_properties': dict(value)
                }
                row_data[key] = display_label

            # Handle Relationship objects
            elif hasattr(value, "type") and hasattr(value, "start_node") and hasattr(value, "end_node"):
                # Skip connecting result nodes as requested
                rel_type = value.type.upper()
                if rel_type not in ["RESULT", "CONNECTS", "LINKS"]:  # Add other connecting types as needed
                    relationships.append({
                        'start_id': value.start_node.id,
                        'end_id': value.end_node.id,
                        'type': value.type,
                        'properties': dict(value)
                    })

                # Make sure we have the connected nodes
                for node in [value.start_node, value.end_node]:
                    if node.id not in nodes:
                        display_label, props, labels = get_node_display_info(node)
                        nodes[node.id] = {
                            'id': node.id,
                            'display_label': display_label,
                            'labels': labels,
                            'relevant_properties': props,
                            'all_properties': dict(node)
                        }

                row_data[key] = f"{value.type} relationship"

            # Handle Path objects
            elif hasattr(value, "nodes") and hasattr(value, "relationships"):
                # Add all nodes from the path
                for node in value.nodes:
                    if node.id not in nodes:
                        display_label, props, labels = get_node_display_info(node)
                        nodes[node.id] = {
                            'id': node.id,
                            'display_label': display_label,
                            'labels': labels,
                            'relevant_properties': props,
                            'all_properties': dict(node)
                        }

                # Add all relationships from the path
                for rel in value.relationships:
                    rel_type = rel.type.upper()
                    if rel_type not in ["RESULT", "CONNECTS", "LINKS"]:
                        relationships.append({
                            'start_id': rel.start_node.id,
                            'end_id': rel.end_node.id,
                            'type': rel.type,
                            'properties': dict(rel)
                        })

                row_data[key] = f"Path with {len(value.nodes)} nodes"

            # Handle lists of nodes/relationships
            elif isinstance(value, list):
                list_display = []
                for item in value:
                    if hasattr(item, "labels") and hasattr(item, "id"):  # Node
                        display_label, props, labels = get_node_display_info(item)
                        nodes[item.id] = {
                            'id': item.id,
                            'display_label': display_label,
                            'labels': labels,
                            'relevant_properties': props,
                            'all_properties': dict(item)
                        }
                        list_display.append(display_label)
                    else:
                        list_display.append(str(item))

                row_data[key] = '; '.join(list_display) if list_display else str(value)

            # Everything else (properties, scalars, etc.)
            else:
                row_data[key] = value

        table_data.append(row_data)

    return list(nodes.values()), relationships, table_data

def create_graph_visualization(nodes, relationships):
    """Build the interactive graph using PyVis"""
    if not nodes:
        return False

    # Create the network
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#2b2b2b",
        font_color="white",
        directed=True
    )

    # Add nodes with proper styling
    for node in nodes:
        # Create a simple tooltip with just the relevant info
        tooltip_parts = [f"ID: {node['id']}"]
        if node['labels']:
            tooltip_parts.append(f"Type: {', '.join(node['labels'])}")

        for key, value in node['relevant_properties'].items():
            tooltip_parts.append(f"{key}: {value}")

        tooltip = '\n'.join(tooltip_parts)

        # Color nodes by type (handle virtual nodes too)
        color = "#4a9eff"  # Default blue
        if node['labels']:
            label = node['labels'][0]
            if label == "AS":
                color = "#ff6b6b"  # Red for AS
            elif label == "Organization":
                color = "#4ecdc4"  # Teal for organizations
            elif label == "Country":
                color = "#45b7d1"  # Light blue for countries
            elif label == "Prefix":
                color = "#96ceb4"  # Green for prefixes
            elif label == "IXP":
                color = "#feca57"  # Yellow for IXPs
            elif label == "Data":
                color = "#9b59b6"  # Purple for aggregated data

        # Make virtual nodes slightly different (dashed border effect via size variation)
        node_size = 25 if node.get('is_virtual', False) else 30

        net.add_node(
            node['id'],
            label=node['display_label'],
            title=tooltip,
            color=color,
            size=node_size
        )

    # Add relationships with clean labels
    added_edges = set()
    for rel in relationships:
        # Create unique edge identifier to avoid duplicates
        edge_key = (rel['start_id'], rel['end_id'], rel['type'])

        if edge_key not in added_edges:
            # Simple relationship tooltip
            rel_tooltip = f"Relationship: {rel['type']}"
            if rel['properties']:
                rel_tooltip += f"\nProperties: {len(rel['properties'])} items"

            net.add_edge(
                rel['start_id'],
                rel['end_id'],
                label=rel['type'],
                title=rel_tooltip,
                color="#888888",
                width=3
            )
            added_edges.add(edge_key)

    # Set up the physics for a clean layout
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.08,
          "damping": 0.4
        },
        "stabilization": {"iterations": 100}
      },
      "edges": {
        "smooth": {
          "enabled": true,
          "type": "continuous"
        },
        "font": {
          "size": 12,
          "color": "white"
        }
      },
      "nodes": {
        "font": {
          "size": 14,
          "color": "white"
        }
      }
    }
    """)

    # Save and display the graph
    net.save_graph("network_graph.html")
    with open("network_graph.html", "r", encoding="utf-8") as f:
        components.html(f.read(), height=650)

    return True

def show_data_table(table_data):
    """Display the results as a clean data table"""
    if not table_data:
        return

    # Clean up the data for display
    clean_data = []
    for row in table_data:
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, list):
                clean_row[key] = '; '.join(str(x) for x in value) if value else ''
            elif isinstance(value, dict):
                clean_row[key] = json.dumps(value, default=str)
            else:
                clean_row[key] = str(value) if value is not None else ''
        clean_data.append(clean_row)

    if clean_data:
        df = pd.DataFrame(clean_data)
        st.dataframe(df, use_container_width=True)

# Main Streamlit interface
st.title("🌐 Network Infrastructure Visualizer")
st.markdown("Query and visualize network data from Neo4j")
# Method Chain Translation Section
st.markdown("---")
st.subheader("🔄 Method Chain Translator")
st.markdown("Convert method chains like `.find.with_organizations.upstream` to Cypher queries")
# Create columns for method chain input

col1, col2, col3 = st.columns([3, 1, 2])
with col1:
    method_chain = st.text_input(
        "Method Chain:",
        placeholder=".find.with_organizations.upstream",
        help="Enter a method chain starting with a dot"
    )

with col2:
    asn_input = st.number_input(
        "ASN:",
        value=15169,
        min_value=1,
        max_value=999999,
        help="Autonomous System Number (commonly needed)"
    )

with col3:
    st.markdown("**Other Parameters (JSON):**")
    parameters_text = st.text_area(
        "Other Parameters:",
        value='{"hops": 2, "limit": 10}',
        height=50,
        label_visibility="collapsed",
        help="Additional parameters like hops, limit, relationship, etc."
    )

# Query input with max records control
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_area(
        "Cypher Query:",
        value="MATCH (n)-[r]->(m) RETURN n,r,m",
        height=100
    )
with col2:
    max_records = st.number_input(
        "Max Records:",
        min_value=1,
        max_value=1000,
        value=50,
        step=10
    )
    
# Translation button and results
if st.button("🔄 Translate Method Chain", type="secondary"):
    if method_chain.strip():
        try:
            # Parse other parameters
            other_parameters = json.loads(parameters_text) if parameters_text.strip() else {}
            
            # Combine ASN with other parameters
            parameters = {"asn": int(asn_input)}
            parameters.update(other_parameters)
            
            # Call translation API
            result = translate_method_chain(method_chain.strip(), parameters)
            
            if result["success"]:
                st.success(f"✅ Translation successful: {result.get('method_chain', 'N/A')}")
                
                # Display the generated Cypher in a code block with copy button
                cypher_code = result["cypher"]
                st.code(cypher_code, language="cypher")
                
                # Add explanation if available
                if result.get("explanation"):
                    st.info(f"💡 **Explanation:** {result['explanation']}")
                
                # Button to copy to main query box
                if st.button("📋 Use This Cypher Query", key="use_cypher"):
                    st.session_state.translated_query = cypher_code
                    st.success("Cypher query copied! Scroll down to see it in the main query box.")
                    
            else:
                st.error(f"❌ Translation failed: {result.get('error', 'Unknown error')}")
                
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON in parameters. Please check the format.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter a method chain")

# Help section for method chains
with st.expander("📚 Method Chain Help"):
    st.markdown("""
    **Available Method Chains:**
    
    - `.find` - Basic node lookup
      - ASN: `15169` (Google)
    
    - `.find.with_organizations` - Include organization details
      - ASN: `15169`
    
    - `.find.upstream` - Find upstream providers
      - ASN: `15169`, Other params: `{"hops": 2}`
    
    - `.find.downstream` - Find downstream customers
      - ASN: `15169`, Other params: `{"hops": 1}`
    
    - `.find.peers` - Find peering partners
      - ASN: `15169`
    
    - `.find.with_relationship` - Custom relationship traversal
      - ASN: `15169`, Other params: `{"relationship": "COUNTRY", "to": "Country"}`
    
    - `.find.limit` - Limit number of results
      - ASN: `15169`, Other params: `{"limit": 10}`
    
    **Complex Chains:**
    - `.find.with_organizations.upstream.limit`
    - `.find.peers.limit`
    - `.find.upstream.with_organizations`
    
    **Parameter Structure:**
    - **ASN Field:** Always included automatically (e.g., 15169)
    - **Other Parameters (JSON):** Optional additional parameters:
    ```json
    {
      "hops": 2,
      "limit": 10,
      "relationship": "COUNTRY",
      "to": "Country"
    }
    ```
    
    **Common ASN Examples:**
    - `15169` - Google
    - `32934` - Facebook/Meta
    - `16509` - Amazon
    - `13335` - Cloudflare
    - `3356` - Level3/CenturyLink
    - `174` - Cogent
    """)

st.markdown("---")

# Query input - check if we have a translated query to use
default_query = "MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10"
if "translated_query" in st.session_state:
    default_query = st.session_state.translated_query
    # Clear it after using
    del st.session_state.translated_query

query = st.text_area(
    "Enter Cypher Query:",
    value=default_query,
    height=100
)

# Example queries
with st.expander("📝 Example Queries"):
    st.code("""
# Nodes and relationships
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10


# Example queries for network data
with st.expander("📋 Common Network Queries"):
    st.code("""
# AS and their prefixes
MATCH (as:AS)-[:ORIGINATE]->(prefix:Prefix) RETURN as, prefix

# Organizations by country
MATCH (org:Organization)-[:COUNTRY]->(country:Country) RETURN org, country

# AS connections through IXPs
MATCH (as1:AS)-[:MEMBER_OF]->(ixp:IXP)<-[:MEMBER_OF]-(as2:AS)
RETURN as1, ixp, as2

# Prefix country relationships
MATCH (prefix:Prefix)-[:COUNTRY]->(country:Country) RETURN prefix, country

# Find specific AS
MATCH (as:AS {asn: 216139})-[r]-(connected) RETURN as, r, connected
    """, language="cypher")

# Execute the query
if st.button("Run Query", type="primary"):
    if not query.strip():
        st.error("Please enter a query")
    else:
        with st.spinner("Running query..."):
            results = run_query(query.strip(), max_records)

            if not results:
                st.warning("No results found")
            else:
                # Process the results
                nodes, relationships, table_data = extract_graph_data(results)

                # Show stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Records", len(results))
                with col2:
                    st.metric("Nodes", len(nodes))
                with col3:
                    st.metric("Relationships", len(relationships))

                # Show the graph
                graph_created = create_graph_visualization(nodes, relationships)
                if graph_created:
                    # Check if we used virtual nodes
                    virtual_count = sum(1 for node in nodes if node.get('is_virtual', False))
                    if virtual_count > 0:
                        st.info(f"📊 Created {virtual_count} virtual nodes from aggregated data")
                    st.success("Graph visualization ready!")
                else:
                    st.info("No graph data to display")

                # Show the data table
                if table_data:
                    st.subheader("Query Results")
                    show_data_table(table_data)

# Sidebar with legend
with st.sidebar:
    st.header("🎨 Node Types")
    st.markdown("""
    **Color Legend:**
    - 🔴 **AS**: Autonomous Systems
    - 🟢 **Prefix**: IP Prefixes
    - 🔵 **Country**: Countries
    - 🟡 **IXP**: Internet Exchange Points
    - 🟦 **Organization**: Organizations

    **Relationship Types:**
    - ORIGINATE: AS → Prefix
    - COUNTRY: Entity → Country
    - MEMBER_OF: AS → IXP
    """)

    st.header("⚙️ Settings")
    st.markdown(f"""
    - Max records: **{max_records}**
    - Connecting relationships: **Hidden**
    - Node labels: **Simplified**

    **🔄 Method Chain Translator:**
    - Convert simple chains like `.find.with_organizations` to Cypher
    - ASN field is always included (e.g., 15169 for Google)
    - Use "Other Parameters" for hops, limits, relationships, etc.
    - Click "Use This Cypher Query" to copy to main query box
    - Check the help section for all available methods
    
    **📊 Query Visualizer:**
    - ✅ Nodes and relationships
    - ✅ Path objects
    - ✅ Collections/lists
    - ✅ Property-only queries
    - ✅ Mixed result types
    - ✅ Complex aggregations

    **🎨 Features:**
    - 🔄 Method chain to Cypher translation
    - 🎨 Auto-colored nodes by label
    - 🔍 Hover for detailed info
    - 📊 Always shows data table
    - 🤖 Creates virtual graphs from scalars
    - 🛠 Debug mode for troubleshooting
    """)

st.markdown("---")
st.caption("Network data visualization tool")
