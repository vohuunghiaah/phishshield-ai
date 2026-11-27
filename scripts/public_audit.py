"""Check the Git index that will actually be published (no raw content in diagnostics)."""
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys
import zipfile
from io import BytesIO


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    issues = []
    names = git("ls-files","-z").decode().split("\0")
    secret = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AIza[\w-]{34,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)")
    for name in filter(None,names):
        p=PurePosixPath(name)
        if (p.parts[0] in {"data","results","checkpoints","manifests",".venv","dist","private"} or
                p.suffix in {".joblib",".zip",".pt",".pth",".pkl",".parquet",".log"} or p.name in {".env","cohort.csv","desktop.ini"}):
            issues.append((name,"restricted path"))
        data=git("show",":"+name)
        if len(data)>12_000_000:
            issues.append((name,"unexpected size"))
        texts=[data]
        if p.suffix==".docx":
            with zipfile.ZipFile(BytesIO(data)) as archive:
                texts=[archive.read(k) for k in archive.namelist() if k.endswith((".xml",".rels"))]
        if any(secret.search(t) for t in texts):
            issues.append((name,"credential pattern"))
        if p.suffix==".ipynb":
            notebook=json.loads(data)
            if any(c.get("outputs") or c.get("execution_count") is not None for c in notebook["cells"]):
                issues.append((name,"notebook output"))
    if issues:
        for item in issues:
            print(*item)
        return 1
    print(f"Audited {len(names)-1} Git index entries.")
    return 0


if __name__=="__main__":
    sys.exit(main())

