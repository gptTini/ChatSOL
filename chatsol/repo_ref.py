from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def _github_path_from_remote(raw: str) -> str:
    if "://" in raw:
        parsed = urlparse(raw)
        if parsed.scheme.lower() not in {"https", "ssh", "git"}:
            raise ValueError("unsupported repository URL scheme")
        if (parsed.hostname or "").lower() != "github.com":
            raise ValueError("repository URL must use github.com")
        return parsed.path.strip("/")

    if raw.startswith("git@"):
        try:
            host, path = raw[4:].split(":", 1)
        except ValueError as exc:
            raise ValueError("invalid SSH repository reference") from exc
        if host.lower() != "github.com":
            raise ValueError("SSH repository URL must use github.com")
        return path.strip("/")

    return raw


def parse_repo_ref(value: str) -> RepoRef:
    """Parse common GitHub repository references into ``owner/repo``."""
    raw = value.strip()
    if not raw:
        raise ValueError("empty repository reference")

    raw = _github_path_from_remote(raw)

    if raw.endswith(".git"):
        raw = raw[:-4]

    parts = raw.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("repository reference must be owner/repo")

    return RepoRef(parts[0], parts[1])
