from typing import Protocol


class StoragePort(Protocol):
    def put(self, key: str, data: bytes) -> str:
        """Store bytes under key and return the resolved location."""
        ...

    def get(self, key: str) -> bytes | None:
        ...

    def delete(self, key: str) -> bool:
        """Return True when something was removed."""
        ...
