from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_repo_ref(value: str) -> RepoRef:
    """Parse a GitHub repository reference into owner/repo.

    Supported initially: owner/repo and https://github.com/owner/repo(.git).
    """
    raw = value.strip()
    if not raw:
        raise ValueError("empty repository reference")

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        if parsed.hostname != "github.com":
            raise ValueError("repository URL must use github.com")
        raw = parsed.path.strip("/")

    if raw.endswith(".git"):
        raw = raw[:-4]

    parts = raw.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("repository reference must be owner/repo")

    return RepoRef(parts[0], parts[1])
