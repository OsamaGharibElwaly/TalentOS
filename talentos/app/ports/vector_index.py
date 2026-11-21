from typing import Protocol

from app.domain.models import SearchHit


class VectorIndexPort(Protocol):
    def upsert(
        self, doc_id: str, tenant_id: str, text: str, metadata: dict[str, object]
    ) -> None: ...

    def search(
        self,
        tenant_id: str,
        query: str,
        *,
        top_k: int = 10,
        metadata_filter: dict[str, object] | None = None,
    ) -> list[SearchHit]: ...
