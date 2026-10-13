import json
import ssl
import certifi
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LICENSE_URL = "https://raw.githubusercontent.com/nobregao/inkaza-license/refs/heads/main/license.json"
LICENSE_TIMEZONE = timezone(timedelta(hours=-3))


class LicenseValidationError(ValueError):
    pass


class LicenseService:
    """Consulta a licença online a cada publicação, sem autorização em cache."""

    def validate(self, license_key: str):
        license_key = license_key.strip()
        if not license_key:
            raise LicenseValidationError("Informe a licença para publicar.")
        request = Request(LICENSE_URL, headers={"Cache-Control": "no-cache", "Accept": "application/json"})
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with urlopen(request, timeout=15, context=context) as response:
                payload = json.load(response)
        except HTTPError as error:
            raise LicenseValidationError(
                f"Não foi possível consultar as licenças online (HTTP {error.code})."
            ) from error
        except (URLError, OSError) as error:
            reason = getattr(error, "reason", error)
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise LicenseValidationError(
                    "Não foi possível verificar o certificado HTTPS do servidor de licenças. "
                    "Verifique a data do computador e os certificados da conexão."
                ) from error
            raise LicenseValidationError(
                "Não foi possível consultar as licenças online. Verifique a conexão e tente novamente."
            ) from error
        except ValueError as error:
            raise LicenseValidationError("O arquivo online de licenças não contém JSON válido.") from error
        if not isinstance(payload, dict):
            raise LicenseValidationError("O arquivo online de licenças tem formato inválido.")
        license_data = payload.get(license_key)
        if not isinstance(license_data, dict) or license_data.get("active") is not True:
            raise LicenseValidationError("Licença inválida ou inativa. Entre em contato com o fornecedor.")
        try:
            expires_at = license_data["expires_at"]
            if not isinstance(expires_at, str):
                raise ValueError()
            expiry = datetime.strptime(expires_at, "%Y-%m-%d").date()
            if expiry.isoformat() != expires_at:
                raise ValueError()
        except (KeyError, TypeError, ValueError) as error:
            raise LicenseValidationError("A licença não possui uma data de validade válida.") from error
        if datetime.now(LICENSE_TIMEZONE).date() > expiry:
            raise LicenseValidationError("Licença expirada. Entre em contato com o fornecedor.")
