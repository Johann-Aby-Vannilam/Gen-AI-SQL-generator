from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from Query_executor.postges_exe import QueryExecutor
from Query_generator import PostgresQueryGenerator, MongoQueryGenerator
from Connection_db.mongo_con import MongoDBConnection
import logging
import re
from Query_executor import MongoQueryExecutor
from django.conf import settings
from pymongo import MongoClient
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

class GenerateQueryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.debug(f"Parsed request data: {request.data}")
            user_input = request.data.get('user_input')
            db_selected = request.data.get('db_selected', 'sql').lower()

            if not user_input or not isinstance(user_input, str) or not user_input.strip():
                logger.error("Missing 'user_input' parameter.")
                return Response(
                    {"error": "Missing 'user_input' parameter."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if db_selected == "sql":
                logger.debug("Generating SQL query.")
                connection = connections['default']
                generator = PostgresQueryGenerator(connection)
                sql_query = generator.generate_query(user_input)
                logger.debug(f"Generated SQL query: {sql_query}")
                return Response(data={"generated_query": sql_query}, status=status.HTTP_200_OK)
            
            else:
                logger.debug("Generating NoSQL query.")
                mongo_host = settings.MONGODB_SETTINGS["HOST"]
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]
                mongo_client = MongoClient(mongo_host)
                generator = MongoQueryGenerator(mongo_client, database_name)
                logger.debug(f"User input received: {user_input}")  # ✅ Debugging log
                no_sql_query = generator.generate_query(user_input)
                logger.debug(f"Generated NoSQL query: {no_sql_query}")
                return Response(data={"generated_query": no_sql_query}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"An error occurred while generating query: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExecuteQueryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Execute a SQL query and return the result."""
        try:
            logger.debug(f"Received request data: {request.data}")
            generated_query = request.data.get('generated_query')
            db_selected = request.data.get('db_selected', 'sql').lower()
            if not generated_query or (isinstance(generated_query, dict) and 'query' not in generated_query):
                return Response(
                    {"error": "Missing 'generated_query' parameter."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🔹 Ensure generated_query is a string (adjust this based on actual format)
            if isinstance(generated_query, dict):
                query = generated_query.get('query')
            else:
                query = generated_query

            if not query:
                return Response(
                    {"error": "Invalid 'generated_query' format. Expected a string or dict with 'query' key."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if db_selected == "sql":
                logger.debug("Executing SQL query.")
                # Ensure database connection is open
                connection = connections['default']
                connection.ensure_connection()  #Reconnect if needed

                if not connection.connection:
                    return Response(
                        {"error": "Database connection is not available."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # Execute query
                executor = QueryExecutor(connection)
                execution_result = executor.execute_query(query)  
                logger.debug(f"Query executed successfully: {execution_result}")

                return Response(
                    data={"execution_result": execution_result},
                    status=status.HTTP_200_OK
                )

            else:
                logger.debug("Executing NoSQL (MongoDB) query.")

                # Connect to MongoDB
                mongo_connection = MongoDBConnection()
                mongo_connection.connect()
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]

                # Execute MongoDB query
                executor = MongoQueryExecutor(mongo_connection.db)
                execution_result = executor.execute_query(query)
                logger.debug(f"Query executed successfully: {execution_result}")

                # Check if the query execution was successful
                if "error" in execution_result:
                    return Response(
                        {"error": execution_result["error"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif "data" in execution_result:
                    return Response(
                        data={"execution_result": execution_result["data"]},  # Return query result
                        status=status.HTTP_200_OK
                    )
                '''
                logger.debug("Executing NoSQL (MongoDB) query.")

                mongo_connection = MongoDBConnection()
                mongo_connection.connect()
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]

                # Remove reliance on collection name
                executor = MongoQueryExecutor(mongo_connection.db)
                execution_result = executor.execute_query(generated_query)  
                
                logger.debug(f"Query executed successfully: {execution_result}")

                return Response(
                    data={"execution_result": execution_result["data"]},  # ✅ Return query result
                    status=status.HTTP_200_OK
                )'''
                '''logger.debug("Executing NoSQL query.")
                mongo_connection = MongoDBConnection()
                mongo_connection.connect()
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]
                execution_result = mongo_connection.execute_query(database_name, query)  # Replace with actual collection name
                logger.debug(f"Query executed successfully: {execution_result}")

                return Response(
                    data={"execution_result": list(execution_result)},  # Convert cursor to list
                    status=status.HTTP_200_OK
                )
                
                
                elif db_selected == "nosql":
                    logger.debug("Executing NoSQL (MongoDB) query.")

                    # Connect to MongoDB
                    mongo_connection = MongoDBConnection()
                    mongo_connection.connect()
                    database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]

                    # Extract the collection name from the query string
                    collection_match = re.search(r"db\.(\w+)\.aggregate\(", query)
                    if not collection_match:
                        return Response(
                            {"error": "Collection name could not be determined from the query."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    collection_name = collection_match.group(1)

                    # Get the MongoDB collection
                    db_connection = mongo_connection.db[collection_name]

                    # Execute MongoDB query
                    executor = MongoQueryExecutor(db_connection)
                    execution_result = executor.execute_query(query)
                    logger.debug(f"Query executed successfully: {execution_result}")

                    return Response(
                        data={"execution_result": execution_result["data"]},  # Return query result
                        status=status.HTTP_200_OK
                    )
                
                
                '''

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
