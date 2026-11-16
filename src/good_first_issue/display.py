class Color:
    BOLD   = "\033[1m"
    CYAN   = "\033[36m"
    YELLOW = "\033[33m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"


def paint(text: str, *styles: str) -> str:
    return "".join(styles) + text + Color.RESET


def print_repo(repo: dict) -> None:
    name  = paint(repo["nameWithOwner"], Color.BOLD, Color.CYAN)
    stars = paint(f"★ {repo['stargazerCount']}", Color.YELLOW)
    print(f"\n{name}  {stars}")
    for issue in repo["issues"]["nodes"]:
        number = paint(f"#{issue['number']}", Color.DIM)
        print(f"  {number} {issue['title']}")
        print(f"    {paint(issue['url'], Color.DIM)}")


def print_summary(repo_count: int, quota_remaining: int) -> None:
    print(paint(f"\nDone: {repo_count} repos with matching issues.", Color.BOLD))
    print(f"Remaining quota: {paint(str(quota_remaining), Color.YELLOW)}")
