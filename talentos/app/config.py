from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    db_path: Path
    storage_dir: Path
    rubric_tolerance: float
    index_path: Path
    inference_backend: str
    max_batch_size: int

    @classmethod
    def from_env(cls) -> Settings:
        data_dir = Path(os.getenv("TALENTOS_DATA_DIR", "./data"))
        return cls(
            data_dir=data_dir,
            db_path=Path(os.getenv("TALENTOS_DB_PATH", str(data_dir / "talentos.db"))),
            storage_dir=Path(os.getenv("TALENTOS_STORAGE_DIR", str(data_dir / "storage"))),
            rubric_tolerance=float(os.getenv("TALENTOS_RUBRIC_TOLERANCE", "1e-6")),
            index_path=Path(os.getenv("TALENTOS_INDEX_PATH", str(data_dir / "hybrid_index.json"))),
            inference_backend=os.getenv("TALENTOS_INFERENCE_BACKEND", "offline"),
            max_batch_size=int(os.getenv("TALENTOS_MAX_BATCH_SIZE", "50")),
        )
