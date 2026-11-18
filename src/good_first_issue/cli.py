from argparse import ArgumentParser, Namespace
from enum import Enum

from .storage.sqlite import DEFAULT_DB_PATH


class Language(Enum):
    CPP = "c++"
    PYTHON = "python"
    JAVA = "java"
    RUST = "rust"
    SHELL = "shell"
    TYPESCRIPT = "typescript"


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
        nargs='+',
        choices=LANGUAGE_CHOICES,
        type=str.lower,
        default=[Language.PYTHON.value],
        metavar="LANG",
        help=f"Language to search (default: {Language.PYTHON.value})",
    )
    parser.add_argument(
        "-m",
        "--min-stars",
        type=int,
        default=1000,
        help="Minimum star count (default: 1000)",
        dest="min_stars"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=7,
        metavar="DAYS",
        help="Display issues created within the last N days (default: 7)",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"Path to output SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Get issues for all languages'
    )
    return parser.parse_args()


def build_search(language: str, min_stars: int) -> str:
    return f'language:"{language}" stars:>{min_stars} sort:stars'
