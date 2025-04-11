# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.db import connections,connection
# from Query_executor.postges_exe import QueryExecutor
# from Query_generator import PostgresQueryGenerator, MongoQueryGenerator
# from Connection_db.mongo_con import MongoDBConnection
# import logging
# from uuid import uuid4
# from Query_executor import MongoQueryExecutor
# from django.conf import settings
# from pymongo import MongoClient
# from rest_framework.permissions import AllowAny
# from rest_framework.pagination import LimitOffsetPagination

# logger = logging.getLogger(__name__)

# class GenerateQueryView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         try:
#             logger.debug(f"Parsed request data: {request.data}")
#             user_name = request.data.get('user_name')
#             user_input = request.data.get('user_input')
#             db_selected = request.data.get('db_selected', 'sql').lower()

#             if not user_input or not isinstance(user_input, str) or not user_input.strip():
#                 logger.error("Missing 'user_input' parameter.")
#                 return Response(
#                     {"error": "Missing 'user_input' parameter."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             if db_selected == "sql":
#                 logger.debug("Generating SQL query.")
#                 connection = connections['default']
#                 generator = PostgresQueryGenerator(connection)
#                 sql_query = generator.generate_query(user_input)
#                 logger.debug(f"Generated SQL query: {sql_query}")
#                 self.save_chat_history(user_name, user_input, sql_query, db_selected)
#                 return Response(data={"generated_query": sql_query}, status=status.HTTP_200_OK)
            
#             else:
#                 logger.debug("Generating NoSQL query.")
#                 mongo_host = settings.MONGODB_SETTINGS["HOST"]
#                 database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]
#                 mongo_client = MongoClient(mongo_host)
#                 generator = MongoQueryGenerator(mongo_client, database_name)
#                 logger.debug(f"User input received: {user_input}")  # ✅ Debugging log
#                 no_sql_query = generator.generate_query(user_input)
#                 logger.debug(f"Generated NoSQL query: {no_sql_query}")
#                 self.save_chat_history(user_name, user_input, no_sql_query, db_selected)
#                 return Response(data={"generated_query": no_sql_query}, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.error(f"An error occurred while generating query: {str(e)}", exc_info=True)
#             return Response(
#                 {"error": f"An error occurred: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#     def save_chat_history(self, user_id, user_query, generated_query, database_type):
#         chat_id = str(uuid4())
#         query = """
#             INSERT INTO chat_history (chat_id, user_id, user_query, generated_query, database_type)
#             VALUES (%s, %s, %s, %s, %s)
#         """
#         if isinstance(generated_query, dict):
#             query2 = generated_query.get('query')
#         else:
#             query2 = generated_query
#         with connections['default'].cursor() as cursor:
#             cursor.execute(query, (chat_id, user_id, user_query, query2, database_type))
#             connection.commit()

# class ExecuteQueryView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         """Execute a SQL query and return the result."""
#         try:
#             logger.debug(f"Received request data: {request.data}")
#             generated_query = request.data.get('generated_query')
#             db_selected = request.data.get('db_selected', 'sql').lower()
#             if not generated_query or (isinstance(generated_query, dict) and 'query' not in generated_query):
#                 return Response(
#                     {"error": "Missing 'generated_query' parameter."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # 🔹 Ensure generated_query is a string (adjust this based on actual format)
#             if isinstance(generated_query, dict):
#                 query = generated_query.get('query')
#             else:
#                 query = generated_query

#             if not query:
#                 return Response(
#                     {"error": "Invalid 'generated_query' format. Expected a string or dict with 'query' key."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             if db_selected == "sql":
#                 logger.debug("Executing SQL query.")
#                 # Ensure database connection is open
#                 connection = connections['default']
#                 connection.ensure_connection()  #Reconnect if needed

#                 if not connection.connection:
#                     return Response(
#                         {"error": "Database connection is not available."},
#                         status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                     )

#                 # Execute query
#                 executor = QueryExecutor(connection)
#                 execution_result = executor.execute_query(query)  
#                 logger.debug(f"Query executed successfully: {execution_result}")

#                 return Response(
#                     data={"execution_result": execution_result},
#                     status=status.HTTP_200_OK
#                 )

#             else:
#                 logger.debug("Executing NoSQL (MongoDB) query.")

#                 # Connect to MongoDB
#                 mongo_connection = MongoDBConnection()
#                 mongo_connection.connect()
#                 database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]

#                 # Execute MongoDB query
#                 executor = MongoQueryExecutor(mongo_connection.db)
#                 execution_result = executor.execute_query(query)
#                 logger.debug(f"Query executed successfully: {execution_result}")

