import datetime


def filter_unwanted_issues(repo: dict, cutoff: datetime.datetime) -> dict | None:
    """Keep only issues created at/after cutoff with no linked PR."""
    wanted = [
        issue
        for issue in repo["issues"]["nodes"]
        if datetime.datetime.fromisoformat(issue["createdAt"]) >= cutoff
        and not issue["closedByPullRequestsReferences"]["totalCount"]
    ]
    if not wanted:
        return None
    return {
        **repo,
        "issues": {**repo["issues"], "nodes": wanted, "totalCount": len(wanted)},
    }
