import psycopg2
import json
from psycopg2.extras import DictCursor
from datetime import date, datetime
from decimal import Decimal


def serialize_date(obj):
    """Convert non-serializable objects to a JSON-friendly format."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

class QueryExecutor:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        if self.db_connection is None or not hasattr(self.db_connection, 'connection'):
            raise ValueError("Invalid database connection provided.")

    def execute_query(self, query, params=None, output_file="output.json"):
        if not query:
            raise ValueError("Empty query provided")
        try:
            cursor = self.db_connection.connection.cursor(cursor_factory=DictCursor)
            cursor.execute(query, params)

            # Fetch results if it's a SELECT query
            if query.strip().lower().startswith("select"):
                columns = [desc[0] for desc in cursor.description]  # Extract column names
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]  # Convert to JSON format
                
                # Serialize result and save to JSON file
                with open(output_file, "w", encoding="utf-8") as json_file:
                    json.dump(result, json_file, indent=4, default=serialize_date)

                return json.loads(json.dumps({"status": "success", "data": result, "file": output_file}, default=serialize_date))   # Return JSON response

            # Commit changes for INSERT/UPDATE/DELETE queries
            self.db_connection.connection.commit()
            return {"status": "success", "rows_affected": cursor.rowcount}

        except Exception as e:
            if self.db_connection and hasattr(self.db_connection, 'connection'):
                self.db_connection.connection.rollback()
            raise Exception(f"Query execution failed: {str(e)}")