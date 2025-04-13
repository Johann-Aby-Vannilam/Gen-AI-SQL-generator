from django.urls import path
from . import views

urlpatterns = [
    path('generate-query/', views.GenerateQueryView.as_view(), name='generate_query'),  
    path('execute-query/', views.ExecuteQueryView.as_view(), name='execute_query'),  
    path('sessions/', views.ChatSessionView.as_view(), name='chat-sessions'),
    path('sessions/<int:pk>/', views.ChatDetailView.as_view(), name='chat-detail'), 
    path('sessions/current/', views.CurrentChatView.as_view(), name='current-chat'), 

]

