import logging
import random
import time
import threading
import pandas as pd
from datetime import datetime
from opcua import Server , ua
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from tabulate import tabulate

from flask import Flask, jsonify, request
import threading

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

anomalies_data = []

# Load Excel file and handle missing columns
EXCEL_PATH = "C:\\Users\\Sreen\\Downloads\\tags 2 revised.xlsx"
try:
    data = pd.read_excel(EXCEL_PATH, engine="openpyxl", header=0)

    # Extract relevant columns
    column_mapping = {
        "Loop": "Parent Tag",
        "Tag Number": "Tag ID",
        "Description": "Description",
        "Units": "Units",
    }
    data = data.rename(columns=column_mapping)
    data = data[list(column_mapping.values())]

    # Handle missing values
    data["Parent Tag"] = data["Parent Tag"].fillna("No Parent").str.strip()
    data["Units"] = data["Units"].fillna("-").str.strip()

except Exception as e:
    logging.error(f"Error loading Excel file: {e}")
    raise

# Log Excel data for debugging
logging.info(f"Loaded Excel Data:\n{data.head()}")

# OPC UA Server Setup
server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4842/freeopcua/server/")
server.set_server_name("OPC UA Server with Anomaly Detection")
uri = "http://example.org"
idx = server.register_namespace(uri)
objects = server.nodes.objects

# Global variables
tag_objects = {}
parent_structure = {}

# Dynamically create OPC UA nodes
for _, row in data.iterrows():
    parent_tag = row["Parent Tag"]
    tag_id = str(row["Tag ID"])
    units = row["Units"]
    description = row["Description"] if not pd.isna(row["Description"]) else "No description provided."

    # Log each tag and parent tag for debugging
    logging.info(f"Processing Tag: {tag_id}, Parent Tag: {parent_tag}, Units: {units}, Description: {description}")

    # Create parent tag node if it does not exist
    if parent_tag not in tag_objects:
        tag_objects[parent_tag] = objects.add_object(idx, parent_tag)
        parent_structure[parent_tag] = []

    # Add tag variable under the parent tag node
    obj = tag_objects[parent_tag]
    var = obj.add_variable(idx, tag_id, 0.0)  # Initialize with 0.0
    var.set_writable()

    variable_description = f"{description} Tag: {tag_id}."
    var.set_attribute(ua.AttributeIds.Description, ua.DataValue(ua.LocalizedText(variable_description)))

    # Store metadata for monitoring
    parent_structure[parent_tag].append({
        "tag_id": tag_id,
        "variable": var,
        "value": 0.0,
        "units": units,
        "description": description
    })

logging.info("All tags dynamically added to OPC UA server.")

# Function to monitor tags, update values, and detect anomalies
def monitor_tags():
    scaler = StandardScaler()
    model = IsolationForest(contamination=0.1, random_state=42)

    while True:
        current_data = []
        for parent_tag, tags in parent_structure.items():
            for tag in tags:
                # Generate a random value for the tag
                value = round(random.uniform(10, 500), 2)
                tag["value"] = value  # Update tag value
                tag["variable"].set_value(value)  # Update OPC UA variable
                # Append data for anomaly detection
                current_data.append({
                    "Parent Tag": parent_tag,
                    "Tag": tag["tag_id"],
                    "Value": value,
                    "Deviation": abs(value - 50),
                    "Units": tag["units"],
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        # Convert current data to DataFrame
        tag_data = pd.DataFrame(current_data)
        logging.info(f"Generated DataFrame Columns: {list(tag_data.columns)}")

        # Detect anomalies
        if not tag_data.empty:
            features = ["Value", "Deviation"]
            scaled_data = scaler.fit_transform(tag_data[features])

            # Add 'Anomaly' column to the DataFrame
            tag_data["Anomaly"] = model.fit_predict(scaled_data)

            # Extract anomalies
            anomalies = tag_data[tag_data["Anomaly"] == -1].copy()

            # Log detected anomalies in a tabular format
            if not anomalies.empty:
                anomalies_table = tabulate(
                    anomalies[["Parent Tag", "Tag", "Value", "Deviation", "Units", "Timestamp"]],
                    headers="keys",
                    tablefmt="grid",
                    showindex=False
                )
                logging.info(f"Detected Anomalies:\n{anomalies_table}")

        time.sleep(200)  # Update every 15 seconds

# Start OPC UA server
def start_server():
    try:
        server.start()
        logging.info("OPC UA Server started. Monitoring tags...")
        monitor_tags()
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server.stop()
        logging.info("OPC UA Server stopped.")

# Function to monitor tags and store anomalies
def monitor_tags_with_api():
    scaler = StandardScaler()
    model = IsolationForest(contamination=0.1, random_state=42)

    global anomalies_data

    while True:
        current_data = []
        for parent_tag, tags in parent_structure.items():
            for tag in tags:
                # Generate a random value for the tag
                value = round(random.uniform(10, 500), 2)
                tag["value"] = value  # Update tag value
                tag["variable"].set_value(value)  # Update OPC UA variable
                # Append data for anomaly detection
                current_data.append({
                    "Parent Tag": parent_tag,
                    "Tag": tag["tag_id"],
                    "Value": value,
                    "Deviation": abs(value - 50),
                    "Units": tag["units"],
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        # Convert current data to DataFrame
        tag_data = pd.DataFrame(current_data)

        # Detect anomalies
        if not tag_data.empty:
            features = ["Value", "Deviation"]
            scaled_data = scaler.fit_transform(tag_data[features])

            # Add 'Anomaly' column to the DataFrame
            tag_data["Anomaly"] = model.fit_predict(scaled_data)

            # Extract anomalies
            anomalies = tag_data[tag_data["Anomaly"] == -1].copy()

            # Update global anomalies data
            anomalies_data = anomalies.to_dict(orient="records")

        time.sleep(200)  # Update every 15 seconds

# Flask APIs
@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    """
    Fetch the latest anomalies detected by the OPC UA server.
    """
    return jsonify({"anomalies": anomalies_data})

@app.route("/api/anomalies/filter", methods=["POST"])
def filter_anomalies():
    """
    Filter anomalies based on specific criteria (e.g., Parent Tag or Tag ID).
    Request JSON:
    {
        "parent_tag": "Parent_Tag_Name",  # Optional
        "tag_id": "Tag_ID_Name"          # Optional
    }
    """
    criteria = request.json
    filtered_anomalies = anomalies_data

    if "parent_tag" in criteria:
        filtered_anomalies = [a for a in filtered_anomalies if a["Parent Tag"] == criteria["parent_tag"]]
    if "tag_id" in criteria:
        filtered_anomalies = [a for a in filtered_anomalies if a["Tag"] == criteria["tag_id"]]

    return jsonify({"filtered_anomalies": filtered_anomalies})

# Start Flask app in a separate thread
def start_api_server():
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    # Start the Flask API server
    threading.Thread(target=start_api_server, daemon=True).start()

    # Start the OPC UA server and monitoring with anomaly detection
    threading.Thread(target=start_server, daemon=True).start()

    # Run monitoring with API integration
    monitor_tags_with_api()