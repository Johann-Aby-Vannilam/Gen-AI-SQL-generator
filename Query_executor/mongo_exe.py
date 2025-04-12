import re
import json
import logging
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

class MongoQueryExecutor:
    def __init__(self, db_connection):
        """Initializes MongoQueryExecutor with a MongoDB database connection."""
        self.db_connection = db_connection

    def execute_query(self, query, output_file="output.json"):
        """
        Executes a MongoDB query and returns results in JSON format.
        
        Args:
            query: MongoDB query as a string
            output_file: File path to save JSON results
            
        Returns:
            JSON object with query results or an error message
        """
        try:
            logger.debug(f"🔍 Raw MongoDB Query Received: {query}")

            # Parse the query string
            parsed = self._parse_query_string(query)
            collection_name = parsed['collection']
            operations = parsed['operations']

            logger.debug(f"✅ Extracted Collection: {collection_name}")
            logger.debug(f"🔍 Operations to execute: {operations}")

            # Get the collection reference
            collection = self.db_connection[collection_name]

            # Execute the operations
            result = self._execute_operations(collection, operations)

            # Convert and save results
            result = convert_objectid(result)
            with open(output_file, "w", encoding="utf-8") as json_file:
                json.dump(result, json_file, indent=4)

            return {"status": "success", "data": result, "file": output_file}

        except Exception as e:
            logger.error(f"🚨 Query execution failed: {str(e)}", exc_info=True)
            return {"error": f"Query execution failed: {str(e)}"}

    def _parse_query_string(self, query):
        """Parse the MongoDB query string into its components."""
        query = query.strip()
        
        # Match db.collection.method1().method2()...
        pattern = r"db\.(\w+)\.(\w+)\((.*?)\)(.*)"
        match = re.match(pattern, query)
        if not match:
            raise ValueError("Invalid query format. Expected 'db.collection.method(...)'.")

        collection, first_method, first_args, remaining = match.groups()
        
        operations = [{
            'method': first_method,
            'args': first_args
        }]

        # Parse any remaining method calls
        while remaining.strip():
            next_match = re.match(r"\.(\w+)\((.*?)\)(.*)", remaining)
            if not next_match:
                break
                
            method, args, remaining = next_match.groups()
            operations.append({
                'method': method,
                'args': args
            })

        return {
            'collection': collection,
            'operations': operations
        }

    def _process_query_content(self, content):
        """Process and validate query/projection content."""
        if not content or not content.strip():
            return {}
            
        try:
            # First try parsing as strict JSON
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Handle MongoDB extended JSON format
                fixed_content = self._fix_mongo_json(content)
                return json.loads(fixed_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse query content: {content}")
                raise ValueError(f"Invalid query content: {str(e)}")

    def _fix_mongo_json(self, json_string):
        """Convert MongoDB extended JSON to strict JSON format."""
        if not json_string.strip():
            return "{}"
            
        # Step 1: Convert single quotes to double quotes
        json_string = json_string.replace("'", '"')
        
        # Step 2: Fix unquoted field names (including $ operators)
        json_string = re.sub(
            r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)(\s*:)',
            lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
            json_string
        )
        
        # Step 3: Fix ObjectId and other special cases
        json_string = re.sub(
            r'ObjectId\("([a-f0-9]{24})"\)',
            r'{"$oid": "\1"}',
            json_string
        )
        
        # Step 4: Fix ISODate and other date formats
        json_string = re.sub(
            r'ISODate\("([^"]+)"\)',
            r'{"$date": "\1"}',
            json_string
        )
        
        # Step 5: Handle array elements
        json_string = re.sub(
            r'([\[,])\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*([,\]])',
            lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
            json_string
        )
        
        return json_string

    def _execute_operations(self, collection, operations):
        """Execute a sequence of MongoDB operations."""
        cursor = None
        
        for op in operations:
            method = op['method'].lower()  # Case-insensitive
            args = op['args']
            
            # Process the arguments based on method type
            if method in ('find', 'aggregate', 'count', 'distinct'):
                processed_args = self._process_query_content(args)
            elif method in ('limit', 'skip'):
                processed_args = int(args) if args.strip().isdigit() else args
            else:
                processed_args = args
                
            logger.debug(f"Executing {method} with args: {processed_args}")
            
            # Execute the operation
            if method == 'find':
                cursor = collection.find(processed_args) if processed_args else collection.find()
            elif method == 'aggregate':
                if not isinstance(processed_args, list):
                    processed_args = [processed_args]
                cursor = collection.aggregate(processed_args)
            elif method == 'count':
                return collection.count_documents(processed_args) if processed_args else collection.count_documents()
            elif method == 'distinct':
                field = list(processed_args.keys())[0] if isinstance(processed_args, dict) else processed_args
                return collection.distinct(field)
            elif method == 'limit' and cursor:
                cursor = cursor.limit(processed_args)
            elif method == 'skip' and cursor:
                cursor = cursor.skip(processed_args)
            elif method == 'sort' and cursor:
                cursor = cursor.sort(processed_args)
            else:
                raise ValueError(f"Unsupported method: {method}")

        return list(cursor) if cursor else None

def convert_objectid(doc):
    """Recursively converts ObjectId and datetime fields to strings."""
    if isinstance(doc, list):
        return [convert_objectid(item) for item in doc]
    elif isinstance(doc, dict):
        return {key: convert_objectid(value) for key, value in doc.items()}
    elif isinstance(doc, (ObjectId, datetime)):
        return str(doc)
    return doc