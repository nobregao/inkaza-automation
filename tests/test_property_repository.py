import sqlite3
import tempfile
import unittest
from pathlib import Path

from service.property_repository_service import PropertyRepositoryService


class PropertyRepositoryServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.repository = PropertyRepositoryService(self.root / "inkaza.db")
        self.image = Path("assets/icon.png").resolve()
        self.document = self.root / "contrato.pdf"
        self.document.write_bytes(b"%PDF-1.4\n")

    def tearDown(self):
        self.temp_directory.cleanup()

    def _payload(self):
        return {
            "detalhes": {
                "titulo": "Imóvel para teste",
                "slug": "imovel-para-teste",
                "categoria": "Casa",
                "tipo": "venda",
            },
            "localizacao": {"endereco": "Rua de teste"},
            "instalacoes": {
                "piscina": "1",
                "wifi": "Fibra",
                "area": "80",
                "garagem": "1",
                "banheiros": "2",
                "quartos": "3",
                "extras": ["SPA", "Sauna"],
            },
            "seo": {"imagem": str(self.image)},
            "imagens": {
                "imagem_titulo": str(self.image),
                "imagem_3d": str(self.image),
                "galeria": [str(self.image), str(self.image)],
                "documentos": [str(self.document)],
                "link_video": "",
            },
        }

    def test_saves_loads_updates_and_deletes_property_media(self):
        property_id = self.repository.save(self._payload())
        loaded = self.repository.load(property_id)
        self.assertEqual(loaded["instalacoes"]["area"], "80")
        self.assertEqual(loaded["instalacoes"]["garagem"], "1")
        self.assertEqual(loaded["instalacoes"]["banheiros"], "2")
        self.assertEqual(loaded["instalacoes"]["quartos"], "3")
        self.assertEqual(loaded["instalacoes"]["wifi"], "Fibra")
        self.assertEqual(loaded["instalacoes"]["extras"], ["SPA", "Sauna"])

        stored_paths = [
            Path(loaded["seo"]["imagem"]),
            Path(loaded["imagens"]["imagem_titulo"]),
            Path(loaded["imagens"]["imagem_3d"]),
            *(Path(path) for path in loaded["imagens"]["galeria"]),
            *(Path(path) for path in loaded["imagens"]["documentos"]),
        ]
        self.assertTrue(all(path.is_file() for path in stored_paths))

        with sqlite3.connect(self.repository.database_path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM property_files WHERE property_id = ?",
                (property_id,),
            ).fetchone()[0]
        self.assertEqual(count, 6)

        removed_paths = [
            Path(loaded["seo"]["imagem"]),
            Path(loaded["imagens"]["imagem_3d"]),
            *(Path(path) for path in loaded["imagens"]["galeria"]),
            *(Path(path) for path in loaded["imagens"]["documentos"]),
        ]
        loaded["seo"]["imagem"] = ""
        loaded["imagens"]["imagem_3d"] = ""
        loaded["imagens"]["galeria"] = []
        loaded["imagens"]["documentos"] = []
        self.repository.save(loaded, property_id)

        self.assertTrue(all(not path.exists() for path in removed_paths))
        self.assertTrue(Path(loaded["imagens"]["imagem_titulo"]).is_file())

        self.repository.delete(property_id)
        self.assertFalse((self.repository.media_dir / property_id).exists())

    def test_updates_property_status_after_successful_publication(self):
        property_id = self.repository.save(self._payload())

        self.repository.update_status(property_id, "SYNC")

        row = next(
            item for item in self.repository.list_all() if item["id"] == property_id
        )
        self.assertEqual(row["status"], "SYNC")

    def test_rejects_invalid_property_status(self):
        property_id = self.repository.save(self._payload())

        with self.assertRaisesRegex(ValueError, "Status de propriedade inválido"):
            self.repository.update_status(property_id, "PUBLICADO")

    def test_lists_only_properties_with_requested_status(self):
        pending_id = self.repository.save(self._payload())
        synced_payload = self._payload()
        synced_payload["detalhes"]["titulo"] = "Imóvel sincronizado"
        synced_id = self.repository.save(synced_payload)
        self.repository.update_status(synced_id, "SYNC")

        pending = self.repository.list_by_status("NOT_SYNC")

        self.assertEqual([row["id"] for row in pending], [pending_id])


if __name__ == "__main__":
    unittest.main()
