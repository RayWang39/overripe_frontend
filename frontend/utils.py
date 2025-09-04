# utils.py
import json
import pandas as pd
from pyvis.network import Network
import streamlit as st
import random

from neo4j import GraphDatabase

URI = "neo4j+s://iyp.christyquinn.com:7687"
USERNAME = "neo4j"
PASSWORD = "lewagon25omgbbq"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# utils.py
import streamlit as st

def run_query(query, max_records=100, driver=None):
    """Run a Cypher query against Neo4j and return results"""
    if driver is None:
        st.error("No Neo4j driver provided. Please pass a valid driver.")
        return []

    try:
        with driver.session() as session:
            # Clean up query and add LIMIT if missing
            query = query.strip().rstrip(';')
            if "LIMIT" not in query.upper():
                query = f"{query} LIMIT {max_records}"

            results = session.run(query)
            return list(results)
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return []


def get_node_display_info(node):
    labels = list(node.labels) if hasattr(node, 'labels') else []
    properties = dict(node) if hasattr(node, 'items') or hasattr(node, '__iter__') else {}

    display_label = "Unknown"
    relevant_props = {}

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
                rel_type = value.type.upper()
                if rel_type not in ["RESULT", "CONNECTS", "LINKS"]:
                    relationships.append({
                        'start_id': value.start_node.id,
                        'end_id': value.end_node.id,
                        'type': value.type,
                        'properties': dict(value)
                    })

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
        label = node['labels'][0] if node['labels'] else "Data"
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
    if not table_data:
        return
    clean_data = []
    for row in table_data:
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, list):
                clean_row[key] = '; '.join(str(x) for x in value)
            elif isinstance(value, dict):
                clean_row[key] = json.dumps(value, default=str)
            else:
                clean_row[key] = str(value) if value is not None else ''
        clean_data.append(clean_row)
    if clean_data:
        df = pd.DataFrame(clean_data)
        st.dataframe(df, use_container_width=True)
