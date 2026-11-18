import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .cli import LABELS, Language, build_search, parse_args
from .display import print_repo, print_summary
from .filters import filter_unwanted_issues
from .github import run_query
from .storage.sqlite import init_db, save_issues


def main() -> None:
    total_issues = 0
    total_repos = 0
    rate_limit_remaining = 5000

    args = parse_args()
    if args.all:
        args.language = [l.value for l in Language]

    with ThreadPoolExecutor(max_workers=len(args.language)) as executor:
        futures = {
            executor.submit(
                _run,
                language,
                args.min_stars,
                args.max_age,
                args.db,
            ): language
            for language in args.language
        }
        for future in as_completed(futures):
            try:
                repos_processed, issues_processed, remaining_rate_limit = (
                    future.result()
                )
                total_issues += issues_processed
                total_repos += repos_processed
                rate_limit_remaining = min(rate_limit_remaining, remaining_rate_limit)
            except Exception as e:
                print(f"An error occurred while processing {futures[future]}: {e}")
    print_summary(total_repos, total_issues, rate_limit_remaining)


def _run(language: str, min_stars: int, max_age: int, db: str) -> tuple[int, int, int]:
    search = build_search(language, min_stars)
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=max_age)
    conn = init_db(db)

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

    save_issues(conn, repos, language)
    conn.close()

    total_issues = 0
    for repo in repos:
        total_issues += repo["issues"]["totalCount"]

    return len(repos), total_issues, int(headers["x-ratelimit-remaining"])
