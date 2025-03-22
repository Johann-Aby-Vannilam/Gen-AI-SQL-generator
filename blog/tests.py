from django.test import TestCase
from django.urls import reverse
from rest_framework import status

class APITests(TestCase):
    def test_chat_response_handler_missing_query_string(self):
        url = reverse('sql_generator')
        response = self.client.post(url, data={}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Missing 'query_string' parameter.")

    def test_chat_response_handler_get(self):
        url = reverse('sql_generator')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Chat API is available. Please use POST to send queries.")

    def test_debug_view(self):
        url = reverse('debug-view')
        response = self.client.post(url, data={'test': 'data'}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('raw_body', response.data)
        self.assertIn('parsed_data', response.data)
