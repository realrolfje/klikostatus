#!/usr/bin/env python3
"""Test the Kliko Status API outside Home Assistant."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

def post_json(url: str, payload: dict[str, Any]) -> Any:
    """POST JSON and return parsed JSON."""
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "*/*",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        message = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {err.code}: {message}") from err
    except URLError as err:
        raise RuntimeError(f"Network error: {err.reason}") from err


def find_container(containers: Any, container_number: str) -> dict[str, Any]:
    """Find one container in the API response."""
    if not isinstance(containers, list):
        raise RuntimeError(f"Expected a list, got: {type(containers).__name__}")

    expected = container_number.strip().casefold()
    for container in containers:
        if not isinstance(container, dict):
            continue
        actual = str(container.get("containerNumber", "")).strip().casefold()
        if actual == expected:
            return container

    raise RuntimeError(f"Container not found: {container_number}")


def main() -> int:
    """Run the test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--client",
        default=os.environ.get("KLIKO_CLIENT"),
        help="Kliko client slug, for example the subdomain part after cp-",
    )
    parser.add_argument(
        "--card-number",
        default=os.environ.get("KLIKO_CARD_NUMBER"),
        help="Kliko card number, or set KLIKO_CARD_NUMBER",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("KLIKO_PASSWORD"),
        help="Kliko password, or set KLIKO_PASSWORD",
    )
    parser.add_argument(
        "--container-number",
        default=os.environ.get("KLIKO_CONTAINER_NUMBER"),
        help="Container number, or set KLIKO_CONTAINER_NUMBER",
    )
    parser.add_argument(
        "--client-name",
        default=os.environ.get("KLIKO_CLIENT_NAME"),
        help="Defaults to --client",
    )
    parser.add_argument("--app", default=os.environ.get("KLIKO_APP"))
    parser.add_argument("--login-url", default=os.environ.get("KLIKO_LOGIN_URL"))
    parser.add_argument(
        "--containers-url",
        default=os.environ.get("KLIKO_CONTAINERS_URL"),
    )
    parser.add_argument(
        "--dump-container",
        action="store_true",
        help="Print the full matched container JSON",
    )
    args = parser.parse_args()

    if not args.client and not (args.client_name and args.login_url and args.containers_url):
        parser.error(
            "--client is required unless --client-name, --login-url and "
            "--containers-url are all provided"
        )
    if not args.container_number:
        parser.error("--container-number is required")

    client_name = args.client_name or args.client
    app = args.app or f"cp-{client_name}.kcm.com"
    login_url = (
        args.login_url
        or f"https://cp-{client_name}.klikocontainermanager.com/MyKliko/loginWithPassword"
    )
    containers_url = (
        args.containers_url
        or f"https://cp-{client_name}.klikocontainermanager.com/MyKliko/getMyContainers"
    )

    card_number = args.card_number or input("Kaartnummer: ").strip()
    password = args.password or getpass.getpass("Wachtwoord: ")

    login_payload = {
        "cardNumber": card_number,
        "password": password,
        "clientName": client_name,
        "app": app,
        "deviceId": "",
    }

    login_response = post_json(login_url, login_payload)
    token = login_response.get("token") if isinstance(login_response, dict) else None
    if login_response.get("success") is not True or not token:
        raise RuntimeError(f"Login failed: {login_response}")

    containers = post_json(containers_url, {"token": token})
    container = find_container(containers, args.container_number)
    address = container.get("address") if isinstance(container.get("address"), dict) else {}

    print("Login: ok")
    print(f"Container: {container.get('containerNumber')}")
    print(f"Vulling: {container.get('percentageFull')}%")
    print(f"Afvaltype: {container.get('fraction')}")
    print(f"Fout: {container.get('error')}")
    print(f"Vol: {container.get('isFull')}")
    print(f"Bijna vol: {container.get('isNearlyFull')}")
    print(f"Straat: {address.get('street')}")
    print(f"Latitude: {address.get('latitude')}")
    print(f"Longitude: {address.get('longitude')}")

    if args.dump_container:
        print(json.dumps(container, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as err:
        print(f"Error: {err}", file=sys.stderr)
        raise SystemExit(1)
