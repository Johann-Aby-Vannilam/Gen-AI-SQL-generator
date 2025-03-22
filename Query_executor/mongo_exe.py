import re
import json
import logging
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoQueryExecutor:
    def __init__(self, db_connection):
        """
        Initializes MongoQueryExecutor with a MongoDB database connection.
        """
        self.db_connection = db_connection  # ✅ Stores the database connection

    def execute_query(self, query, output_file="output.json"):
        """
        Executes a MongoDB query and returns results in JSON format.

        :param query: MongoDB query as a string (e.g., "db.collection.find({...})" or "db.collection.aggregate([...])").
        :param output_file: File path to save JSON results.
        :return: JSON object with query results or an error message.
        """
        try:
            logger.debug(f"🔍 Raw MongoDB Query Received: {query}")

            match = re.match(r"db\.(\w+)\.(find|aggregate)\((\{.*?\}|\[.*?\])(?:,\s*(\{.*?\}))?\)$", query.strip())
            if not match:
                raise ValueError("Invalid query format. Expected 'db.collection.find({...})' or 'db.collection.aggregate([...])'.")

            collection_name = match.group(1)
            query_type = match.group(2)
            query_content = match.group(3)
            projection_content = match.group(4) if match.group(4) else None

            logger.debug(f"✅ Extracted Collection: {collection_name}, Query Type: {query_type}")
            logger.debug(f"🔍 Extracted Query Content: {query_content}")
            logger.debug(f"🔍 Extracted Projection: {projection_content}")

            # ✅ Auto-fix JSON format dynamically
            query_content = fix_json_keys(query_content)
            if projection_content:
                projection_content = fix_json_keys(projection_content)

            query_dict = json.loads(query_content)
            projection_dict = json.loads(projection_content) if projection_content else None

            logger.debug(f"✅ Parsed Query: {query_dict}")
            logger.debug(f"✅ Parsed Projection: {projection_dict}")

            collection = self.db_connection[collection_name]

            if query_type == "find":
                result = list(collection.find(query_dict, projection_dict if projection_dict else None))
            elif query_type == "aggregate":
                result = list(collection.aggregate(query_dict))
            else:
                raise ValueError(f"Unsupported query type: {query_type}")

            result = convert_objectid(result)

            with open(output_file, "w", encoding="utf-8") as json_file:
                json.dump(result, json_file, indent=4)

            return {"status": "success", "data": result, "file": output_file}

        except Exception as e:
            logger.error(f"🚨 Query execution failed: {str(e)}", exc_info=True)
            return {"error": f"Query execution failed: {str(e)}"}

from datetime import datetime
from bson import ObjectId

def convert_objectid(doc):
    """
    Recursively converts ObjectId and datetime fields to strings in a MongoDB result.
    """
    if isinstance(doc, list):
        return [convert_objectid(item) for item in doc]
    elif isinstance(doc, dict):
        return {key: convert_objectid(value) for key, value in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)  # ✅ Convert ObjectId to string
    elif isinstance(doc, datetime):
        return doc.isoformat()  # ✅ Convert datetime to ISO format string
    else:
        return doc

