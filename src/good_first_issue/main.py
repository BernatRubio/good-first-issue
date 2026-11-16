import datetime
from argparse import Namespace

from .cli import LABELS, Language, build_search, parse_args
from .display import print_repo, print_summary
from .filters import filter_unwanted_issues
from .github import run_query
from .storage.sqlite import DEFAULT_DB_PATH, init_db, save_issues


def main() -> None:
    args = parse_args()
    _run(args)


def main_all() -> None:
    for lang in Language:
        args = Namespace(
            language=lang.value,
            min_stars=1000,
            max_age=7,
            db=DEFAULT_DB_PATH,
        )
        _run(args)


def _run(args: Namespace) -> None:
    search = build_search(args.language, args.min_stars)
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=args.max_age)
    conn = init_db(args.db)

    cursor, repos = None, []
    while True:
        data, headers = run_query({"query": search, "cursor": cursor, "labels": LABELS})
        page = data["search"]

        for repo in page["nodes"]:
            if repo["issues"]["totalCount"] == 0:
                continue
            repo = filter_unwanted_issues(repo, cutoff)
            if repo is None:
                continue
            repos.append(repo)
            print_repo(repo)

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    save_issues(conn, repos, args.language)
    conn.close()
    print_summary(len(repos), int(headers["x-ratelimit-remaining"]))
