import os
import zipfile
from datetime import datetime


def should_exclude(path: str) -> bool:
    norm = path.replace("\\", "/")
    parts = set(norm.split("/"))
    excluded = {"__pycache__", "htmlcov", "miia_skill_sim", "backups"}
    return any(p in excluded for p in parts)


def create_checkpoint_zip(project_root: str) -> str:
    project_root = os.path.abspath(project_root)
    backup_dir = os.path.join(project_root, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"checkpoint_{ts}.zip")

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in os.walk(project_root):
            if should_exclude(dirpath):
                continue
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                if should_exclude(fp):
                    continue
                arcname = os.path.relpath(fp, project_root)
                zf.write(fp, arcname)

    return dest


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = create_checkpoint_zip(root)
    print(f"CHECKPOINT_ZIP={out}")
