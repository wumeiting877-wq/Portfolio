import logging
import sys

_SECRET_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "private_key",
    "passphrase",
    "encrypted_payload",
    "ciphertext",
    "encryption_nonce",
    "master_key",
    "reauth_proof",
)


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        if any(token in message for token in _SECRET_TOKENS):
            record.msg = "[redacted log line containing credential-like field]"
            record.args = ()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RedactFilter())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[handler],
        force=True,
    )
