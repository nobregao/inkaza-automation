import os
import re
import subprocess
from pathlib import Path


VERSION_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
BREAKING_HEADER = re.compile(r"^feat(?:\([^)]+\))?!:", re.MULTILINE)
BREAKING_BODY = re.compile(r"^BREAKING[ -]CHANGE:", re.MULTILINE)
FEATURE = re.compile(r"^feat(?:\([^)]+\))?:", re.MULTILINE)
FIX = re.compile(r"^fix(?:\([^)]+\))?:", re.MULTILINE)


def determine_bump(messages: str) -> str | None:
    if BREAKING_HEADER.search(messages) or BREAKING_BODY.search(messages):
        return "major"
    if FEATURE.search(messages):
        return "minor"
    if FIX.search(messages):
        return "patch"
    return None


def increment(version: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def latest_version_tag() -> tuple[str | None, tuple[int, int, int]]:
    tags = subprocess.check_output(
        ["git", "tag", "--merged", "HEAD"], text=True
    ).splitlines()
    versions = []
    for tag in tags:
        match = VERSION_TAG.fullmatch(tag)
        if match:
            versions.append((tuple(map(int, match.groups())), tag))

    if not versions:
        return None, (0, 0, 0)
    version, tag = max(versions)
    return tag, version


def commits_after(tag: str | None) -> str:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    return subprocess.check_output(
        ["git", "log", revision, "--format=%B"], text=True
    )


def calculate_next_version() -> tuple[str, str, str]:
    current_tag, current_version = latest_version_tag()
    bump = determine_bump(commits_after(current_tag))
    if bump is None:
        reference = current_tag or "o início do histórico"
        raise RuntimeError(
            f"Nenhum fix, feat ou breaking change encontrado após {reference}"
        )

    next_version = ".".join(map(str, increment(current_version, bump)))
    return next_version, f"v{next_version}", bump


def main():
    version, tag, bump = calculate_next_version()
    output = f"version={version}\ntag={tag}\nbump={bump}\n"
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as output_file:
            output_file.write(output)
    print(output, end="")


if __name__ == "__main__":
    main()
