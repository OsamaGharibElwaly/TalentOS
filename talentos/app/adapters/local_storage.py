from pathlib import Path

from app.ports.storage import StoragePort


class LocalStorage(StoragePort):
    """Filesystem StoragePort rooted at a local directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _resolve(self, key: str) -> Path:
        root = self._root.resolve()
        target = (root / key).resolve()
        if target != root and root not in target.parents:
            raise ValueError("storage key escapes the storage root")
        return target

    def put(self, key: str, data: bytes) -> str:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return str(target)

    def get(self, key: str) -> bytes | None:
        target = self._resolve(key)
        return target.read_bytes() if target.is_file() else None

    def delete(self, key: str) -> bool:
        target = self._resolve(key)
        if not target.is_file():
            return False
        target.unlink()
        return True
