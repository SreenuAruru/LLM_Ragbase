from opcua import Server, ua
import random
import time
import logging
import pandas as pd

# Set up logging
logging.basicConfig(filename="opcua_server_updated.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Update the file path to the location of your Excel file
excel_path = r"C:\Users\Sreen\Downloads\tags 2 revised.xlsx"

# Load the Excel file
data = pd.read_excel(excel_path, engine='openpyxl')  # Use openpyxl as the engine

# Filter relevant columns
relevant_columns = ["Tag Number", "Description", "Units"]
tags_data = data[relevant_columns].dropna(subset=["Tag Number"])

# Initialize OPC UA server
server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4841/llmtool/server/")  # Use IPv4 and an alternative port
server.set_server_name("Updated Excel-Based OPC UA Server")

# Set namespace
namespace = server.register_namespace("UpdatedInstrumentNamespace")
objects = server.nodes.objects

# Create a folder for all tags
tags_folder = objects.add_folder(namespace, "Tags")

# Add nodes dynamically based on Excel data
nodes = {}
for index, row in tags_data.iterrows():
    tag_id = row["Tag Number"]
    sanitized_tag_id = tag_id  # Ensure valid identifier by replacing spaces

    # Add the main value variable under the Tags folder
    value_variable = tags_folder.add_variable(namespace, sanitized_tag_id, random.uniform(0.0, 100.0))
    value_variable.set_writable()

    # Add descriptions
    description = row["Description"] if not pd.isna(row["Description"]) else "No description provided."
    unit = row["Units"] if not pd.isna(row["Units"]) else "N/A"
    variable_description = f"{description} Units: {unit}."
    value_variable.set_attribute(ua.AttributeIds.Description, ua.DataValue(ua.LocalizedText(variable_description)))

    # Log the addition of the variable
    print(f"Added tag: {tag_id}, Description: {description}, Units: {unit}")
    logging.info(f"Added tag: {tag_id}, Description: {description}, Units: {unit}")

    # Assign a random increment rate (1, 2, or 0.5)
    increment = random.choice([1, 2, 0.5])

    # Save the variable and increment for updates
    nodes[sanitized_tag_id] = {
        "variable": value_variable,
        "increment": increment,
        "min_range": 0.0,
        "max_range": 100.0,
        "last_value": value_variable.get_value(),  # Initialize the last value
    }

# Start server
server.start()
print(f"Server started at {server.endpoint}")
logging.info("Server started")

try:
    while True:
        # Update tags with their respective increment values every 20 seconds
        for sanitized_tag_id, node_data in nodes.items():
            variable = node_data["variable"]
            increment = node_data["increment"]
            min_range = node_data["min_range"]
            max_range = node_data["max_range"]

            # Get the current value (from client or server)
            current_value = variable.get_value()

            # Check if the client updated the value
            if current_value != node_data["last_value"]:
                print(f"Client updated {sanitized_tag_id}: New Value = {current_value}")
                logging.info(f"Client updated {sanitized_tag_id}: New Value = {current_value}")
                node_data["last_value"] = current_value
                continue  # Skip auto-update this cycle to respect client changes

            # Increment the value
            new_value = current_value + increment
            if new_value > max_range:
                new_value = min_range  # Reset to min if it exceeds max

            # Update the variable
            print(f"Updating {sanitized_tag_id}: {current_value:.2f} -> {new_value:.2f} (Increment: {increment})")
            logging.info(f"Updated {sanitized_tag_id}: {current_value:.2f} -> {new_value:.2f}")
            variable.set_value(new_value)
            node_data["last_value"] = new_value  # Update the last value

        # Wait for 20 seconds before the next update cycle
        time.sleep(200)
except KeyboardInterrupt:
    print("Server stopped")
    logging.info("Server stopped")
finally:
    server.stop()
    logging.info("Server shutdown complete.")