#                 # Check if the query execution was successful
#                 if "error" in execution_result:
#                     return Response(
#                         {"error": execution_result["error"]},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#                 elif "data" in execution_result:
#                     return Response(
#                         data={"execution_result": execution_result["data"]},  # Return query result
#                         status=status.HTTP_200_OK
#                     )
#         except Exception as e:
#             logger.error(f"Unexpected error: {str(e)}", exc_info=True)
#             return Response(
#                 {"error": f"An error occurred: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
            

# class ChatSessionView(APIView):
#     permission_classes = [AllowAny]
#     pagination_class = LimitOffsetPagination

#     def get(self, request):
#         """Get paginated chat history"""
#         try:
#             user = request.user.username
#             paginator = self.pagination_class()
            
#             # Get total count
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     "SELECT COUNT(*) FROM chat_history WHERE user_name = %s",
#                     [user]
#                 )
#                 total_count = cursor.fetchone()[0]

#             # Get paginated results
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     """
#                     SELECT id, name, messages, database_type, created_at, last_updated
#                     FROM chat_history
#                     WHERE user_name = %s
#                     ORDER BY last_updated DESC
#                     LIMIT %s OFFSET %s
#                     """,
#                     [user, paginator.get_limit(request), paginator.get_offset(request)]
#                 )
#                 columns = [col[0] for col in cursor.description]
#                 chats = [dict(zip(columns, row)) for row in cursor.fetchall()]

#             return Response({
#                 "results": chats,
#                 "count": total_count,
#                 "next": paginator.get_next_link(),
#                 "previous": paginator.get_previous_link()
#             })

#         except Exception as e:
#             logger.error(f"Chat history error: {str(e)}", exc_info=True)
#             return Response({"error": "Failed to load history"}, status=500)

#     def post(self, request):
#         """Create new chat session"""
#         try:
#             user = request.user.username
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     """
#                     INSERT INTO chat_history 
#                     (user_name, name, messages, database_type)
#                     VALUES (%s, %s, %s, %s)
#                     RETURNING id, created_at
#                     """,
#                     [user, request.data.get('name'), [], 'sql']
#                 )
#                 chat = cursor.fetchone()
                
#             return Response({
#                 "id": chat[0],
#                 "created_at": chat[1].isoformat()
#             }, status=201)

#         except Exception as e:
#             logger.error(f"Chat creation error: {str(e)}")
#             return Response({"error": "Chat creation failed"}, status=500)

# class ChatDetailView(APIView):
#     permission_classes = [AllowAny]

#     def put(self, request, pk):
#         """Update chat session"""
#         try:
#             user = request.user.username
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     """
#                     UPDATE chat_history 
#                     SET 
#                         messages = %s,
#                         database_type = %s,
#                         last_updated = NOW()
#                     WHERE 
#                         id = %s 
#                         AND user_name = %s
#                     RETURNING last_updated
#                     """,
#                     [
#                         request.data.get('messages'),
#                         request.data.get('database_type'),
#                         pk,
#                         user
#                     ]
#                 )
                
#                 if cursor.rowcount == 0:
#                     return Response({"error": "Not found"}, status=404)
                    
#                 last_updated = cursor.fetchone()[0]
                
#             return Response({"last_updated": last_updated.isoformat()})

#         except Exception as e:
#             logger.error(f"Chat update error: {str(e)}")
#             return Response({"error": "Update failed"}, status=500)

#     def delete(self, request, pk):
#         """Delete specific chat"""
#         try:
#             user = request.user.username
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     "DELETE FROM chat_history WHERE id = %s AND user_name = %s",
#                     [pk, user]
#                 )
#             return Response(status=204)
#         except Exception as e:
#             logger.error(f"Chat delete error: {str(e)}")
#             return Response({"error": "Deletion failed"}, status=500)

# class CurrentChatView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request):
#         """Get most recent chat"""
#         try:
#             user = request.user.username
#             with connections['default'].cursor() as cursor:
#                 cursor.execute(
#                     """
#                     SELECT id, name, messages, database_type 
#                     FROM chat_history 
#                     WHERE user_name = %s 
#                     ORDER BY last_updated DESC 
#                     LIMIT 1
#                     """,
#                     [user]
#                 )
#                 chat = cursor.fetchone()
                
#             if not chat:
#                 return Response({"error": "No chats found"}, status=404)

#             return Response({
#                 "id": chat[0],
#                 "name": chat[1],
#                 "messages": chat[2],
#                 "database_type": chat[3]
#             })

#         except Exception as e:
#             logger.error(f"Current chat error: {str(e)}")
#             return Response({"error": "Failed to get current chat"}, status=500)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections, connection
from Query_executor.postges_exe import QueryExecutor
from Query_generator import PostgresQueryGenerator, MongoQueryGenerator
from Connection_db.mongo_con import MongoDBConnection
import logging
from uuid import uuid4
from Query_executor import MongoQueryExecutor
from django.conf import settings
from pymongo import MongoClient
from rest_framework.permissions import AllowAny
import json
from datetime import datetime,date

