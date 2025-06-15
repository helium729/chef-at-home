import json

from django.test import Client, TestCase


class HealthCheckTests(TestCase):
    """Test the API health check endpoint"""

    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """Test that the health check endpoint returns expected response"""
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["message"], "FamilyChef API is running")
        self.assertEqual(data["version"], "1.0.0")
