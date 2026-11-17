import datetime
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, as_completed

from .cli import LABELS, Language, build_search, parse_args
from .display import print_repo, print_summary
from .filters import filter_unwanted_issues
from .github import run_query
from .storage.sqlite import DEFAULT_DB_PATH, init_db, save_issues


def main() -> None:
    args = parse_args()
    total_issues, total_repos, rate_limit_remaining = _run(args)
    print_summary(total_repos, total_issues, rate_limit_remaining)


def main_all() -> None:
    total_issues = 0
    total_repos = 0
    rate_limit_remaining = 5000

    with ThreadPoolExecutor(max_workers=len(Language)) as executor:
        futures = {
            executor.submit(_run, Namespace(language=lang.value,min_stars=1000,max_age=7,db=DEFAULT_DB_PATH)): lang
            for lang in Language
        }
        for future in as_completed(futures):
            try:
                repos_processed, issues_processed, remaining_rate_limit = future.result()
                total_issues += issues_processed
                total_repos += repos_processed
                rate_limit_remaining = min(rate_limit_remaining, remaining_rate_limit)
            except Exception as e:
                print(
                    f"An error occurred while processing {futures[future]}: {e}"
                )
    print_summary(total_repos, total_issues, rate_limit_remaining)

def _run(args: Namespace) -> tuple[int, int, int]:
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

    total_issues = 0
    for repo in repos:
        total_issues += repo["issues"]["totalCount"]

    return len(repos), total_issues, int(headers["x-ratelimit-remaining"])
