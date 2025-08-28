

import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd
import json
from typing import Any, Dict, List, Set, Tuple


# CONNECT TO NEO4J DATABASE

URI = "neo4j+s://iyp.christyquinn.com:7687"
USERNAME = "neo4j"
PASSWORD = "lewagon25omgbbq"

# Initialize driver
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_query(query):
    """Execute Cypher query and return results"""
    try:
        with driver.session() as session:
            results = session.run(query)
            return list(results)
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return []

def extract_graph_elements(results):
    """Extract nodes and relationships from any Neo4j query results"""
    nodes = {}  # Use dict to avoid duplicates by ID
    relationships = []
    scalar_data = []

    for record in results:
        row_data = {}

        for key in record.keys():
            value = record.get(key)

            if value is None:
                row_data[key] = None
                continue

            # Handle Neo4j Node objects
            if hasattr(value, "labels") and hasattr(value, "id"):
                nodes[value.id] = {
                    'id': value.id,
                    'labels': list(value.labels),
                    'properties': dict(value)
                }
                row_data[key] = f"Node({value.id})"

            # Handle Neo4j Relationship objects
            elif hasattr(value, "type") and hasattr(value, "start_node") and hasattr(value, "end_node"):
                relationships.append({
                    'start_id': value.start_node.id,
                    'end_id': value.end_node.id,
                    'type': value.type,
                    'properties': dict(value),
                    'id': getattr(value, 'id', None)
                })
                # Also add the connected nodes if not already present
                for node in [value.start_node, value.end_node]:
                    if node.id not in nodes:
                        nodes[node.id] = {
                            'id': node.id,
                            'labels': list(node.labels) if hasattr(node, 'labels') else [],
                            'properties': dict(node) if hasattr(node, 'items') else {}
                        }
                row_data[key] = f"Relationship({value.type})"

            # Handle Neo4j Path objects
            elif hasattr(value, "nodes") and hasattr(value, "relationships"):
                # Extract nodes from path
                for node in value.nodes:
                    nodes[node.id] = {
                        'id': node.id,
                        'labels': list(node.labels),
                        'properties': dict(node)
                    }
                # Extract relationships from path
                for rel in value.relationships:
                    relationships.append({
                        'start_id': rel.start_node.id,
                        'end_id': rel.end_node.id,
                        'type': rel.type,
                        'properties': dict(rel),
                        'id': getattr(rel, 'id', None)
                    })
                row_data[key] = f"Path({len(value.nodes)} nodes, {len(value.relationships)} rels)"

            # Handle lists that might contain nodes/relationships
            elif isinstance(value, list):
                list_items = []
                for item in value:
                    if hasattr(item, "labels") and hasattr(item, "id"):  # Node in list
                        nodes[item.id] = {
                            'id': item.id,
                            'labels': list(item.labels),
                            'properties': dict(item)
                        }
                        list_items.append(f"Node({item.id})")
                    elif hasattr(item, "type") and hasattr(item, "start_node"):  # Relationship in list
                        relationships.append({
                            'start_id': item.start_node.id,
                            'end_id': item.end_node.id,
                            'type': item.type,
                            'properties': dict(item),
                            'id': getattr(item, 'id', None)
                        })
                        list_items.append(f"Relationship({item.type})")
                    else:
                        list_items.append(str(item))
                row_data[key] = list_items if list_items else value

            # Handle everything else (scalars, dicts, etc.)
            else:
                row_data[key] = value

        scalar_data.append(row_data)

    return list(nodes.values()), relationships, scalar_data

def create_virtual_graph_from_scalars(scalar_data, query):
    """Create virtual nodes from scalar data when no graph objects are present"""
    nodes = []
    relationships = []

    # Try to detect if we can create meaningful virtual nodes
    if not scalar_data:
        return nodes, relationships

    # Strategy 1: If query mentions specific node labels, create virtual nodes
    query_lower = query.lower()
    node_labels = []
    common_labels = ['organization', 'person', 'company', 'user', 'product', 'location', 'city', 'country']

    for label in common_labels:
        if label in query_lower:
            node_labels.append(label.title())

    if not node_labels:
        node_labels = ['Entity']

    # Create virtual nodes from each row
    for i, row in enumerate(scalar_data):
        # Find the most likely identifier
        identifier = None
        display_props = {}

        for key, value in row.items():
            if value is not None:
                # Common identifier fields
                if any(id_field in key.lower() for id_field in ['id', 'name', 'title', 'email']):
                    if isinstance(value, (str, int)) and not identifier:
                        identifier = str(value)
                display_props[key] = value

        if not identifier:
            identifier = f"Record_{i+1}"

        # Create virtual node
        virtual_node = {
            'id': f"virtual_{i}",
            'labels': node_labels,
            'properties': display_props,
            'virtual_identifier': identifier
        }
        nodes.append(virtual_node)

    return nodes, relationships

