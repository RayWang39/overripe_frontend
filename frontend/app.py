import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd
import json
import requests
import os
from typing import Any, Dict, List, Set, Tuple
import html  # for escaping
import importlib
import sys

# Page config - must be first Streamlit command for multipage apps
st.set_page_config(
    page_title="OverRipe - IYP Query & Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Top padding
st.markdown("<br>", unsafe_allow_html=True)

# ASCII banner text
banner_text = r"""
   ____                  ____  ________  ______
  / __ \_   _____  _____/ __ \/  _/ __ \/ ____/
 / / / / | / / _ \/ ___/ /_/ // // /_/ / __/
/ /_/ /| |/ /  __/ /  / _, _// // ____/ /___
\____/ |___/\___/_/  /_/ |_/___/_/   /_____/
"""

# CSS for flicker and neon cyan
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

# Display the banner directly with class reference
st.markdown(f"<p class='banner-text'>{banner_text}</p>", unsafe_allow_html=True)







# Database connection settings - using environment variables with fallbacks
URI = os.getenv('NEO4J_URI', 'neo4j+s://iyp.christyquinn.com:7687')
USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD', 'lewagon25omgbbq')

# Connect to Neo4j
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Method Chain Translation API - using environment variable with fallback
API_BASE = os.getenv('API_BASE_URL', 'https://overripefrontend-production.up.railway.app')

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
                # Skip connecting result nodes
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
    """Build an interactive, dynamic PyVis graph with inline embed + download/open button"""
    if not nodes:
        return False

    import random
    from pyvis.network import Network
    import streamlit.components.v1 as components
    import streamlit as st

    # Create the network
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        directed=True
    )

    # Node shapes by type
    node_shapes = {
        "AS": "triangle",
        "Organization": "box",
        "Country": "ellipse",
        "Prefix": "diamond",
        "IXP": "star",
        "Data": "dot"
    }

    # Add nodes with dynamic properties
    for node in nodes:
        tooltip_parts = [f"ID: {node['id']}"]
        if node['labels']:
            tooltip_parts.append(f"Type: {', '.join(node['labels'])}")
        for key, value in node['relevant_properties'].items():
            tooltip_parts.append(f"{key}: {value}")
        tooltip = '\n'.join(tooltip_parts)

        color = "#4a9eff"  # default
        if node['labels']:
            label = node['labels'][0]
            if label == "AS":
                color = "#ff6b6b"
            elif label == "Organization":
                color = "#4ecdc4"
            elif label == "Country":
                color = "#45b7d1"
            elif label == "Prefix":
                color = "#96ceb4"
            elif label == "IXP":
                color = "#feca57"
            elif label == "Data":
                color = "#9b59b6"

        # Randomize node size for a more organic look
        node_size = random.randint(25, 35) if not node.get('is_virtual', False) else 20

        # Assign shape based on type
        shape = node_shapes.get(label, "dot")

        net.add_node(
            node['id'],
            label=node['display_label'],
            title=tooltip,
            color=color,
            size=node_size,
            shape=shape
        )

    # Add edges
    added_edges = set()
    for rel in relationships:
        edge_key = (rel['start_id'], rel['end_id'], rel['type'])
        if edge_key not in added_edges:
            rel_tooltip = f"Relationship: {rel['type']}"
            if rel['properties']:
                rel_tooltip += f"<br>Properties: {len(rel['properties'])} items"

            net.add_edge(
                rel['start_id'],
                rel['end_id'],
                label=rel['type'],
                title=rel_tooltip,
                color="#aaaaaa",
                width=2,
                arrows="to"
            )
            added_edges.add(edge_key)

    # Force-directed physics for dynamic layout
    net.set_options("""
{
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 150,
      "springConstant": 0.08,
      "damping": 0.4,
      "avoidOverlap": 0.5
    },
    "stabilization": { "iterations": 150 }
  },
  "edges": {
    "smooth": { "enabled": true, "type": "dynamic" },
    "font": { "size": 12, "color": "white" }
  },
  "nodes": {
    "font": { "size": 14, "color": "white" }
  }
}
""")


    # Save graph to HTML
    file_path = "network_graph.html"
    net.save_graph(file_path)

    # Inline embed
    with open(file_path, "r", encoding="utf-8") as f:
        components.html(f.read(), height=750, scrolling=True)

    # Download button
    with open(file_path, "rb") as f:
        st.download_button(
            label="📥 Download Graph as HTML",
            data=f,
            file_name="network_graph.html",
            mime="text/html"
        )

    # Open in new tab link
    st.markdown(
        f'🔗 <a href="{file_path}" target="_blank">Open Graph in New Tab</a>',
        unsafe_allow_html=True
    )

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

                # Get the generated Cypher and parameters
                cypher_code = result["cypher"]
                cypher_params = result.get("parameters", {})

                # Substitute parameters in the Cypher query
                if cypher_params:
                    # Replace parameter placeholders with actual values
                    for param_name, param_value in cypher_params.items():
                        # Handle different parameter formats ($param_0, $asn, etc.)
                        placeholder = f"${param_name}"
                        if isinstance(param_value, str):
                            # For string values, add quotes
                            replacement = f"'{param_value}'"
                        else:
                            # For numeric values, use as-is
                            replacement = str(param_value)
                        cypher_code = cypher_code.replace(placeholder, replacement)

                # Display the generated Cypher with substituted values
                st.code(cypher_code, language="cypher")

                # Add explanation if available
                if result.get("explanation"):
                    st.info(f"💡 **Explanation:** {result['explanation']}")

                # Button to copy to main query box
                if st.button("📋 Use This Cypher Query", key="use_cypher"):
                    st.session_state.query_text = cypher_code
                    st.success("✅ Cypher query copied to the query box below!")

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

