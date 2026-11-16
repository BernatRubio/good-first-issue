import os
from collections.abc import Mapping
from importlib.resources import files

import requests
from dotenv import load_dotenv


def load_query(name: str) -> str:
    return (files("good_first_issue") / "queries" / f"{name}.graphql").read_text(
        encoding="utf-8"
    )


def run_query(variables: dict) -> tuple[dict, Mapping[str, str]]:
    load_dotenv()
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
        json={"query": load_query("fetch_issues"), "variables": variables},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"], response.headers
