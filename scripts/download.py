from phishshield.data.download import download
from phishshield.utils.storage import resolve_drive_root, validate_drive_access

if __name__ == "__main__":
    root = resolve_drive_root()
    validate_drive_access(root)
    download(root)
