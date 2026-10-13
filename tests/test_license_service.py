import io
import json
import unittest
from datetime import datetime
from unittest.mock import patch
from urllib.error import URLError

from service.license_service import LicenseService, LicenseValidationError, LICENSE_URL
from service.inkaza_publisher_service import InkazaPublisherService


class LicenseServiceTest(unittest.TestCase):
    def validate_payload(self, payload, key="test-key"):
        with patch("service.license_service.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())) as fetch:
            LicenseService().validate(key)
            self.assertEqual(fetch.call_args.args[0].full_url, LICENSE_URL)
            self.assertEqual(fetch.call_args.kwargs["timeout"], 15)

    def test_accepts_active_license_and_trims_input(self):
        self.validate_payload({"test-key": {"active": True, "expires_at": "2099-01-01"}}, " test-key ")

    def test_rejects_missing_key_without_network(self):
        with patch("service.license_service.urlopen") as fetch:
            with self.assertRaises(LicenseValidationError):
                LicenseService().validate(" ")
            fetch.assert_not_called()

    def test_rejects_unknown_inactive_expired_and_malformed_licenses(self):
        for payload in [[], {}, {"test-key": None}, *[
            {"test-key": record} for record in [
                {"active": False, "expires_at": "2099-01-01"},
                {"active": "true", "expires_at": "2099-01-01"},
                {"active": True, "expires_at": "2000-01-01"},
                {"active": True},
                {"active": True, "expires_at": "invalid"},
                {"active": True, "expires_at": None},
            ]
        ]]:
            with self.subTest(payload=payload), self.assertRaises(LicenseValidationError):
                self.validate_payload(payload)

    def test_valid_through_expiry_day_in_recife(self):
        with patch("service.license_service.datetime") as clock:
            clock.strptime.side_effect = datetime.strptime
            clock.now.return_value = datetime(2026, 10, 22, 23, 59)
            self.validate_payload({"test-key": {"active": True, "expires_at": "2026-10-22"}})

    def test_blocks_network_errors_and_invalid_json(self):
        with patch("service.license_service.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(LicenseValidationError):
                LicenseService().validate("test-key")
        with patch("service.license_service.urlopen", return_value=io.BytesIO(b"not json")):
            with self.assertRaises(LicenseValidationError):
                LicenseService().validate("test-key")

    def test_checks_again_for_each_attempt(self):
        with patch("service.license_service.urlopen", side_effect=[
            io.BytesIO(b'{"test-key":{"active":true,"expires_at":"2099-01-01"}}'),
            io.BytesIO(b'{"test-key":{"active":false,"expires_at":"2099-01-01"}}'),
        ]) as fetch:
            service = LicenseService()
            service.validate("test-key")
            with self.assertRaises(LicenseValidationError):
                service.validate("test-key")
            self.assertEqual(fetch.call_count, 2)

    def test_publisher_stops_before_browser_and_reports_on_license_failure(self):
        with patch("service.inkaza_publisher_service.LicenseService.validate", side_effect=LicenseValidationError("blocked")) as validate, patch("playwright.sync_api.sync_playwright") as browser:
            with self.assertRaises(LicenseValidationError):
                InkazaPublisherService().publish_all([], license_key="test-key")
            validate.assert_called_once_with("test-key")
            browser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
