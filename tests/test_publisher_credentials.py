import sqlite3
import tempfile
import unittest
from pathlib import Path

from service.publisher_credentials_service import PublisherCredentialsService


class PublisherCredentialsServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.database_path = self.root / "inkaza.db"
        self.key_path = self.root / ".credentials.key"

    def tearDown(self):
        self.temp_directory.cleanup()

    def _service(self):
        return PublisherCredentialsService(self.database_path, self.key_path)

    def test_saves_and_loads_encrypted_credentials(self):
        service = self._service()
        service.save("cliente@inkaza.com.br", "senha-super-secreta")

        loaded = self._service().load()
        self.assertEqual(loaded.login, "cliente@inkaza.com.br")
        self.assertEqual(loaded.password, "senha-super-secreta")
        self.assertTrue(self.key_path.is_file())

        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT login_token, password_token
                  FROM publisher_credentials
                 WHERE id = 1
                """
            ).fetchone()
        self.assertNotIn("cliente@inkaza.com.br", row[0])
        self.assertNotIn("senha-super-secreta", row[1])

    def test_requires_complete_credentials(self):
        service = self._service()
        with self.assertRaisesRegex(ValueError, "login e a senha"):
            service.save("cliente@inkaza.com.br", "")

    def test_clear_removes_saved_credentials(self):
        service = self._service()
        service.save("cliente@inkaza.com.br", "senha")
        service.clear()
        self.assertEqual(service.load().login, "")
        self.assertEqual(service.load().password, "")


if __name__ == "__main__":
    unittest.main()