def visualize_graph(nodes, relationships, scalar_data, query):
    """Create and display the graph visualization"""

    # If no graph objects but we have data, try to create virtual graph
    if not nodes and not relationships and scalar_data:
        nodes, relationships = create_virtual_graph_from_scalars(scalar_data, query)

    if not nodes and not relationships:
        return False  # No graph to show

    # Initialize PyVis network
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        directed=True
    )

    # Add nodes
    added_nodes = set()
    for node in nodes:
        if node['id'] not in added_nodes:
            # Determine node label
            if node['labels']:
                display_label = node['labels'][0]
            else:
                display_label = "Node"

            # For virtual nodes, use the identifier
            if 'virtual_identifier' in node:
                display_label = node['virtual_identifier']

            # Create hover title with all info
            title_parts = [f"ID: {node['id']}"]
            if node['labels']:
                title_parts.append(f"Labels: {', '.join(node['labels'])}")

            if node['properties']:
                title_parts.append("Properties:")
                for k, v in node['properties'].items():
                    if isinstance(v, list):
                        v_str = '; '.join(str(x) for x in v)
                    else:
                        v_str = str(v)
                    title_parts.append(f"  {k}: {v_str}")

            title = '\n'.join(title_parts)

            # Color coding by label
            color = "#97C2FC"  # Default blue
            if node['labels']:
                label_hash = hash(node['labels'][0]) % 10
                colors = ["#97C2FC", "#FFAB91", "#C5E1A5", "#F8BBD9", "#FFE082",
                         "#BCAAA4", "#B39DDB", "#80CBC4", "#FFCC02", "#FF8A65"]
                color = colors[label_hash]

            net.add_node(
                node['id'],
                label=display_label,
                title=title,
                color=color,
                size=25
            )
            added_nodes.add(node['id'])

    # Add relationships
    for rel in relationships:
        if rel['start_id'] in added_nodes and rel['end_id'] in added_nodes:
            # Create relationship title
            title_parts = [f"Type: {rel['type']}"]
            if rel['properties']:
                title_parts.append("Properties:")
                for k, v in rel['properties'].items():
                    title_parts.append(f"  {k}: {str(v)}")
            rel_title = '\n'.join(title_parts)

            net.add_edge(
                rel['start_id'],
                rel['end_id'],
                label=rel['type'],
                title=rel_title,
                color="#666666",
                arrows="to",
                width=2
            )

    # Configure physics for better layout
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08,
          "damping": 0.4
        },
        "stabilization": {"iterations": 150}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200
      }
    }
    """)

    # Save and display
    net.save_graph("graph.html")
    with open("graph.html", "r", encoding="utf-8") as f:
        components.html(f.read(), height=650)

    return True

def display_table_results(scalar_data):
    """Display results in table format"""
    if not scalar_data:
        return

    # Convert to DataFrame for better display
    df_data = []
    for row in scalar_data:
        formatted_row = {}
        for key, value in row.items():
            if isinstance(value, list):
                # Handle arrays nicely
                formatted_row[key] = '; '.join(str(x) for x in value) if value else ''
            elif isinstance(value, dict):
                # Handle objects
                formatted_row[key] = json.dumps(value, default=str)
            else:
                formatted_row[key] = str(value) if value is not None else ''
        df_data.append(formatted_row)

    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.title("🔗 Neo4j Graph Integration")
st.markdown("Handles any Neo4j query")

# Query input
query = st.text_area(
    "Enter Cypher Query:",
    value="MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10",
    height=100
)

# Example queries
with st.expander("📝 Example Queries"):
    st.code("""
# Nodes and relationships
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 10

# Just nodes
MATCH (o:Organization) RETURN o LIMIT 25

# Properties only (will show table + virtual graph)
MATCH (o:Organization) RETURN o.name, o.address_lines LIMIT 25

# Paths
MATCH p = (n)-[*1..3]-(m) RETURN p LIMIT 5

# Complex aggregations
MATCH (n:Person)-[r:WORKS_AT]->(o:Organization)
RETURN o.name, collect(n.name) as employees, count(r) as employee_count

# Mixed results
MATCH (p:Person)-[r]-(o:Organization)
RETURN p, r.type as relationship_type, o.name as org_name
    """, language="cypher")

# Execute query
if st.button("🚀 Run Query", type="primary"):
    if not query.strip():
        st.error("Please enter a query")
    else:
        with st.spinner("Executing query..."):
            results = run_query(query.strip())

            if not results:
                st.warning("No results returned from query")
            else:
                # Extract all possible elements
                nodes, relationships, scalar_data = extract_graph_elements(results)

                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Records", len(results))
                with col2:
                    st.metric("🔵 Nodes", len(nodes))
                with col3:
                    st.metric("🔗 Relationships", len(relationships))

                # Try to create graph visualization
                graph_created = visualize_graph(nodes, relationships, scalar_data, query)

                # Always show table data if available
                if scalar_data:
                    st.subheader("📋 Data Table")
                    display_table_results(scalar_data)

                # Show raw results in expandable section for debugging
                with st.expander("🔍 Raw Query Results (Debug)"):
                    for i, record in enumerate(results):
                        st.write(f"**Record {i+1}:**")
                        for key in record.keys():
                            value = record.get(key)
                            st.write(f"  - `{key}`: {type(value).__name__} = {repr(value)}")

# Helpful tips
with st.sidebar:
    st.header("💡 Tips")
    st.markdown("""
    **This visualizer handles:**
    - ✅ Nodes and relationships
    - ✅ Path objects
    - ✅ Collections/lists
    - ✅ Property-only queries
    - ✅ Mixed result types
    - ✅ Complex aggregations

    **Features:**
    - 🎨 Auto-colored nodes by label
    - 🔍 Hover for detailed info
    - 📊 Always shows data table
    - 🤖 Creates virtual graphs from scalars
    - 🛠 Debug mode for troubleshooting
    """)

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit, Neo4j, and PyVis*")
