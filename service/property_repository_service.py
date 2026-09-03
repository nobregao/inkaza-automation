import json
import mimetypes
import shutil
import sqlite3
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from helper.system_helper import get_inkaza_data_dir


class PropertyRepositoryService:
    FILE_FIELDS = {
        "SEO_IMAGE": ("seo_image", False),
        "TITLE_IMAGE": ("imagem_titulo", False),
        "THREE_D_IMAGE": ("imagem_3d", False),
        "GALLERY_IMAGE": ("galeria", True),
        "DOCUMENT": ("documentos", True),
    }
    ALLOWED_MIME_TYPES = {
        "TITLE_IMAGE": {"image/jpeg", "image/png", "image/webp"},
        "GALLERY_IMAGE": {"image/jpeg", "image/png", "image/webp"},
        "DOCUMENT": {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
    }

    def __init__(self, database_path: Path | None = None):
        self.database_path = Path(
            database_path or get_inkaza_data_dir() / "inkaza.db"
        ).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.media_dir = self.database_path.parent / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS properties (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    address TEXT NOT NULL,
                    category TEXT NOT NULL,
                    property_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'NOT_SYNC',
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._add_missing_columns(connection)
            self._migrate_uuid_ids(connection)
            self._migrate_normalized_values(connection)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS property_files (
                    id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    relative_path TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
                )
                """
            )

    @staticmethod
    def _add_missing_columns(connection):
        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(properties)").fetchall()
        }
        migrations = {
            "address": "TEXT NOT NULL DEFAULT ''",
            "category": "TEXT NOT NULL DEFAULT ''",
            "property_type": "TEXT NOT NULL DEFAULT ''",
            "status": "TEXT NOT NULL DEFAULT 'NOT_SYNC'",
        }
        for column, definition in migrations.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE properties ADD COLUMN {column} {definition}"
                )

    @staticmethod
    def _migrate_uuid_ids(connection):
        columns = connection.execute("PRAGMA table_info(properties)").fetchall()
        id_column = next(row for row in columns if row["name"] == "id")
        if str(id_column["type"]).upper() == "TEXT":
            return

        connection.execute(
            """
            CREATE TABLE properties_uuid (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                slug TEXT NOT NULL,
                address TEXT NOT NULL,
                category TEXT NOT NULL,
                property_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NOT_SYNC',
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        rows = connection.execute("SELECT * FROM properties").fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT INTO properties_uuid (
                    id, title, slug, address, category, property_type,
                    status, data_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    row["title"],
                    row["slug"],
                    row["address"],
                    row["category"],
                    row["property_type"],
                    row["status"],
                    row["data_json"],
                    row["created_at"],
                    row["updated_at"],
                ),
            )
        connection.execute("DROP TABLE properties")
        connection.execute("ALTER TABLE properties_uuid RENAME TO properties")

    @classmethod
    def _migrate_normalized_values(cls, connection):
        rows = connection.execute(
            """
            SELECT id, address, category, property_type, data_json
              FROM properties
            """
        ).fetchall()
        for row in rows:
            try:
                data = json.loads(row["data_json"])
            except (TypeError, json.JSONDecodeError):
                continue

            details = data.get("detalhes", {})
            location = data.get("localizacao", {})
            address = row["address"] or str(location.get("endereco", "")).strip()
            category = row["category"] or str(details.get("categoria", "")).strip()
            property_type = row["property_type"] or str(details.get("tipo", "")).strip()
            normalized_json = json.dumps(
                cls._data_without_columns(data), ensure_ascii=False
            )
            connection.execute(
                """
                UPDATE properties
                   SET address = ?, category = ?, property_type = ?, data_json = ?
                 WHERE id = ?
                """,
                (address, category, property_type, normalized_json, row["id"]),
            )

    def save(self, data: dict, property_id: str | None = None) -> str:
        details = data.get("detalhes", {})
        location = data.get("localizacao", {})
        title = details.get("titulo", "").strip() or "Propriedade sem título"
        slug = details.get("slug", "").strip()
        address = location.get("endereco", "").strip()
        category = details.get("categoria", "").strip()
        property_type = details.get("tipo", "").strip()
        data_json = json.dumps(self._data_without_columns(data), ensure_ascii=False)

        with self._connect() as connection:
            if property_id is None:
                property_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO properties
                        (id, title, slug, address, category, property_type, status, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, 'NOT_SYNC', ?)
                    """,
                    (
                        property_id,
                        title,
                        slug,
                        address,
                        category,
                        property_type,
                        data_json,
                    ),
                )
                self._sync_files(connection, property_id, self._media_values(data))
                return property_id

            cursor = connection.execute(
                """
                UPDATE properties
                   SET title = ?, slug = ?, address = ?, category = ?,
                       property_type = ?, status = 'NOT_SYNC', data_json = ?,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?
                """,
                (
                    title,
                    slug,
                    address,
                    category,
                    property_type,
                    data_json,
                    property_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Propriedade {property_id} não encontrada")
            self._sync_files(connection, property_id, self._media_values(data))
            return property_id

    def load(self, property_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT data_json, address, category, property_type
                  FROM properties
                 WHERE id = ?
                """,
                (property_id,),
            ).fetchone()
            stored_files = connection.execute(
                """
                SELECT file_type, relative_path
                  FROM property_files
                 WHERE property_id = ?
                 ORDER BY created_at, id
                """,
                (property_id,),
            ).fetchall()

        if row is None:
            raise ValueError(f"Propriedade {property_id} não encontrada")
        data = json.loads(row["data_json"])
        data.setdefault("detalhes", {})["categoria"] = row["category"]
        data["detalhes"]["tipo"] = row["property_type"]
        data.setdefault("localizacao", {})["endereco"] = row["address"]
        if stored_files:
            images = data.setdefault("imagens", {})
            images.update(
                {
                    "imagem_titulo": "",
                    "imagem_3d": "",
                    "galeria": [],
                    "documentos": [],
                }
            )
            for stored_file in stored_files:
                path = str(self.database_path.parent / stored_file["relative_path"])
                file_type = stored_file["file_type"]
                if file_type == "SEO_IMAGE":
                    data.setdefault("seo", {})["imagem"] = path
                elif file_type == "TITLE_IMAGE":
                    images["imagem_titulo"] = path
                elif file_type == "THREE_D_IMAGE":
                    images["imagem_3d"] = path
                elif file_type == "GALLERY_IMAGE":
                    images["galeria"].append(path)
                elif file_type == "DOCUMENT":
                    images["documentos"].append(path)
        return data

    def delete(self, property_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM properties WHERE id = ?", (property_id,)
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Propriedade {property_id} não encontrada")
        property_media_dir = self.media_dir / property_id
        if property_media_dir.exists():
            shutil.rmtree(property_media_dir)

    @staticmethod
    def _data_without_columns(data: dict) -> dict:
        stored_data = deepcopy(data)
        stored_data.get("detalhes", {}).pop("categoria", None)
        stored_data.get("detalhes", {}).pop("tipo", None)
        stored_data.get("localizacao", {}).pop("endereco", None)
        images = stored_data.get("imagens", {})
        for field in ("imagem_titulo", "imagem_3d", "galeria", "documentos"):
            images.pop(field, None)
        stored_data.get("seo", {}).pop("imagem", None)
        return stored_data

    @staticmethod
    def _media_values(data: dict) -> dict:
        values = dict(data.get("imagens", {}))
        values["seo_image"] = data.get("seo", {}).get("imagem", "")
        return values

    def _sync_files(self, connection, property_id: str, images: dict):
        selected_files = []
        for file_type, (field, multiple) in self.FILE_FIELDS.items():
            raw_value = images.get(field, [] if multiple else "")
            paths = list(raw_value or []) if multiple else ([raw_value] if raw_value else [])
            if not multiple and len(paths) > 1:
                raise ValueError(f"{file_type} aceita apenas um arquivo")
            for raw_path in paths:
                source = Path(raw_path).expanduser().resolve()
                mime_type = self._validate_file(file_type, source)
                selected_files.append((file_type, source, mime_type))

        existing_rows = connection.execute(
            "SELECT id, relative_path FROM property_files WHERE property_id = ?",
            (property_id,),
        ).fetchall()
        existing_by_path = {
            (self.database_path.parent / row["relative_path"]).resolve(): row
            for row in existing_rows
        }

        records = []
        new_files = []
        try:
            for file_type, source, mime_type in selected_files:
                existing = existing_by_path.get(source)
                if existing:
                    relative_path = str(source.relative_to(self.database_path.parent))
                    records.append(
                        (
                            existing["id"],
                            property_id,
                            file_type,
                            source.name,
                            source.name,
                            relative_path,
                            mime_type,
                            source.stat().st_size,
                        )
                    )
                    continue

                target_dir = self.media_dir / property_id / file_type.lower()
                target_dir.mkdir(parents=True, exist_ok=True)
                stored_name = f"{uuid4()}{source.suffix.lower()}"
                target = target_dir / stored_name
                shutil.copy2(source, target)
                new_files.append(target)
                records.append(
                    (
                        str(uuid4()),
                        property_id,
                        file_type,
                        source.name,
                        stored_name,
                        str(target.relative_to(self.database_path.parent)),
                        mime_type,
                        target.stat().st_size,
                    )
                )

            desired_paths = {record[5] for record in records}
            connection.execute(
                "DELETE FROM property_files WHERE property_id = ?", (property_id,)
            )
            connection.executemany(
                """
                INSERT INTO property_files (
                    id, property_id, file_type, original_name, stored_name,
                    relative_path, mime_type, size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            for row in existing_rows:
                if row["relative_path"] not in desired_paths:
                    old_path = self.database_path.parent / row["relative_path"]
                    if old_path.is_file():
                        old_path.unlink()
        except Exception:
            for new_file in new_files:
                if new_file.is_file():
                    new_file.unlink()
            raise

    def _validate_file(self, file_type: str, path: Path) -> str:
        if not path.is_file():
            raise ValueError(f"Arquivo não encontrado: {path.name}")
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if file_type in {"SEO_IMAGE", "THREE_D_IMAGE"}:
            allowed = mime_type.startswith("image/")
        else:
            allowed = mime_type in self.ALLOWED_MIME_TYPES[file_type]
        if not allowed:
            raise ValueError(f"Tipo de arquivo inválido para {file_type}: {path.name}")
        return mime_type

    def list_all(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, slug, address, category, property_type, status,
                       created_at, updated_at
                  FROM properties
                 ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
