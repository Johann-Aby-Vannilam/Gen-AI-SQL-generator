from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db import connections
from .models import ChatSession, ChatMessage
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
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from .serializers import ChatSessionSerializer, ChatMessageSerializer


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
            connections['default'].connection.commit()
            #connection.commit()

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
        

class ChatSessionView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """Get all chats for current user (paginated)"""
        try:
            user = request.user
            queryset = ChatSession.objects.filter(user=user).order_by('-last_updated')
        
            # Pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
        
            if page is not None:
                serializer = ChatSessionSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = ChatSessionSerializer(queryset, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create new chat session"""
        try:
            with transaction.atomic():
                chat = ChatSession.objects.create(
                    user=request.user,
                    name=request.data.get('name', 'New Chat'),
                    database_type=request.data.get('database_type', 'sql')
                )
                
                ChatMessage.objects.create(
                    session=chat,
                    text="Hello! I can help you generate queries. What would you like to know?",
                    sender='system'
                )
                
                return Response({
                    'id': chat.id,
                    'name': chat.name,
                    'created_at': chat.created_at
                }, status=201)
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=500)

class ChatDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Get single chat with all messages"""
        try:
            chat = ChatSession.objects.get(id=pk, user=request.user)
            messages = chat.messages.all().order_by('timestamp')
            
            return Response({
                'id': chat.id,
                'name': chat.name,
                'database_type': chat.database_type,
                'messages': [
                    {
                        'id': msg.id,
                        'text': msg.text,
                        'sender': msg.sender,
                        'timestamp': msg.timestamp
                    } for msg in messages
                ]
            })
            
        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=404)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=500)

    def put(self, request, pk):
        """Update chat (messages or database type)"""
        try:
            with transaction.atomic():
                chat = ChatSession.objects.get(id=pk, user=request.user)
                
                if 'database_type' in request.data:
                    chat.database_type = request.data['database_type']
                    chat.save()
                
                if 'messages' in request.data:
                    chat.messages.all().delete()
                    for msg in request.data['messages']:
                        ChatMessage.objects.create(
                            session=chat,
                            text=msg['text'],
                            sender=msg['sender'],
                            timestamp=datetime.fromisoformat(msg['timestamp'])
                        )
                
                return Response({
                    'id': chat.id,
                    'last_updated': chat.last_updated
                })
                
        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=404)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=500)

    def delete(self, request, pk):
        """Delete chat session"""
        try:
            chat = ChatSession.objects.get(id=pk, user=request.user)
            chat.delete()
            return Response(status=204)
        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=404)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=500)

class CurrentChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get most recent chat"""
        try:
            chat = ChatSession.objects.filter(user=request.user).order_by('-last_updated').first()
            if not chat:
                return Response({
                    'id': None,
                    'name': None,
                    'database_type': None,
                    'messages': []
                })
                
            serializer = ChatSessionSerializer(chat)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)