from unittest import TestCase

from handler import handle
from src.container import Services
from tests.helpers import make_event, parse_body


class TestHandlerRouting(TestCase):
    def setUp(self):
        self.services = Services()  # fresh in-memory state for every test

    def test_unknown_resource_returns_404(self):
        response = handle(make_event("GET", "/unknown"), services=self.services)

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(parse_body(response)["error"], "resource_missing")

    def test_wrong_method_returns_405(self):
        response = handle(make_event("DELETE", "/users"), services=self.services)
        self.assertEqual(response["statusCode"], 405)

    def test_request_reaches_controller_and_service(self):
        event = make_event("POST", "/users", body={"name": "Asha", "phone": "9000000001"})

        response = handle(event, services=self.services)

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(parse_body(response)["id"], "user_1")