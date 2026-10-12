"""Generate an AES-256 resource credential master key for secret-environment injection."""

import base64
import secrets


def main() -> None:
    print(base64.b64encode(secrets.token_bytes(32)).decode("ascii"))
    print("Store this key securely in the local secret environment; this script does not edit .env.")


if __name__ == "__main__":
    main()