def fix_json_keys(json_string):
    """
    Fixes MongoDB queries before JSON parsing:
    - Converts single quotes to double quotes.
    - Ensures MongoDB operators (e.g., $group, $match, $lookup) are properly quoted.
    - Ensures field names are quoted.
    - Fixes array elements inside `$concat` where strings need double quotes.
    """
    # ✅ Convert single quotes to double quotes
    json_string = json_string.replace("'", '"')

    # ✅ Fix field names (e.g., {field: 1} → {"field": 1})
    json_string = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_string)

    # ✅ Ensure MongoDB operators ($group, $match, $lookup, etc.) remain quoted
    json_string = re.sub(r'([{,])\s*(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_string)

    # ✅ Fix array elements inside `$concat` where strings need double quotes
    json_string = re.sub(r'(\[\s*)("?\$[a-zA-Z_][a-zA-Z0-9_.]*"?)\s*,\s*("?\s*[^"\$][^,]*\s*"?)\s*,\s*("?\$[a-zA-Z_][a-zA-Z0-9_.]*"?)\s*\]',
                         r'\1"\2", "\3", "\4"]', json_string)

    # ✅ Fix incorrect `$size` usage in `$match`
    json_string = re.sub(r'"(\$size)":\s*\{"(\$gt)":\s*(\d+)\}',
                         r'"$expr": { "\2": [ { "\1": "\3" }, 1 ] }', json_string)

    return json_string








'''import json
import re
from pymongo import MongoClient
import logging
from django.conf import settings
from bson import ObjectId  # ✅ Import ObjectId

logger = logging.getLogger(__name__)

class MongoQueryExecutor:
    def __init__(self, db_connection):
        """
        Initializes MongoQueryExecutor with a MongoDB database connection.
        """
        self.db_connection = db_connection  # ✅ Stores the database connection

    def execute_query(self, query, output_file="output.json"):
        """
        Executes a MongoDB query and returns results in JSON format.

        :param query: MongoDB query as a string (e.g., "db.collection.find({...})" or "db.collection.aggregate([...])").
        :param output_file: File path to save JSON results.
        :return: JSON object with query results or an error message.
        """
        try:
            logger.debug(f"🔍 Raw MongoDB Query Received: {query}")

            # ✅ Updated regex to support both `find({...})` and `aggregate([...])`
            match = re.match(r"db\.(\w+)\.(find|aggregate)\((\{.*?\}|\[.*?\])(?:,\s*(\{.*?\}))?\)$", query.strip())
            if not match:
                raise ValueError("Invalid query format. Expected 'db.collection.find({...})' or 'db.collection.aggregate([...])'.")

            collection_name = match.group(1)  # ✅ Extract collection name
            query_type = match.group(2)       # ✅ Determine query type (find or aggregate)
            query_content = match.group(3)    # ✅ Extract `{...}` or `[...]`
            projection_content = match.group(4) if match.group(4) else "{}"  # ✅ Extract `{...}` projection if present

            logger.debug(f"✅ Extracted Collection: {collection_name}, Query Type: {query_type}")
            logger.debug(f"🔍 Extracted Query Content Before Fixing: {query_content}")
            logger.debug(f"🔍 Extracted Projection Before Fixing: {projection_content}")

            # ✅ Fix missing quotes around field names
            query_content = fix_json_keys(query_content)
            if query_type == "find":
                projection_content = fix_json_keys(projection_content)

            logger.debug(f"🔍 Fixed Query Content: {query_content}")
            logger.debug(f"🔍 Fixed Projection: {projection_content}")

            # ✅ Convert to valid JSON
            query_dict = json.loads(query_content)
            projection_dict = json.loads(projection_content)

            logger.debug(f"✅ Parsed Query: {query_dict}")
            logger.debug(f"✅ Parsed Projection: {projection_dict}")

            # ✅ Step 4: Get MongoDB collection
            collection = self.db_connection[collection_name]

            # ✅ Step 5: Execute MongoDB query
            if query_type == "find":
                result = list(collection.find(query_dict, projection_dict))  # ✅ Apply projection
            elif query_type == "aggregate":
                result = list(collection.aggregate(query_dict))  # ✅ Directly execute aggregation pipeline
            else:
                raise ValueError(f"Unsupported query type: {query_type}")

            # ✅ Step 6: Convert all ObjectId fields to string before returning response
            result = convert_objectid(result)

            # ✅ Step 7: Save results to a JSON file
            with open(output_file, "w", encoding="utf-8") as json_file:
                json.dump(result, json_file, indent=4)

            return {"status": "success", "data": result, "file": output_file}

        except Exception as e:
            logger.error(f"🚨 Query execution failed: {str(e)}", exc_info=True)
            return {"error": f"Query execution failed: {str(e)}"}

def fix_json_keys(json_string):
    """
    Ensures all field names and MongoDB operators in a JSON-like string are properly quoted.
    Handles both normal queries and aggregation pipelines.
    """
    # ✅ Fix standard field names (e.g., {field: 1} → {"field": 1})
    json_string = re.sub(r"([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', json_string)

    # ✅ Ensure MongoDB operators (e.g., $group, $match, $lookup) remain quoted
    json_string = re.sub(r'([{,])\s*(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_string)

    # ✅ Convert single quotes to double quotes
    json_string = json_string.replace("'", '"')

    return json_string

def convert_objectid(doc):
    """
    Recursively converts ObjectId fields to strings in a MongoDB result.
    """
    if isinstance(doc, list):
        return [convert_objectid(item) for item in doc]
    elif isinstance(doc, dict):
        return {key: convert_objectid(value) for key, value in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)  # ✅ Convert ObjectId to string
    else:
        return doc'''
