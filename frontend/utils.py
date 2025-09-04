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
    nodes = {}
    relationships = []
    table_data = []

    for record in results:
        row_data = {}
        for key in record.keys():
            value = record.get(key)
            if value is None:
                row_data[key] = None
                continue
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
            else:
                row_data[key] = value
        table_data.append(row_data)

    return list(nodes.values()), relationships, table_data

def create_graph_visualization(nodes, relationships):
    if not nodes:
        return False

    net = Network(height="750px", width="100%", bgcolor="#1e1e1e", font_color="white", directed=True)
    node_shapes = {"AS": "triangle", "Organization": "box", "Country": "ellipse", "Prefix": "diamond", "IXP": "star", "Data": "dot"}

    for node in nodes:
        tooltip = '\n'.join([f"{k}: {v}" for k, v in node['relevant_properties'].items()])
        color = "#4a9eff"
        label = node['labels'][0] if node['labels'] else "Data"
        shape = node_shapes.get(label, "dot")
        net.add_node(node['id'], label=node['display_label'], title=tooltip, color=color, size=random.randint(25, 35), shape=shape)

    added_edges = set()
    for rel in relationships:
        edge_key = (rel['start_id'], rel['end_id'], rel['type'])
        if edge_key not in added_edges:
            net.add_edge(rel['start_id'], rel['end_id'], label=rel['type'], title=f"Relationship: {rel['type']}", color="#aaaaaa", width=2, arrows="to")
            added_edges.add(edge_key)

    file_path = "network_graph.html"
    net.save_graph(file_path)
    import streamlit.components.v1 as components
    with open(file_path, "r", encoding="utf-8") as f:
        components.html(f.read(), height=750, scrolling=True)
    with open(file_path, "rb") as f:
        st.download_button("📥 Download Graph as HTML", data=f, file_name="network_graph.html", mime="text/html")
    st.markdown(f'🔗 <a href="{file_path}" target="_blank">Open Graph in New Tab</a>', unsafe_allow_html=True)
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
