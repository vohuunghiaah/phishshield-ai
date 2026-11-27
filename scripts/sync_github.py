"""Review an allowlisted source snapshot. Commit/push only via explicit flags."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import shutil

TOP = {"README.md", "pyproject.toml", "uv.lock", ".env.example", ".gitignore"}
TYPES = {
    "src": {".py"},
    "configs": {".yaml", ".json"},
    "notebooks": {".ipynb"},
    "tests": {".py"},
    "scripts": {".py"},
    "docs": {".md"},
}
SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[\w]{20,}|github_pat_[A-Za-z0-9_]{22,}|AIza[\w-]{32,}|AKIA[A-Z0-9]{16}|(?:sk-|xox[bp]-)[\w-]{20,}|(?im:^\s*(?:password|api_key|access_token|client_secret)\s*[:=]\s*[\"'][^\"'\s]{6,})"
)


def allowed(rel):
    return rel.as_posix() in TOP or (
        len(rel.parts) > 1
        and rel.parts[0] in TYPES
        and rel.suffix in TYPES[rel.parts[0]]
        and not any(p.startswith(".") for p in rel.parts)
    )


def inspect(path, rel):
    if path.is_symlink() or path.stat().st_size > 2_000_000 or not allowed(rel):
        raise ValueError(f"Rejected: {rel}")
    inspect_text(path.read_text("utf8"), rel)


def inspect_text(text, rel):
    if SECRET.search(text):
        raise ValueError(f"Possible secret: {rel}")
    if rel.suffix == ".ipynb" and any(
        c.get("outputs") or c.get("attachments") for c in json.loads(text)["cells"]
    ):
        raise ValueError(f"Clear notebook output/attachments: {rel}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--repo", type=Path)
    p.add_argument("--commit", metavar="MESSAGE")
    p.add_argument("--push", action="store_true")
    args = p.parse_args()
    src = args.source.resolve()
    repo = (args.repo or src).resolve(strict=True)

    def git(*argv):
        return subprocess.check_output(
            ["git", "-C", str(repo), *argv], text=True
        ).strip()

    if (
        Path(git("rev-parse", "--show-toplevel")).resolve() != repo
        or git("branch", "--show-current") != "main"
    ):
        raise ValueError("Cần repository main tại đúng đường dẫn --repo.")
    if git("diff", "--cached", "--name-only"):
        raise ValueError("Index có thay đổi đang stage. Kiểm tra trước khi đồng bộ.")
    items = []
    for base in sorted(TOP | TYPES.keys()):
        folder = src / base
        for file in sorted(folder.rglob("*")) if folder.is_dir() else [folder]:
            rel = file.relative_to(src)
            if not file.is_file() or not allowed(rel):
                continue
            if not file.resolve().is_relative_to(src):
                raise ValueError(rel)
            inspect(file, rel)
            items.append(rel)
    # Refuse a repository whose tracked tree already contains forbidden material.
    for tracked in git("ls-files", "-z").split("\0"):
        if tracked and not allowed(Path(tracked)):
            raise ValueError("Disallowed tracked path: " + tracked)
    for banned in [
        "data/raw/file.zip",
        "checkpoints/a.joblib",
        ".env",
        "secrets/credentials.json",
    ]:
        if (
            src == repo
            and subprocess.run(
                ["git", "-C", str(src), "check-ignore", "--no-index", "-q", banned]
            ).returncode
        ):
            raise ValueError("Missing ignore protection: " + banned)
    for rel in items:
        print(rel.as_posix())
    if args.push and not args.commit:
        raise ValueError("--push yêu cầu --commit và kiểm tra trong cùng phiên.")
    if not args.commit:
        return
    if args.push:
        remote = git("remote", "get-url", "--push", "--all", "origin")
        match = re.fullmatch(
            r"(?:https://github\.com/|git@github\.com:)([\w.-]+)/phishshield-ai(?:\.git)?",
            remote,
        )
        if not match:
            raise ValueError("Kiểm tra remote GitHub đích.")
        owner = match.group(1)
        remote_info = json.loads(
            subprocess.check_output(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{owner}/phishshield-ai",
                    "--json",
                    "nameWithOwner,visibility",
                ],
                text=True,
            )
        )
        if (
            remote_info["visibility"] != "PRIVATE"
            or remote_info["nameWithOwner"].lower() != f"{owner}/phishshield-ai".lower()
        ):
            raise ValueError("Cần xác minh đúng repository private trước khi push.")
        # Inspect every blob reachable from main before publishing its history.
        exists = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", "HEAD"],
            capture_output=True,
        )
        if exists.returncode == 0:
            seen = set()
            for commit in git("rev-list", "HEAD").splitlines():
                for entry in git("ls-tree", "-rz", "--full-tree", commit).split("\0"):
                    if not entry:
                        continue
                    head, filename = entry.split("\t", 1)
                    mode, kind, oid = head.split()
                    rel = Path(filename)
                    if mode not in ("100644", "100755") or not allowed(rel):
                        raise ValueError("Disallowed historical path: " + filename)
                    if oid in seen:
                        continue
                    if int(git("cat-file", "-s", oid)) > 2_000_000:
                        raise ValueError("Large historical blob: " + filename)
                    body = subprocess.check_output(
                        ["git", "-C", str(repo), "cat-file", "blob", oid]
                    ).decode("utf8")
                    inspect_text(body, rel)
                    seen.add(oid)
    for rel in items:
        dst = repo / rel
        if not dst.resolve().is_relative_to(repo):
            raise ValueError(rel)
        if repo != src:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / rel, dst)
        inspect(dst, rel)
    git("add", "--", *[p.as_posix() for p in items])
    print(git("diff", "--cached", "--stat"))
    if git("diff", "--cached", "--name-only"):
        git("commit", "-m", args.commit)
    if args.push:
        git("push", "--no-follow-tags", "-u", "origin", "main")


if __name__ == "__main__":
    main()
