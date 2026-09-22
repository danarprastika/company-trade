"""
G1.9 — Correlation and Causation IDs

Trace identifiers for request tracing across the system.

Specification references:
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md:
  Command envelope: trace_id, command_id
  Event envelope: correlation_id, causation_id
- FINAL_SPECIFICATION/10_OBSERVABILITY_AND_FAILURES.md:
  "Every request/task/order/event is correlated with trace_id, request_id/task_id, event_id and relevant strategy/experiment/incident identifiers."
- docs/02_architecture/03_EVENT_ARCHITECTURE.md:
  Envelope: correlation_id, causation_id
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, Union

from .ids import CommandId, EventId, TraceId


@dataclass(frozen=True)
class CausationId:
    """
    Identifier of the command or event that caused this event.
    Can reference either a CommandId or an EventId.
    """

    value: Union[CommandId, EventId]

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"CausationId({self.value})"


@dataclass(frozen=True)
class TraceContext:
    """
    Tracing context carried across the system.
    Per OBSERVABILITY_AND_FAILURES.md: "Every request/task/order/event is correlated with trace_id."
    """

    trace_id: TraceId
    causation_id: Optional[CausationId] = None

    @classmethod
    def new(cls) -> "TraceContext":
        """Create a new trace context with a fresh trace ID."""
        return cls(trace_id=TraceId.generate())

    @classmethod
    def from_trace_id(cls, trace_id: TraceId) -> "TraceContext":
        """Create a trace context from an existing trace ID."""
        return cls(trace_id=trace_id)

    def with_causation(self, causation: Union[CommandId, EventId]) -> "TraceContext":
        """Create a new trace context with a causation ID."""
        return TraceContext(
            trace_id=self.trace_id,
            causation_id=CausationId(causation),
        )

    def __str__(self) -> str:
        return f"TraceContext(trace_id={self.trace_id}, causation_id={self.causation_id})"


__all__ = [
    "CausationId",
    "TraceContext",
]
