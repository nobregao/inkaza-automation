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
        service.save("cliente@inkaza.com.br", "senha-super-secreta", " licenca-secreta ")

        loaded = self._service().load()
        self.assertEqual(loaded.login, "cliente@inkaza.com.br")
        self.assertEqual(loaded.password, "senha-super-secreta")
        self.assertEqual(loaded.license_key, "licenca-secreta")
        self.assertTrue(self.key_path.is_file())

        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT login_token, password_token, license_token
                  FROM publisher_credentials
                 WHERE id = 1
                """
            ).fetchone()
        self.assertNotIn("cliente@inkaza.com.br", row[0])
        self.assertNotIn("senha-super-secreta", row[1])
        self.assertNotIn("licenca-secreta", row[2])

    def test_migrates_existing_credentials_without_losing_data(self):
        from cryptography.fernet import Fernet

        self.key_path.write_bytes(Fernet.generate_key())
        cipher = Fernet(self.key_path.read_bytes())
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("CREATE TABLE publisher_credentials (id INTEGER PRIMARY KEY, login_token TEXT NOT NULL, password_token TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            connection.execute(
                "INSERT INTO publisher_credentials (id, login_token, password_token) VALUES (1, ?, ?)",
                (cipher.encrypt(b"cliente").decode(), cipher.encrypt(b"senha").decode()),
            )
        service = self._service()
        loaded = service.load()
        self.assertEqual((loaded.login, loaded.password, loaded.license_key), ("cliente", "senha", ""))
        service.save(loaded.login, loaded.password, "nova-licenca")
        self.assertEqual(self._service().load().license_key, "nova-licenca")
        service.save(loaded.login, loaded.password, "outra-licenca")
        self.assertEqual(self._service().load().license_key, "outra-licenca")

    def test_requires_complete_credentials(self):
        service = self._service()
        with self.assertRaisesRegex(ValueError, "login e a senha"):
            service.save("cliente@inkaza.com.br", "")

    def test_clear_removes_saved_credentials(self):
        service = self._service()
        service.save("cliente@inkaza.com.br", "senha", "licenca")
        service.clear()
        self.assertEqual(service.load().login, "")
        self.assertEqual(service.load().password, "")
        self.assertEqual(service.load().license_key, "")


if __name__ == "__main__":
    unittest.main()
