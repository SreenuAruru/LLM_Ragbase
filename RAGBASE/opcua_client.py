import logging
import re
from opcua import Client, Node, ua
from typing import Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize logging
logging.basicConfig(level=logging.INFO)


def connect_to_opcua_server(endpoint: str) -> Optional[Client]:
    """Connects to the OPC UA server and returns the client instance if successful."""
    client = Client(endpoint)
    try:
        client.connect()
        logging.info("Connected to OPC UA Server at %s", endpoint)
        return client
    except Exception as e:
        logging.error("Failed to connect to OPC UA Server: %s", str(e))
        return None


def fetch_all_tags_recursive(node: Node, tags: Dict[str, ua.NodeId]) -> None:
    """Recursively fetch all tags (Variable nodes) and add them to the tags dictionary."""
    try:
        # Get all children of the current node
        children = node.get_children()

        for child in children:
            node_class = child.get_node_class()
            if node_class == ua.NodeClass.Variable:
                # If it's a Variable node (i.e., a tag), get its description and node ID
                description = child.get_description().Text.lower()
                if description:
                    tags[description] = child.nodeid
                    # logging.info("Found tag: '%s', NodeID: %s", description, child.nodeid)
            elif node_class == ua.NodeClass.Object:
                # If it's an Object node (folder), recursively fetch tags from it
                fetch_all_tags_recursive(child, tags)

    except Exception as e:
        logging.error("Error in fetching tags: %s", str(e))


def get_all_opcua_tags(client: Client) -> Dict[str, ua.NodeId]:
    """Get all tags from the OPC UA server by recursively traversing the folder hierarchy."""
    tags = {}
    try:
        root = client.get_root_node()
        objects_folder = root.get_child(["0:Objects"])  # Navigate to the "Objects" folder
        fetch_all_tags_recursive(objects_folder, tags)
        logging.info("All OPC UA tags fetched successfully.")
    except Exception as e:
        logging.error("Error fetching OPC UA tags: %s", str(e))
    return tags


def extract_value_from_text(text: str) -> Optional[float]:
    """Extract numerical value from text (basic regex)."""
    match = re.search(r'\b\d+(\.\d+)?\b', text)  # Match integer or decimal number
    if match:
        return float(match.group(0))
    return None


def advanced_text_matching(text: str, tags: Dict[str, ua.NodeId]) -> Optional[ua.NodeId]:
    """Match text with the tags based on advanced string matching (e.g., cosine similarity)."""
    descriptions = list(tags.keys())
    vectorizer = TfidfVectorizer().fit_transform([text] + descriptions)

    # Compute cosine similarity between the text and each tag description
    cosine_similarities = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()

    # Find the tag with the highest similarity
    max_similarity_idx = np.argmax(cosine_similarities)
    if cosine_similarities[max_similarity_idx] > 0.5:  # Threshold for similarity
        matched_description = descriptions[max_similarity_idx]
        node_id = tags[matched_description]
        logging.info("Advanced match found! Text '%s' matches with tag: '%s'", text, matched_description)
        return node_id
    else:
        logging.info("No significant match found for text: %s", text)
    return None


def update_opcua_tag_value(client: Client, node_id: ua.NodeId, value: float) -> bool:
    """Update the value of the OPC UA tag."""
    try:
        node = client.get_node(node_id)
        node.set_value(value)
        logging.info("Updated tag with Node ID '%s' with new value: %f", node_id, value)
        return True
    except Exception as e:
        logging.error("Error in updating OPC UA tag value: %s", str(e))
    return False


def update_single_node_value(client: Client, answer: str, question: str) -> bool:
    """
    Match the AI-generated answer or the question with the tag descriptions
    and update the corresponding OPC UA tag.
    """
    try:
        logging.info("Processing question: '%s', with answer: '%s'", question, answer)

        # Get all OPC UA tags from the server
        tags = get_all_opcua_tags(client)

        # Match the AI answer or the question with the appropriate OPC UA tag
        node_id = advanced_text_matching(answer, tags) or advanced_text_matching(question, tags)

        if node_id:
            # Extract numerical value from the answer (if any)
            value = extract_value_from_text(answer) or extract_value_from_text(question)
            if value is not None:
                return update_opcua_tag_value(client, node_id, value)

        logging.error("No matching tag found or valid value in answer/question. Exiting.")
        return False
    except Exception as e:
        logging.error("Error in update_single_node_value: %s", str(e))
        return False