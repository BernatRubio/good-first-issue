import datetime

from .cli import LABELS, build_search, parse_args
from .display import print_repo, print_summary
from .filters import filter_unwanted_issues
from .github import run_query
from .storage.sqlite import init_db, save_issues


def main():
    args = parse_args()
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
