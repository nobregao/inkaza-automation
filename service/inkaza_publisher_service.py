import json
import time
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from domain.catalog_admin import (
    INSTALACOES_OBRIGATORIAS_POR_CATEGORIA,
    INSTALACOES_POR_CATEGORIA,
)
from helper.system_helper import get_bot_user_data_dir
from service.license_service import LicenseService


LOGIN_URL = "https://admin.inkaza.com.br/login"
CREATE_PROPERTY_URL = "https://admin.inkaza.com.br/property/create"

CATEGORY_VALUES = {
    "Condo": "1",
    "House": "2",
    "Plote": "3",
    "Apartament": "4",
    "Apartment": "4",
    "Penthouse": "5",
    "Commercial": "6",
    "Farm": "7",
    "New Property": "8",
    "Transfer": "9",
}
PROPERTY_TYPE_VALUES = {"venda": "0", "aluguel": "1"}
VIDEO_TYPE_VALUES = {"YouTube": "1", "Vimeo": "2"}
PRICE_DURATION_VALUES = {
    "Diário": "Daily",
    "Diariamente": "Daily",
    "Mensal": "Monthly",
    "Mensalmente": "Monthly",
    "Anual": "Yearly",
    "Anualmente": "Yearly",
    "Trimestral": "Quarterly",
    "Trimestralmente": "Quarterly",
}
NEARBY_PLACE_IDS = {
    "Mall": 1,
    "Gas Station": 2,
    "Garden": 3,
    "Gym": 4,
    "Bus Stop": 5,
    "Bank ATM": 6,
    "Supermarket": 7,
    "School": 8,
    "Hospital": 9,
}
INSTALLATION_PARAMETER_IDS = {
    "piscina": 1,
    "wifi": 2,
    "elevadores": 3,
    "fitness": 4,
    "cctv": 5,
    "ar_condicionado": 6,
    "seguranca": 7,
    "estacionamento": 8,
    "area": 9,
    "recepcao": 10,
    "garagem": 11,
    "cozinha": 12,
    "banheiros": 13,
    "quartos": 14,
    "sacadas": 15,
    "extras": 16,
}
NUMERIC_INSTALLATIONS = {
    "piscina", "elevadores", "fitness", "seguranca",
    "estacionamento", "area", "recepcao", "garagem",
    "cozinha", "banheiros", "quartos", "sacadas",
}


@dataclass
class PublicationResult:
    filled_fields: list[str] = field(default_factory=list)
    skipped_fields: list[str] = field(default_factory=list)
    error_fields: list[str] = field(default_factory=list)
    review_fields: list[str] = field(default_factory=list)
    submitted: bool = False
    response_url: str = ""
    response_status: int | None = None
    response_message: str = ""
    published: bool = False

    def report_rows(self) -> list[tuple[str, str]]:
        statuses: dict[str, str] = {}
        for status, fields in (
            ("PREENCHIDO", self.filled_fields),
            ("IGNORADO", self.skipped_fields),
            ("ERRO", self.error_fields),
            ("REVISAR", self.review_fields),
        ):
            for field_name in fields:
                statuses[field_name] = status
        return [(status, field_name) for field_name, status in statuses.items()]

    def summary(self) -> str:
        counts = {status: 0 for status in ("PREENCHIDO", "IGNORADO", "ERRO", "REVISAR")}
        for status, _field_name in self.report_rows():
            counts[status] += 1
        return " | ".join(f"{status}: {count}" for status, count in counts.items())


