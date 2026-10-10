from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoryEntry:
    timestamp: str
    kind: str
    speaker: str
    message: str
    data: dict[str, Any]


class HistoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[HistoryEntry]:
        if not self.path.exists():
            return []

        entries: list[HistoryEntry] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    entries.append(
                        HistoryEntry(
                            timestamp=str(payload.get("timestamp", "")),
                            kind=str(payload.get("kind", "log")),
                            speaker=str(payload.get("speaker", "System")),
                            message=str(payload.get("message", "")),
                            data=dict(payload.get("data", {})),
                        )
                    )
                except Exception:
                    continue
        return entries

    def append(self, kind: str, speaker: str, message: str, data: dict[str, Any] | None = None) -> HistoryEntry:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "timestamp": timestamp,
            "kind": kind,
            "speaker": speaker,
            "message": message,
            "data": data or {},
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return HistoryEntry(
            timestamp=timestamp,
            kind=kind,
            speaker=speaker,
            message=message,
            data=data or {},
        )

    @staticmethod
    def matches(entry: HistoryEntry, query: str) -> bool:
        if not query.strip():
            return True
        needle = query.lower().strip()
        haystack = " ".join(
            [
                entry.timestamp,
                entry.kind,
                entry.speaker,
                entry.message,
                json.dumps(entry.data, ensure_ascii=False),
            ]
        ).lower()
        return needle in haystack
