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

    
class DBLogin():
    def base(request):
        if request.user.is_authenticated:
            return redirect('database-selection')
        return render(request, 'blog/login_page.html')

    # View for database selection (authenticated users)
    @login_required
    def database_selection(request):
        return render(request, 'blog/db_selection.html')