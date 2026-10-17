from unittest import TestCase

from handler import handle
from tests.helpers import make_event, parse_body


class TestHandlerRouting(TestCase):
    def test_unknown_resource_returns_404(self):
        response = handle(make_event("GET", "/unknown"))

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(parse_body(response)["error"], "resource_missing")