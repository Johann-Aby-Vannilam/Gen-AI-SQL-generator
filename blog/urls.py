from django.urls import path
from . import views

urlpatterns = [
    #path('sql/', views.ChatResponseHandler.as_view(), name='sql_generator'),  # Existing endpoint
    path('generate-query/', views.GenerateQueryView.as_view(), name='generate_query'),  # New endpoint for generating queries
    path('execute-query/', views.ExecuteQueryView.as_view(), name='execute_query'),  # New endpoint for executing queries
]