# Convert datetime objects for JSON serialization
def convert_datetime(obj):
    """Convert datetime and date objects to JSON serializable format."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type not serializable") 

logger = logging.getLogger(__name__)

class GenerateQueryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.debug(f"Parsed request data: {request.data}")
            user_name = request.data.get('user_name')
            user_input = request.data.get('user_input')
            db_selected = request.data.get('db_selected', 'sql').lower()

            if not user_input or not isinstance(user_input, str) or not user_input.strip():
                logger.error("Missing 'user_input' parameter.")
                return Response({"error": "Missing 'user_input' parameter."}, status=status.HTTP_400_BAD_REQUEST)

            if db_selected == "sql":
                logger.debug("Generating SQL query.")
                connection = connections['default']
                generator = PostgresQueryGenerator(connection)
                sql_query = generator.generate_query(user_input)
                logger.debug(f"Generated SQL query: {sql_query}")
                self.save_chat_history(user_name, user_input, sql_query, db_selected)
                return Response(data={"generated_query": sql_query}, status=status.HTTP_200_OK)
            
            else:
                logger.debug("Generating NoSQL query.")
                mongo_host = settings.MONGODB_SETTINGS["HOST"]
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]
                mongo_client = MongoClient(mongo_host)
                generator = MongoQueryGenerator(mongo_client, database_name)
                no_sql_query = generator.generate_query(user_input)
                self.save_chat_history(user_name, user_input, no_sql_query, db_selected)
                return Response(data={"generated_query": no_sql_query}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"An error occurred while generating query: {str(e)}", exc_info=True)
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def save_chat_history(self, user_name, user_query, generated_query, database_type):
        chat_id = str(uuid4())
        query = """
            INSERT INTO chat_history (chat_id, user_name, user_query, generated_query, database_type, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        query2 = generated_query.get('query') if isinstance(generated_query, dict) else generated_query

        with connections['default'].cursor() as cursor:
            cursor.execute(query, (chat_id, user_name, user_query, query2, database_type))
            connection.commit()

class ExecuteQueryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.debug(f"Received request data: {request.data}") 
            generated_query = request.data.get('generated_query')
            db_selected = request.data.get('db_selected', 'sql').lower()
            if not generated_query or (isinstance(generated_query, dict) and 'query' not in generated_query):
                return Response({"error": "Missing 'generated_query' parameter."}, status=status.HTTP_400_BAD_REQUEST)

            query = generated_query.get('query') if isinstance(generated_query, dict) else generated_query

            if not query:
                return Response({"error": "Invalid 'generated_query' format."}, status=status.HTTP_400_BAD_REQUEST)

            if db_selected == "sql":
                logger.debug("Executing SQL query.")
                connection = connections['default']
                connection.ensure_connection()

                if not connection.connection:
                    return Response({"error": "Database connection is not available."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                executor = QueryExecutor(connection)
                execution_result = executor.execute_query(query)
                execution_result_serialized = json.loads(json.dumps(execution_result, default=convert_datetime))

                return Response(data={"execution_result": execution_result_serialized}, status=status.HTTP_200_OK)

            else:
                logger.debug("Executing NoSQL (MongoDB) query.")

                mongo_connection = MongoDBConnection()
                mongo_connection.connect()
                database_name = settings.MONGODB_SETTINGS["DATABASE_NAME"]

                executor = MongoQueryExecutor(mongo_connection.db)
                execution_result = executor.execute_query(query)

                if "error" in execution_result:
                    return Response({"error": execution_result["error"]}, status=status.HTTP_400_BAD_REQUEST)
                elif "data" in execution_result:
                    return Response(data={"execution_result": execution_result["data"]}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_name):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 10)), 100))
            offset = max(0, int(request.query_params.get('offset', 0)))

            count_query = "SELECT COUNT(*) FROM chat_history WHERE user_name = %s"
            with connections['default'].cursor() as cursor:
                cursor.execute(count_query, [user_name])
                total_count = cursor.fetchone()[0]

            query = """
                SELECT chat_id, user_query, generated_query, database_type, created_at
                FROM chat_history
                WHERE user_name = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            with connections['default'].cursor() as cursor:
                cursor.execute(query, (user_name, limit, offset))
                chat_history = cursor.fetchall()

            formatted_history = [
                {"chat_id": chat[0], "user_query": chat[1], "generated_query": chat[2], "database_type": chat[3], "created_at": convert_datetime(chat[4])}
                for chat in chat_history
            ]

            return Response(data={"chat_history": formatted_history, "total_count": total_count}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching chat history: {str(e)}", exc_info=True)
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)