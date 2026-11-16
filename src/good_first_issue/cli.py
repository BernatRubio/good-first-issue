from argparse import ArgumentParser, Namespace
from enum import Enum

from .storage.sqlite import DEFAULT_DB_PATH


class Language(Enum):
    PYTHON = "Python"
    CPP = "C++"
    JAVA = "Java"
    SHELL = "Shell"
    TYPESCRIPT = "Typescript"
    RUST = "Rust"


LANGUAGE_CHOICES = [lang.value for lang in Language]
LABELS = ["good first issue"]


def parse_args() -> Namespace:
    parser = ArgumentParser(
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
        help="minimum star count (default: 1000)",
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
        help=f"path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


def build_search(language: str, min_stars: int) -> str:
    return f'language:"{language.lower()}" stars:>{min_stars} sort:stars'
