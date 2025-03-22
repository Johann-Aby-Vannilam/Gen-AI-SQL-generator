import psycopg2
from psycopg2 import OperationalError
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connections



class PostgresDBConnection:
    def __init__(self):
        """
        Initializes the database connection using Django's default database settings.
        """
        self.connection = connections['default']
        self.cursor = None

    def connect(self):
        """
        Establishes a connection and cursor if not already active.
        """
        if not self.is_cursor_active():
            try:
                self.cursor = self.connection.cursor()
                print("✅ Connected to PostgreSQL via Django settings")
            except OperationalError as e:
                print(f"❌ Connection error: {e}")

    def is_cursor_active(self):
        """
        Checks if the cursor is active and not closed.
        """
        return self.cursor and not self.cursor.closed

    def execute_query(self, query, params=None):
        """
        Executes a given SQL query using the active cursor.

        Args:
            query (str): SQL query to be executed.
            params (list or tuple, optional): Parameters to pass with the query.

        Returns:
            cursor: Cursor after executing the query.
        """
        if not self.is_cursor_active():
            self.connect()

        try:
            self.cursor.execute(query, params)
            return self.cursor
        except Exception as e:
            print(f"❌ Query execution error: {e}")
            raise e

    def close(self):
        """
        Closes the cursor if it is active.
        """
        if self.is_cursor_active():
            self.cursor.close()
            print("🔒 Cursor closed")
