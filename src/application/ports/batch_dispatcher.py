from __future__ import annotations

from typing import Protocol
from uuid import UUID


class BatchDispatcherProtocol(Protocol):
    def dispatch(self, organization_id: UUID, batch_id: UUID, row_indices: list[int]) -> None: ...
