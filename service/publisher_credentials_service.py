from dataclasses import dataclass
from pathlib import Path
import os
import sqlite3

from cryptography.fernet import Fernet, InvalidToken

from helper.system_helper import get_inkaza_data_dir


@dataclass(frozen=True)
class PublisherCredentials:
    login: str = ""
    password: str = ""


class PublisherCredentialsService:
    """Armazena credenciais cifradas no banco local da aplicação."""

    def __init__(
        self,
        database_path: Path | None = None,
        key_path: Path | None = None,
    ):
        data_dir = get_inkaza_data_dir()
        self.database_path = Path(
            database_path or data_dir / "inkaza.db"
        ).expanduser().resolve()
        self.key_path = Path(
            key_path or self.database_path.parent / ".publisher-credentials.key"
        ).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_table()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS publisher_credentials (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    login_token TEXT NOT NULL,
                    password_token TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def load(self) -> PublisherCredentials:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT login_token, password_token
                  FROM publisher_credentials
                 WHERE id = 1
                """
            ).fetchone()
        if row is None:
            return PublisherCredentials()

        cipher = self._cipher(create_key=False)
        try:
            return PublisherCredentials(
                login=cipher.decrypt(row[0].encode("ascii")).decode("utf-8"),
                password=cipher.decrypt(row[1].encode("ascii")).decode("utf-8"),
            )
        except (InvalidToken, ValueError, UnicodeDecodeError) as error:
            raise RuntimeError(
                "Não foi possível descriptografar as credenciais salvas. "
                "Informe-as novamente."
            ) from error

    def save(self, login: str, password: str):
        login = str(login).strip()
        password = str(password)
        if not login and not password:
            self.clear()
            return
        if not login or not password:
            raise ValueError("Informe o login e a senha para salvar o acesso.")

        cipher = self._cipher(create_key=True)
        login_token = cipher.encrypt(login.encode("utf-8")).decode("ascii")
        password_token = cipher.encrypt(password.encode("utf-8")).decode("ascii")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO publisher_credentials (
                    id, login_token, password_token, updated_at
                ) VALUES (1, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    login_token = excluded.login_token,
                    password_token = excluded.password_token,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (login_token, password_token),
            )

    def clear(self):
        with self._connect() as connection:
            connection.execute("DELETE FROM publisher_credentials WHERE id = 1")

    def _cipher(self, create_key: bool) -> Fernet:
        if not self.key_path.exists():
            if not create_key:
                raise RuntimeError(
                    "A chave das credenciais não foi encontrada. "
                    "Informe o login e a senha novamente."
                )
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            self.key_path.write_bytes(Fernet.generate_key())
            try:
                os.chmod(self.key_path, 0o600)
            except OSError:
                pass
        return Fernet(self.key_path.read_bytes())
