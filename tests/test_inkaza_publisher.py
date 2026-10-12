import unittest
from pathlib import Path

from domain.catalog_admin import INSTALACOES_POR_CATEGORIA

from service.inkaza_publisher_service import (
    CATEGORY_VALUES,
    INSTALLATION_PARAMETER_IDS,
    PRICE_DURATION_VALUES,
    PROPERTY_TYPE_VALUES,
    InkazaPublisherService,
    NEARBY_PLACE_IDS,
    PublicationResult,
    VIDEO_TYPE_VALUES,
)


class InkazaPublisherServiceTest(unittest.TestCase):
    def test_submits_form_and_interprets_response_without_saving_diagnostics(self):
        calls = {}

        class Request:
            method = "POST"

        class Response:
            request = Request()
            url = "https://admin.inkaza.com.br/property"
            status = 200
            ok = True

            def text(self):
                return (
                    '{"error":false,"message":"Dados criados com sucesso",'
                    '"data":null,"code":200}'
                )

            def finished(self):
                calls["response_finished"] = True

        class ResponseInfo:
            value = Response()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class Locator:
            def wait_for(self, **options):
                calls["wait"] = options

            def click(self):
                calls["click"] = True

        class Page:
            url = "https://admin.inkaza.com.br/property/123"

            def locator(self, selector):
                calls["selector"] = selector
                return Locator()

            def evaluate(self, script):
                calls["evaluate"] = script
                return True

            def expect_response(self, predicate, **options):
                calls["response_timeout"] = options["timeout"]
                calls["response_matched"] = predicate(Response())
                return ResponseInfo()

        result = PublicationResult()
        InkazaPublisherService._submit_and_capture(Page(), result)

        self.assertEqual(
            calls["selector"],
            '#myForm input[type="submit"][value="Salvar"]',
        )
        self.assertTrue(calls["click"])
        self.assertIn("window.successFunction = () => {}", calls["evaluate"])
        self.assertTrue(calls["response_matched"])
        self.assertTrue(calls["response_finished"])
        self.assertTrue(result.submitted)
        self.assertEqual(result.response_url, Page.url)
        self.assertEqual(result.response_status, 200)
        self.assertTrue(result.published)
        self.assertEqual(result.response_message, "Dados criados com sucesso")
        self.assertIn("Publicação confirmada pela INKAZA", result.filled_fields)

    def test_interprets_rejected_publication_response(self):
        published, message, payload = (
            InkazaPublisherService._interpret_publish_response(
                500,
                False,
                '{"error":true,"message":"The slug has already been taken.","code":500}',
            )
        )

        self.assertFalse(published)
        self.assertEqual(message, "The slug has already been taken.")
        self.assertTrue(payload["error"])

    def test_does_not_accept_invalid_json_as_success(self):
        published, message, payload = (
            InkazaPublisherService._interpret_publish_response(
                200, True, "resposta inesperada"
            )
        )

        self.assertFalse(published)
        self.assertIn("Resposta inválida", message)
        self.assertIsNone(payload)

    def test_performs_login_with_credentials(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            @property
            def first(self):
                return self

            def wait_for(self, **options):
                calls[(self.selector, "wait")] = options

            def fill(self, value):
                calls[(self.selector, "fill")] = value

            def click(self):
                calls[(self.selector, "click")] = True

        class Page:
            def locator(self, selector):
                return Locator(selector)

        InkazaPublisherService._perform_login(
            Page(), "cliente.com.br", "senha-segura"
        )

        self.assertEqual(
            calls[('input[name="email"], input[type="email"]', "fill")],
            "cliente.com.br",
        )
        self.assertEqual(
            calls[('input[name="password"], input[type="password"]', "fill")],
            "senha-segura",
        )
        self.assertTrue(
            calls[('button[type="submit"], input[type="submit"]', "click")]
        )

    def test_login_requires_credentials_when_session_expired(self):
        with self.assertRaisesRegex(ValueError, "sessão da INKAZA expirou"):
            InkazaPublisherService._perform_login(None, "", "")

    def test_assisted_validation_report_prioritizes_review_and_errors(self):
        result = PublicationResult(
            filled_fields=["Título", "Imagem do título"],
            skipped_fields=["Vídeo"],
            error_fields=["Cidade"],
            review_fields=["Imagem do título"],
        )

        self.assertEqual(
            result.report_rows(),
            [
                ("PREENCHIDO", "Título"),
                ("REVISAR", "Imagem do título"),
                ("IGNORADO", "Vídeo"),
                ("ERRO", "Cidade"),
            ],
        )
        self.assertIn("ERRO: 1", result.summary())
        self.assertIn("REVISAR: 1", result.summary())

    def test_fill_failure_is_reported_as_error(self):
        class Locator:
            def fill(self, _value):
                raise RuntimeError("seletor indisponível")

        class Page:
            def locator(self, _selector):
                return Locator()

        result = PublicationResult()
        InkazaPublisherService._fill(
            Page(), "Título", "#title", "Casa", result
        )

        self.assertIn("Título", result.error_fields)
        self.assertNotIn("Título", result.skipped_fields)

    def test_validation_reports_missing_required_fields(self):
        missing = InkazaPublisherService.validate_property({})
        self.assertIn("Título", missing)
        self.assertIn("Imagem do título", missing)

    def test_complete_property_is_valid(self):
        data = {
            "detalhes": {"categoria": "House", "titulo": "Casa", "descricao": "Descrição", "tipo": "venda", "preco": "100"},
            "localizacao": {"cidade": "Fortaleza", "pais": "Brasil", "estado": "Ceará", "endereco_cliente": "Rua A, 10", "endereco": "Rua A"},
            "imagens": {"imagem_titulo": "/tmp/image.png"},
            "instalacoes": {"area": "80", "garagem": "1", "banheiros": "2", "quartos": "3"},
        }
        self.assertEqual(InkazaPublisherService.validate_property(data), [])

    def test_slug_is_generated_from_title_only_when_publishing(self):
        self.assertEqual(
            InkazaPublisherService._slugify("  Apartamento à Beira-Mar  "),
            "apartamento-a-beira-mar",
        )

    def test_details_values_match_inkaza_html(self):
        self.assertEqual(CATEGORY_VALUES["Apartament"], "4")
        self.assertEqual(CATEGORY_VALUES["Apartment"], "4")
        self.assertEqual(PROPERTY_TYPE_VALUES["venda"], "0")
        self.assertEqual(PROPERTY_TYPE_VALUES["aluguel"], "1")
        self.assertEqual(PRICE_DURATION_VALUES["Mensalmente"], "Monthly")

    def test_rental_requires_supported_price_duration(self):
        data = {
            "detalhes": {"categoria": "House", "titulo": "Casa", "descricao": "Descrição", "tipo": "aluguel", "duracao_preco": "Semanal", "preco": "100"},
            "localizacao": {"cidade": "Fortaleza", "pais": "Brasil", "estado": "Ceará", "endereco": "Rua A"},
            "imagens": {"imagem_titulo": "/tmp/image.png"},
        }
        self.assertIn("Duração por preço reconhecida pela INKAZA", InkazaPublisherService.validate_property(data))

    def test_fills_seo_fields_and_uploads_image(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            def fill(self, value):
                calls[self.selector] = ("fill", value)

            def set_input_files(self, value):
                calls[self.selector] = ("upload", value)

        class Page:
            def locator(self, selector):
                return Locator(selector)

        result = PublicationResult()
        InkazaPublisherService()._fill_seo(
            Page(),
            {"seo": {"titulo": "SEO", "descricao": "Descrição SEO", "palavras_chave": "casa, praia", "imagem": "/tmp/seo.png"}},
            result,
        )

        self.assertEqual(calls["#meta_title"], ("fill", "SEO"))
        self.assertEqual(calls["#meta_description"], ("fill", "Descrição SEO"))
        self.assertEqual(calls["#keywords"], ("fill", "casa, praia"))
        self.assertEqual(calls['input[type="file"][name="meta_image"]'][0], "upload")
        self.assertIn("Imagem SEO", result.filled_fields)

    def test_fills_selected_nearby_places_and_clears_others(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            def check(self):
                calls[self.selector] = ("check", None)

            def uncheck(self):
                calls[self.selector] = ("uncheck", None)

            def fill(self, value):
                calls[self.selector] = ("fill", value)

        class Page:
            def locator(self, selector):
                return Locator(selector)

        result = PublicationResult()
        InkazaPublisherService()._fill_nearby_places(
            Page(),
            {"perto_de_lugares": {"Mall": {"selecionado": True, "distancia_km": "1.5"}}},
            result,
        )

        self.assertEqual(NEARBY_PLACE_IDS["Hospital"], 9)
        self.assertEqual(calls["#chk1"], ("check", None))
        self.assertEqual(calls["#dist1"], ("fill", "1.5"))
        self.assertEqual(calls["#chk2"], ("uncheck", None))
        self.assertIn("Perto de Mall", result.filled_fields)

    def test_selected_nearby_place_allows_empty_optional_distance(self):
        missing = InkazaPublisherService.validate_property(
            {"detalhes": {}, "perto_de_lugares": {"Gym": {"selecionado": True, "distancia_km": ""}}}
        )
        self.assertNotIn("Distância de Gym", missing)

    def test_plote_requires_only_area_installation(self):
        self.assertEqual(INSTALACOES_POR_CATEGORIA["Plote"], ("area",))
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["House"],
            ("piscina", "wifi", "ar_condicionado", "area", "garagem", "cozinha", "banheiros", "quartos"),
        )
        self.assertIn("sacadas", INSTALACOES_POR_CATEGORIA["Penthouse"])
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["Commercial"],
            ("area", "garagem", "banheiros"),
        )
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["New Property"],
            ("area", "garagem", "banheiros", "quartos"),
        )
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["Transfer"],
            ("area", "garagem", "banheiros", "quartos"),
        )
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["Farm"],
            ("wifi", "cctv", "ar_condicionado", "seguranca", "estacionamento", "recepcao", "garagem"),
        )
        self.assertEqual(
            INSTALACOES_POR_CATEGORIA["Apartament"],
            ("area", "garagem", "banheiros", "quartos"),
        )

    def test_fills_dynamic_condo_installations(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            def wait_for(self, **options):
                calls[(self.selector, "wait")] = options

            def fill(self, value):
                calls[(self.selector, "fill")] = value

            def check(self):
                calls[(self.selector, "checked")] = True

            def uncheck(self):
                calls[(self.selector, "checked")] = False

        class Page:
            def locator(self, selector):
                return Locator(selector)

        result = PublicationResult()
        InkazaPublisherService()._fill_installations(
            Page(),
            {
                "detalhes": {"categoria": "Condo"},
                "instalacoes": {
                    "area": "120",
                    "garagem": "2",
                    "wifi": "Fibra",
                    "extras": ["SPA"],
                },
            },
            result,
        )

        self.assertEqual(INSTALLATION_PARAMETER_IDS["area"], 9)
        self.assertEqual(calls[( '[name="par_9"]', "fill")], "120")
        self.assertEqual(calls[( '[name="par_11"]', "fill")], "2")
        self.assertEqual(calls[( '[name="par_2"]', "fill")], "Fibra")
        self.assertTrue(calls[( 'input[name="par_16[]"][value="SPA"]', "checked")])
        self.assertFalse(calls[( 'input[name="par_16[]"][value="Sauna"]', "checked")])
        self.assertIn("Instalações extras", result.filled_fields)

    def test_validation_requires_category_installations(self):
        data = {
            "detalhes": {"categoria": "Plote", "titulo": "Terreno", "descricao": "Descrição", "tipo": "venda", "preco": "100"},
            "localizacao": {"cidade": "Fortaleza", "pais": "Brasil", "estado": "Ceará", "endereco": "Rua A"},
            "imagens": {"imagem_titulo": "/tmp/image.png"},
            "instalacoes": {},
        }
        self.assertIn("Instalação obrigatória: area", InkazaPublisherService.validate_property(data))


    def test_fills_youtube_video(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            def select_option(self, value):
                calls[(self.selector, "select")] = value

            def wait_for(self, **options):
                calls[(self.selector, "wait")] = options

            def fill(self, value):
                calls[(self.selector, "fill")] = value

        class Page:
            def locator(self, selector):
                return Locator(selector)

        result = PublicationResult()
        InkazaPublisherService()._fill_video(
            Page(),
            {
                "video": {
                    "tipo": "YouTube",
                    "link": "https://youtu.be/video-teste",
                }
            },
            result,
        )

        self.assertEqual(VIDEO_TYPE_VALUES["YouTube"], "1")
        self.assertEqual(calls[("#video_type", "select")], "1")
        self.assertEqual(
            calls[("#video_link", "fill")],
            "https://youtu.be/video-teste",
        )
        self.assertIn("Tipo de vídeo", result.filled_fields)
        self.assertIn("Link do vídeo", result.filled_fields)

    def test_uploads_property_images_and_documents(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector

            def set_input_files(self, paths):
                calls[self.selector] = paths

        class Page:
            def locator(self, selector):
                return Locator(selector)

        result = PublicationResult()
        InkazaPublisherService()._fill_images(
            Page(),
            {
                "imagens": {
                    "imagem_titulo": "/tmp/title.png",
                    "imagem_3d": "/tmp/3d.webp",
                    "galeria": [str(Path("/tmp/gallery-1.jpg").resolve()), str(Path("/tmp/gallery-2.png").resolve())],
                    "documentos": [str(Path("/tmp/document.pdf").resolve())],
                }
            },
            result,
        )

        self.assertEqual(
            calls['input[type="file"][name="title_image"]'],
            [str(Path("/tmp/title.png").resolve())],
        )
        self.assertEqual(
            calls['input[type="file"][name="3d_image"]'],
            [str(Path("/tmp/3d.webp").resolve())],
        )
        self.assertEqual(
            calls['input[type="file"][name="gallery_images[]"]'],
            [str(Path("/tmp/gallery-1.jpg").resolve()), str(Path("/tmp/gallery-2.png").resolve())],
        )
        self.assertEqual(
            calls['input[type="file"][name="documents[]"]'],
            [str(Path("/tmp/document.pdf").resolve())],
        )
        self.assertIn("Imagem do título", result.filled_fields)
        self.assertIn("Documentos", result.filled_fields)

    def test_fills_location_using_city_autocomplete(self):
        calls = {}

        class Locator:
            def __init__(self, selector):
                self.selector = selector


            @property
            def first(self):
                return self

            def fill(self, value):
                calls[(self.selector, "fill")] = value

            def wait_for(self, **options):
                calls[(self.selector, "wait")] = options

            def click(self):
                calls[(self.selector, "click")] = True

        class Page:
            def locator(self, selector):
                return Locator(selector)

            def wait_for_function(self, expression, **options):
                calls[("wait_for_function", "expression")] = expression
                calls[("wait_for_function", "options")] = options

        result = PublicationResult()
        InkazaPublisherService()._fill_location(
            Page(),
            {
                "localizacao": {
                    "cidade": "Fortaleza",
                    "pais": "Brasil",
                    "estado": "Ceará",
                    "endereco_cliente": "Av. Beira Mar, 3960",
                    "endereco": "Fortaleza - Ceará, Brasil",
                }
            },
            result,
        )

        self.assertEqual(calls[("#searchInput", "fill")], "Fortaleza")
        self.assertTrue(calls[("#places-suggestions .list-group-item", "click")])
        self.assertEqual(calls[("#country", "fill")], "Brasil")
        self.assertEqual(calls[("#state", "fill")], "Ceará")
        self.assertEqual(calls[("#client-address", "fill")], "Av. Beira Mar, 3960")
        self.assertEqual(calls[("#address", "fill")], "Fortaleza - Ceará, Brasil")
        self.assertIn("Cidade", result.filled_fields)
        self.assertNotIn("Cidade (autocomplete)", result.skipped_fields)


if __name__ == "__main__":
    unittest.main()
