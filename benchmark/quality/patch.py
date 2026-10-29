"""Minimal unified-diff reader for agent.patch (git diff --cached bench/start)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# never part of what is analysed: harness artifacts (would reveal the level) and generated noise
HARNESS = re.compile(r"^(AGENTS\.md|CLAUDE\.md|opencode\.json|ai/|\.claude/|\.cursor/|\.vscode/)")
NOISE = re.compile(r"(^|/)(composer\.lock|package-lock\.json|yarn\.lock|pnpm-lock\.yaml)$|^public/build/|^storage/")


@dataclass
class FileDiff:
    path: str
    status: str = "modified"            # added | modified | deleted | renamed
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    text: str = ""                      # this file's section of the patch, verbatim

    @property
    def is_test(self) -> bool:
        return self.path.startswith("tests/")

    @property
    def is_blade(self) -> bool:
        return self.path.endswith(".blade.php")

    @property
    def is_php(self) -> bool:
        return self.path.endswith(".php") and not self.is_blade

    @property
    def is_production(self) -> bool:
        return (not self.is_test and self.path.startswith(("app/", "routes/", "resources/", "database/", "config/"))
                and (self.path.endswith(".php") or self.path.endswith((".js", ".css", ".scss"))))


def parse(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", line.rstrip("\n"))
            cur = FileDiff(path=m.group(2) if m else line.split()[-1][2:])
            files.append(cur)
        if cur is None:
            continue
        cur.text += line
        if line.startswith("new file mode"):
            cur.status = "added"
        elif line.startswith("deleted file mode"):
            cur.status = "deleted"
        elif line.startswith("rename to "):
            cur.status = "renamed"
        elif line.startswith("+") and not line.startswith("+++"):
            cur.added.append(line[1:].rstrip("\n"))
        elif line.startswith("-") and not line.startswith("---"):
            cur.removed.append(line[1:].rstrip("\n"))
    return files


def relevant(files: list[FileDiff]) -> list[FileDiff]:
    """Without harness artifacts and generated noise."""
    return [f for f in files if not HARNESS.match(f.path) and not NOISE.search(f.path)]
