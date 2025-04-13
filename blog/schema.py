from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


class QueryExecutor():
    def __init__(self, connection):
        super().__init__(connection)
        self.connection = connection
        
    def execute_query(self, query):
        if not query:
            raise ValueError("Empty query provided")
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if query.strip().lower().startswith("select"):
                    return cursor.fetchall()
                return {"status": "success", "rows_affected": cursor.rowcount}
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")