# Initialize query text in session state if not present
if "query_text" not in st.session_state:
    st.session_state.query_text = "MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10"

# Query input using session state
query = st.text_area(
    "Enter Cypher Query:",
    value=st.session_state.query_text,
    height=100,
    key="query_input",
    on_change=lambda: setattr(st.session_state, 'query_text', st.session_state.query_input)
)

# Example queries
with st.expander("📝 Example Queries"):
    st.code("""
# Nodes and relationships
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10
""", language="cypher")

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

# Max records control
max_records = st.number_input(
    "Max Records:",
    min_value=1,
    max_value=1000,
    value=50,
    step=10,
    help="Maximum number of records to return from the query"
)

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

                    # Store results in session state for Python interpreter
                    st.session_state.last_results = results
                    st.session_state.last_table_data = table_data
                    st.session_state.last_nodes = nodes
                    st.session_state.last_relationships = relationships

# Python Interpreter Section
st.markdown("---")
st.subheader("🐍 Python Data Analysis")
st.markdown("Analyze query results with Python code")

# Check if we have results to work with
if 'last_table_data' in st.session_state and st.session_state.last_table_data:
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📝 Code Editor", "📊 Data Preview", "📚 Available Variables"])

    with tab1:
        # Python code editor
        python_code = st.text_area(
            "Python Code:",
            value="""# Available variables:
# - df: DataFrame with query results
# - nodes: List of graph nodes
# - relationships: List of graph relationships
# - results: Raw Neo4j results

# Example analysis:
print(f"Total nodes: {len(nodes)}")
print(f"Total relationships: {len(relationships)}")
print(f"\\nDataFrame shape: {df.shape}")
print(f"\\nColumn names: {list(df.columns)}")

# Show first few rows
print("\\nFirst 5 rows:")
print(df.head())

# Example: Count nodes by type
if nodes:
    node_types = {}
    for node in nodes:
        for label in node.get('labels', []):
            node_types[label] = node_types.get(label, 0) + 1
    print("\\nNode counts by type:")
    for node_type, count in sorted(node_types.items()):
        print(f"  {node_type}: {count}")
""",
            height=400,
            help="Write Python code to analyze the query results"
        )

        # Execute button
        if st.button("▶️ Run Python Code", type="secondary"):
            try:
                # Prepare the execution environment
                import sys
                from io import StringIO
                import traceback

                # Capture output
                old_stdout = sys.stdout
                sys.stdout = StringIO()

                # Create execution namespace with available data
                exec_globals = {
                    '__builtins__': __builtins__,
                    'pd': pd,
                    'json': json,
                    'df': pd.DataFrame(st.session_state.last_table_data),
                    'nodes': st.session_state.last_nodes,
                    'relationships': st.session_state.last_relationships,
                    'results': st.session_state.last_results,
                    # Add useful libraries
                    'np': __import__('numpy'),
                    'collections': __import__('collections'),
                    'itertools': __import__('itertools'),
                }

                # Execute the code
                exec(python_code, exec_globals)

                # Get the output
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout

                # Display output
                if output:
                    st.success("✅ Code executed successfully")
                    st.code(output, language="text")
                else:
                    st.info("Code executed but produced no output")

                # Check if any new DataFrames were created
                for key, value in exec_globals.items():
                    if isinstance(value, pd.DataFrame) and key not in ['df', '__builtins__']:
                        st.write(f"**{key}** (DataFrame):")
                        st.dataframe(value, use_container_width=True)

            except Exception as e:
                sys.stdout = old_stdout
                st.error(f"❌ Execution error: {str(e)}")
                st.code(traceback.format_exc(), language="text")

    with tab2:
        # Show data preview
        st.write("**Query Results DataFrame:**")
        df_preview = pd.DataFrame(st.session_state.last_table_data)
        st.dataframe(df_preview, use_container_width=True)

        # Basic statistics
        st.write("**Basic Statistics:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", len(df_preview))
        with col2:
            st.metric("Columns", len(df_preview.columns))
        with col3:
            st.metric("Nodes", len(st.session_state.last_nodes))
        with col4:
            st.metric("Relationships", len(st.session_state.last_relationships))

        # Column info
        st.write("**Column Information:**")
        col_info = pd.DataFrame({
            'Column': df_preview.columns,
            'Type': [str(df_preview[col].dtype) for col in df_preview.columns],
            'Non-Null': [df_preview[col].notna().sum() for col in df_preview.columns],
            'Unique': [df_preview[col].nunique() for col in df_preview.columns]
        })
        st.dataframe(col_info, use_container_width=True)

    with tab3:
        # Show available variables documentation
        st.markdown("""
        ### Available Variables

        The following variables are available in your Python code:

        #### Data Variables
        - **`df`**: Pandas DataFrame containing the query results in tabular format
        - **`nodes`**: List of dictionaries containing node information
          - Each node has: `id`, `labels`, `display_label`, `relevant_properties`, `all_properties`
        - **`relationships`**: List of dictionaries containing relationship information
          - Each relationship has: `start_id`, `end_id`, `type`, `properties`
        - **`results`**: Raw Neo4j query results (list of records)

        #### Pre-imported Libraries
        - **`pd`**: pandas - Data manipulation and analysis
        - **`np`**: numpy - Numerical computing
        - **`json`**: JSON encoder/decoder
        - **`collections`**: Specialized container datatypes
        - **`itertools`**: Functions for creating iterators

        ### Example Code Snippets

        ```python
        # Group and count by a column
        grouped = df.groupby('column_name').size()
        print(grouped)

        # Filter nodes by type
        as_nodes = [n for n in nodes if 'AS' in n.get('labels', [])]
        print(f"Found {len(as_nodes)} AS nodes")

        # Create a new DataFrame
        new_df = pd.DataFrame(nodes)
        print(new_df.head())

        # Network analysis
        from collections import Counter
        relationship_types = Counter(r['type'] for r in relationships)
        print("Relationship type counts:", relationship_types)
        ```
        """)

        # Show example node and relationship structure
        if st.session_state.last_nodes:
            st.write("**Example Node Structure:**")
            st.json(st.session_state.last_nodes[0])

        if st.session_state.last_relationships:
            st.write("**Example Relationship Structure:**")
            st.json(st.session_state.last_relationships[0])

