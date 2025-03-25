from django.urls import path
from . import views

urlpatterns = [
    path('generate-query/', views.GenerateQueryView.as_view(), name='generate_query'),  
    path('execute-query/', views.ExecuteQueryView.as_view(), name='execute_query'), 
    path('chat-history/<str:user_name>/', views.ChatHistoryView.as_view(), name='chat_history'),
]
 
