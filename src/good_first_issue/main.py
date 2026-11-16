import argparse
import datetime
import os
from enum import Enum
from importlib.resources import files

import requests
from dotenv import load_dotenv

from .storage.sqlite import DEFAULT_DB_PATH, init_db, save_issues


class Language(Enum):
    PYTHON = "Python"
    CPP = "C++"
    JAVA = "Java"
    SHELL = "Shell"
    TYPESCRIPT = "Typescript"
    RUST = "Rust"


LANGUAGE_CHOICES = [lang.value for lang in Language]
LABELS = ["good first issue"]


class Color:
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def paint(text, *styles):
    return "".join(styles) + text + Color.RESET


def parse_args():
    parser = argparse.ArgumentParser(
        prog="good-first-issue",
        description="Find open good first issues in reputable repositories.",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=LANGUAGE_CHOICES,
        default=Language.PYTHON.value,
        metavar="LANG",
        help=f"language to search (default: {Language.PYTHON.value})",
    )
    parser.add_argument(
        "-m",
        "--min-stars",
        type=int,
        default=1000,
        help="minimum star count for repositories (default: 1000)",
    )
    parser.add_argument(
        "-w",
        "--max-age",
        type=int,
        default=7,
        metavar="DAYS",
        help="only issues created within the last N days (default: 7)",
    )
    parser.add_argument(
        "-o",
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"path to the SQLite database (default: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


def build_search(language, min_stars):
    return f'language:"{language.lower()}" stars:>{min_stars} sort:stars'


def load_query(name):
    return (files("good_first_issue") / "queries" / f"{name}.graphql").read_text(
        encoding="utf-8"
    )


def run_query(variables):
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


def filter_recent_issues(repo, cutoff):
    """Keep only issues created at/after cutoff; returns None if none remain."""
    wanted = [
        issue
        for issue in repo["issues"]["nodes"]
        if datetime.datetime.fromisoformat(issue["createdAt"]) >= cutoff
    ]
    if not wanted:
        return None
    repo["issues"]["nodes"] = wanted
    repo["issues"]["totalCount"] = len(wanted)
    return repo


def print_repo(repo):
    name = paint(repo["nameWithOwner"], Color.BOLD, Color.CYAN)
    stars = paint(f"★ {repo['stargazerCount']}", Color.YELLOW)
    print(f"\n{name}  {stars}")

    for issue in repo["issues"]["nodes"]:
        number = paint(f"#{issue['number']}", Color.DIM)
        print(f"  {number} {issue['title']}")
        url = paint(issue["url"], Color.DIM)
        print(f"    {url}")


def main():
    args = parse_args()
    search = build_search(args.language, args.min_stars)
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=args.max_age)
    conn = init_db(args.db)

    cursor, repos = None, []
    while True:
        data, headers = run_query(
            {
                "query": search,
                "cursor": cursor,
                "labels": LABELS,
            }
        )
        page = data["search"]

        for repo in page["nodes"]:
            if repo["issues"]["totalCount"] == 0:
                continue
            repo = filter_recent_issues(repo, cutoff)
            if repo is None:
                continue
            repos.append(repo)
            print_repo(repo)

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    save_issues(conn, repos, args.language)
    conn.close()

    print(paint(f"\nDone: {len(repos)} repos with matching issues.", Color.BOLD))
    remaining = paint(str(int(headers["x-ratelimit-remaining"])), Color.YELLOW)
    print(f"Remaining quota: {remaining}")


if __name__ == "__main__":
    main()