else:
    st.info("👆 Run a query first to enable Python data analysis")

# Sidebar with legend
with st.sidebar:
    st.header("🎨 Node Types")
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
    - ORIGINATE: AS -> Prefix<br>
    - COUNTRY: Entity -> Country<br>
    - MEMBER_OF: AS -> IXP
    """, unsafe_allow_html=True)

    st.header("Settings")
    st.markdown(f"**Max records:** {max_records}  \n**Connecting relationships:** Hidden  \n**Node labels:** Simplified")

    st.write("**Method Chain Translator:**")
    st.write("- Convert simple chains like .find.with_organizations to Cypher")
    st.write("- ASN field is always included (e.g., 15169 for Google)")
    st.write("- Use Other Parameters for hops, limits, relationships, etc.")

    st.write("**Query Visualizer:**")
    st.write("- Nodes and relationships")
    st.write("- Path objects and collections")
    st.write("- Property-only queries")
    st.write("- Complex aggregations")

    st.write("**Python Interpreter:**")
    st.write("- Execute Python code on query results")
    st.write("- Access to pandas DataFrames")
    st.write("- Analyze nodes and relationships")
    st.write("- Built-in numpy, collections, itertools")

    st.write("**Features:**")
    st.write("- Method chain to Cypher translation")
    st.write("- Auto-colored nodes by label")
    st.write("- Hover for detailed info")
    st.write("- Always shows data table")
    st.write("- Python code execution")

st.markdown("---")
st.caption("Network data visualization tool")