class InkazaPublisherService:
    """Preenche o formulário da INKAZA sem efetuar a publicação final."""

    def __init__(self, profile_dir: Path | None = None):
        self.profile_dir = Path(profile_dir or get_bot_user_data_dir("INKAZA")).expanduser()

    @staticmethod
    def validate_property(data: dict) -> list[str]:
        details = data.get("detalhes", {})
        location = data.get("localizacao", {})
        images = data.get("imagens", {})
        required = {
            "Categoria": details.get("categoria"),
            "Título": details.get("titulo"),
            "Descrição": details.get("descricao"),
            "Tipo": details.get("tipo"),
            "Preço": details.get("preco"),
            "Cidade": location.get("cidade"),
            "País": location.get("pais"),
            "Estado": location.get("estado"),
            "Endereço do cliente": location.get("endereco_cliente"),
            "Endereço": location.get("endereco"),
            "Imagem do título": images.get("imagem_titulo"),
        }
        missing = [name for name, value in required.items() if not value]
        if details.get("categoria") and details["categoria"] not in CATEGORY_VALUES:
            missing.append("Categoria reconhecida pela INKAZA")
        if details.get("tipo") not in PROPERTY_TYPE_VALUES:
            missing.append("Tipo reconhecido pela INKAZA")
        if details.get("tipo") == "aluguel" and details.get("duracao_preco") not in PRICE_DURATION_VALUES:
            missing.append("Duração por preço reconhecida pela INKAZA")
        category = details.get("categoria")
        installations = data.get("instalacoes", {})
        active_fields = INSTALACOES_POR_CATEGORIA.get(category, ())
        required_fields = INSTALACOES_OBRIGATORIAS_POR_CATEGORIA.get(category, set())
        for field in active_fields:
            if field == "extras":
                continue
            value = str(installations.get(field, "")).strip()
            if field in required_fields and not value:
                missing.append(f"Instalação obrigatória: {field}")
            elif field in NUMERIC_INSTALLATIONS and value and (
                not value.isdigit() or int(value) < 1
            ):
                missing.append(f"Instalação inválida: {field}")
        return missing

    def publish_all(
        self,
        properties: list[tuple[str, dict]],
        notify: Callable[[str], None] | None = None,
        report: Callable[[str, str, PublicationResult], None] | None = None,
        login: str = "",
        password: str = "",
        license_key: str = "",
    ) -> list[tuple[str, PublicationResult]]:
        """Publica propriedades pendentes usando uma única sessão do navegador."""
        emit = notify or (lambda _message: None)
        emit("Validando licença online...")
        LicenseService().validate(license_key)
        from playwright.sync_api import sync_playwright

        emit_report = report or (lambda _property_id, _title, _result: None)
        results: list[tuple[str, PublicationResult]] = []
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        emit("Abrindo o Google Chrome...")

        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(self.profile_dir), channel="chrome", headless=False, no_viewport=True
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()

                total = len(properties)
                for index, (property_id, data) in enumerate(properties, start=1):
                    title = str(data.get("detalhes", {}).get("titulo") or property_id)
                    result = PublicationResult()
                    emit(f"Publicando {index}/{total}: {title}")
                    try:
                        missing = self.validate_property(data)
                        if missing:
                            result.error_fields.extend(missing)
                            result.response_message = (
                                "Campos obrigatórios ausentes: " + ", ".join(missing)
                            )
                        else:
                            self._open_create_page(page, login, password, emit)
                            result = self._fill_form(page, data)
                            if result.error_fields:
                                result.response_message = (
                                    "Falha ao preencher: "
                                    + ", ".join(result.error_fields)
                                )
                            else:
                                self._submit_and_capture(page, result)
                    except Exception as error:
                        result.published = False
                        result.response_message = str(error)
                        if "Publicação" not in result.error_fields:
                            result.error_fields.append("Publicação")

                    results.append((property_id, result))
                    emit_report(property_id, title, result)
            finally:
                context.close()

        published_count = sum(result.published for _property_id, result in results)
        emit(
            f"Publicação concluída: {published_count} publicada(s) e "
            f"{len(results) - published_count} com erro."
        )
        return results

    def fill_property(
        self,
        data: dict,
        notify: Callable[[str], None] | None = None,
        report: Callable[[PublicationResult], None] | None = None,
        login: str = "",
        password: str = "",
        confirm_submit: Callable[[PublicationResult], bool] | None = None,
    ) -> PublicationResult:
        missing = self.validate_property(data)
        if missing:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(missing))

        from playwright.sync_api import sync_playwright

        emit = notify or (lambda _message: None)
        emit_report = report or (lambda _result: None)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        emit("Abrindo o Google Chrome...")
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(self.profile_dir), channel="chrome", headless=False, no_viewport=True
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                self._open_create_page(page, login, password, emit)
                emit("Preenchendo a propriedade (sem publicar)...")
                result = self._fill_form(page, data)
                emit_report(result)
                if result.error_fields:
                    emit(
                        "Preenchimento concluído com erros. " + result.summary() +
                        ". O envio permaneceu bloqueado."
                    )
                elif confirm_submit is not None and confirm_submit(result):
                    emit("Salvando a propriedade na INKAZA para capturar o retorno...")
                    self._submit_and_capture(page, result)
                    emit_report(result)
                    if result.published:
                        emit("Propriedade publicada: " + result.response_message)
                    else:
                        emit("Publicação recusada: " + result.response_message)
                else:
                    emit(
                        "Preenchimento concluído. " + result.summary() +
                        ". Revise no navegador; o envio não foi confirmado."
                    )
                while context.pages:
                    time.sleep(0.5)
                return result
            finally:
                context.close()

    def _open_create_page(self, page, login: str, password: str, emit):
        page.goto(CREATE_PROPERTY_URL, wait_until="domcontentloaded")
        if "/login" not in page.url:
            return
        emit("Sessão expirada. Realizando login automaticamente...")
        self._perform_login(page, login, password)
        try:
            page.wait_for_url(lambda url: "/login" not in url, timeout=30_000)
        except Exception as error:
            raise RuntimeError(
                "Não foi possível autenticar. Verifique o login e a senha."
            ) from error
        page.goto(CREATE_PROPERTY_URL, wait_until="domcontentloaded")

    def _fill_form(self, page, data: dict) -> PublicationResult:
        page.wait_for_selector("#category", state="visible", timeout=30_000)
        result = self._fill_details(page, data)
        self._fill_installations(page, data, result)
        self._fill_seo(page, data, result)
        self._fill_nearby_places(page, data, result)
        self._fill_location(page, data, result)
        self._fill_images(page, data, result)
        self._fill_video(page, data, result)
        return result

    @staticmethod
    def _submit_and_capture(page, result: PublicationResult):
        try:
            save_button = page.locator(
                '#myForm input[type="submit"][value="Salvar"]'
            )
            save_button.wait_for(state="visible", timeout=15_000)

            # O callback de sucesso da INKAZA recarrega imediatamente a página,
            # fazendo o Chromium descartar o corpo da resposta AJAX antes que o
            # Playwright consiga lê-lo. Durante a captura assistida, substituímos
            # somente esse callback; o POST e o tratamento normal da resposta
            # continuam sendo executados pelo site.
            reload_callback_overridden = page.evaluate(
                """
                () => {
                    if (typeof window.successFunction !== 'function') {
                        return false;
                    }
                    window.successFunction = () => {};
                    return true;
                }
                """
            )
            if not reload_callback_overridden:
                raise RuntimeError(
                    "O callback successFunction da INKAZA não foi encontrado."
                )

            def is_property_submission(response):
                request = response.request
                return (
                    request.method.upper() == "POST"
                    and response.url.split("?", 1)[0].rstrip("/")
                    == "https://admin.inkaza.com.br/property"
                )

            with page.expect_response(
                is_property_submission, timeout=30_000
            ) as response_info:
                save_button.click()
            response = response_info.value
            response.finished()

            try:
                response_body = response.text()
            except Exception as body_error:
                response_body = f"Não foi possível ler o corpo da resposta: {body_error}"

            published, response_message, _response_payload = (
                InkazaPublisherService._interpret_publish_response(
                    response.status, response.ok, response_body
                )
            )

            result.submitted = True
            result.response_url = page.url
            result.response_status = response.status
            result.response_message = response_message
            result.published = published
            if published:
                result.filled_fields.append("Publicação confirmada pela INKAZA")
            else:
                result.error_fields.append("Publicação: " + response_message)
        except Exception as error:
            result.error_fields.append("Salvar propriedade")
            raise RuntimeError(
                "Não foi possível salvar a propriedade ou interpretar o retorno."
            ) from error

    @staticmethod
    def _interpret_publish_response(status: int, response_ok: bool, body: str):
        try:
            payload = json.loads(body.strip())
        except (TypeError, json.JSONDecodeError):
            return (
                False,
                f"Resposta inválida da INKAZA (HTTP {status}).",
                None,
            )

        if not isinstance(payload, dict):
            return (
                False,
                f"Formato inesperado na resposta da INKAZA (HTTP {status}).",
                payload,
            )

        message = str(payload.get("message") or "").strip()
        published = response_ok and payload.get("error") is False
        if not message:
            message = (
                "Dados criados com sucesso"
                if published
                else f"A INKAZA recusou a publicação (HTTP {status})."
            )
        return published, message, payload

    @staticmethod
    def _perform_login(page, login: str, password: str):
        login = str(login).strip()
        if not login or not password:
            raise ValueError(
                "A sessão da INKAZA expirou. Informe o login e a senha na tela de publicação."
            )

        login_input = page.locator(
            'input[name="email"], input[type="email"]'
        ).first
        password_input = page.locator(
            'input[name="password"], input[type="password"]'
        ).first
        login_input.wait_for(state="visible", timeout=15_000)
        password_input.wait_for(state="visible", timeout=15_000)
        login_input.fill(login)
        password_input.fill(password)
        page.locator('button[type="submit"], input[type="submit"]').first.click()

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value).lower().strip())
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        return re.sub(r"[^a-z0-9]+", "-", without_accents).strip("-")

    def _fill_details(self, page, data: dict) -> PublicationResult:
        details = data.get("detalhes", {})
        result = PublicationResult()

        self._select(
            page,
            "Categoria",
            "#category",
            CATEGORY_VALUES[details["categoria"]],
            result,
        )
        self._fill(page, "Título", "#title", details.get("titulo"), result)
        self._fill(
            page,
            "Lesma",
            "#slug",
            self._slugify(details.get("titulo", "")),
            result,
        )
        self._fill(
            page,
            "Descrição",
            "#description",
            details.get("descricao"),
            result,
        )

        property_type = PROPERTY_TYPE_VALUES[details["tipo"]]
        self._check(
            page,
            "Tipo de propriedade",
            f'[name="property_type"][value="{property_type}"]',
            result,
        )
        if property_type == "1":
            duration = PRICE_DURATION_VALUES[details["duracao_preco"]]
            self._select(
                page,
                "Duração por preço",
                "#price_duration",
                duration,
                result,
            )

        self._fill(page, "Preço", "#price", details.get("preco"), result)
        return result

    def _fill_installations(
        self,
        page,
        data: dict,
        result: PublicationResult,
    ):
        category = data.get("detalhes", {}).get("categoria")
        active_fields = INSTALACOES_POR_CATEGORIA.get(category, ())
        if not active_fields:
            return

        installations = data.get("instalacoes", {})
        first_parameter = INSTALLATION_PARAMETER_IDS[active_fields[0]]
        try:
            page.locator(f'[name="par_{first_parameter}"]').wait_for(
                state="attached",
                timeout=10_000,
            )
        except Exception:
            result.error_fields.append("Painel de instalações")
            return

        for field in active_fields:
            if field == "extras":
                selected = set(installations.get("extras", []))
                try:
                    for option in ("SPA", "Sauna"):
                        checkbox = page.locator(
                            f'input[name="par_16[]"][value="{option}"]'
                        )
                        if option in selected:
                            checkbox.check()
                        else:
                            checkbox.uncheck()
                    result.filled_fields.append("Instalações extras")
                except Exception:
                    result.error_fields.append("Instalações extras")
                continue

            value = str(installations.get(field, "")).strip()
            locator = page.locator(
                f'[name="par_{INSTALLATION_PARAMETER_IDS[field]}"]'
            )
            try:
                locator.fill(value)
                if value:
                    result.filled_fields.append(f"Instalação: {field}")
                else:
                    result.skipped_fields.append(f"Instalação: {field}")
            except Exception:
                result.error_fields.append(f"Instalação: {field}")

    def _fill_seo(self, page, data: dict, result: PublicationResult):
        seo = data.get("seo", {})
        fields = (
            ("Título SEO", "#meta_title", seo.get("titulo")),
            ("Descrição SEO", "#meta_description", seo.get("descricao")),
            ("Palavras-chave SEO", "#keywords", seo.get("palavras_chave")),
        )
        for label, selector, value in fields:
            if value:
                self._fill(page, label, selector, value, result)
            else:
                result.skipped_fields.append(label)

        image = seo.get("imagem")
        if image:
            self._upload(
                page,
                "Imagem SEO",
                'input[type="file"][name="meta_image"]',
                image,
                result,
            )
        else:
            result.skipped_fields.append("Imagem SEO")

    def _fill_nearby_places(
        self,
        page,
        data: dict,
        result: PublicationResult,
    ):
        places = data.get("perto_de_lugares", {})
        for place, index in NEARBY_PLACE_IDS.items():
            fields = places.get(place, {})
            checkbox = page.locator(f"#chk{index}")
            if fields.get("selecionado"):
                try:
                    checkbox.check()
                    page.locator(f"#dist{index}").fill(
                        str(fields.get("distancia_km", ""))
                    )
                    result.filled_fields.append(f"Perto de {place}")
                except Exception:
                    result.error_fields.append(f"Perto de {place}")
            else:
                try:
                    checkbox.uncheck()
                    result.skipped_fields.append(f"Perto de {place}")
                except Exception:
                    result.error_fields.append(f"Perto de {place}")

    def _fill_location(
        self,
        page,
        data: dict,
        result: PublicationResult,
    ):
        location = data.get("localizacao", {})
        city = str(location.get("cidade", "")).strip()

        try:
            search = page.locator("#searchInput")
            search.fill(city)
            suggestion = page.locator(
                "#places-suggestions .list-group-item"
            ).first
            suggestion.wait_for(state="visible", timeout=15_000)
            suggestion.click()
            page.wait_for_function(
                """() => Boolean(
                    document.querySelector("#city")?.value &&
                    document.querySelector("#latitude")?.value &&
                    document.querySelector("#longitude")?.value
                )""",
                timeout=15_000,
            )
            result.filled_fields.append("Cidade")
            result.review_fields.append("Cidade")
        except Exception:
            result.error_fields.append("Cidade (autocomplete)")

        self._fill(page, "País", "#country", location.get("pais"), result)
        self._fill(page, "Estado", "#state", location.get("estado"), result)
        self._fill(
            page,
            "Endereço do cliente",
            "#client-address",
            location.get("endereco_cliente"),
            result,
        )
        self._fill(
            page,
            "Endereço",
            "#address",
            location.get("endereco"),
            result,
        )

    def _fill_images(
        self,
        page,
        data: dict,
        result: PublicationResult,
    ):
        images = data.get("imagens", {})
        uploads = (
            ("Imagem do título", "title_image", images.get("imagem_titulo")),
            ("Imagem 3D", "3d_image", images.get("imagem_3d")),
            ("Imagens da galeria", "gallery_images[]", images.get("galeria", [])),
            ("Documentos", "documents[]", images.get("documentos", [])),
        )

        for label, field_name, paths in uploads:
            if not paths:
                if label != "Imagem do título":
                    result.skipped_fields.append(label)
                continue
            file_paths = paths if isinstance(paths, list) else [paths]
            try:
                page.locator(
                    f'input[type="file"][name="{field_name}"]'
                ).set_input_files(
                    [str(Path(path).resolve()) for path in file_paths]
                )
                result.filled_fields.append(label)
                result.review_fields.append(label)
            except Exception:
                result.error_fields.append(label)

    def _fill_video(
        self,
        page,
        data: dict,
        result: PublicationResult,
    ):
        video = data.get("video", {})
        video_type = str(video.get("tipo", "")).strip()
        video_link = str(video.get("link", "")).strip()

        if not video_type:
            result.skipped_fields.append("Vídeo")
            return
        if video_type not in VIDEO_TYPE_VALUES:
            result.error_fields.append("Tipo de vídeo")
            return

        self._select(
            page,
            "Tipo de vídeo",
            "#video_type",
            VIDEO_TYPE_VALUES[video_type],
            result,
        )
        if video_link:
            try:
                page.locator("#video_link_div").wait_for(
                    state="visible", timeout=10_000
                )
            except Exception:
                result.error_fields.append("Painel do link do vídeo")
                return
            self._fill(
                page, "Link do vídeo", "#video_link", video_link, result
            )
        else:
            result.skipped_fields.append("Link do vídeo")

    @staticmethod
    def _upload(page, label: str, selector: str, path, result: PublicationResult):
        try:
            page.locator(selector).set_input_files(str(Path(path).resolve()))
            result.filled_fields.append(label)
            result.review_fields.append(label)
        except Exception:
            result.error_fields.append(label)

    @staticmethod
    def _fill(page, label: str, selector: str, value, result: PublicationResult):
        try:
            page.locator(selector).fill(str(value))
            result.filled_fields.append(label)
        except Exception:
            result.error_fields.append(label)

    @staticmethod
    def _select(
        page,
        label: str,
        selector: str,
        value: str,
        result: PublicationResult,
    ):
        try:
            page.locator(selector).select_option(value=value)
            result.filled_fields.append(label)
        except Exception:
            result.error_fields.append(label)

    @staticmethod
    def _check(page, label: str, selector: str, result: PublicationResult):
        try:
            page.locator(selector).check()
            result.filled_fields.append(label)
        except Exception:
            result.error_fields.append(label)
