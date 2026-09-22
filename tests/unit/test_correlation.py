"""
G1.9 — Unit tests for Correlation and Causation IDs

Tests:
- TraceContext creation
- CausationId wrapping
- Trace ID propagation
"""

import pytest
from src.domain.correlation import TraceContext, CausationId
from src.domain.ids import CommandId, EventId, TraceId


class TestTraceContext:
    def test_new_creates_fresh_trace(self):
        """TraceContext.new() should create a fresh trace ID."""
        ctx = TraceContext.new()
        assert ctx.trace_id is not None
        assert isinstance(ctx.trace_id, TraceId)
        assert ctx.causation_id is None

    def test_from_trace_id(self):
        """TraceContext.from_trace_id should reuse an existing trace ID."""
        trace_id = TraceId.generate()
        ctx = TraceContext.from_trace_id(trace_id)
        assert ctx.trace_id == trace_id
        assert ctx.causation_id is None

    def test_with_causation_command(self):
        """with_causation should set causation from a CommandId."""
        ctx = TraceContext.new()
        cmd_id = CommandId.generate()
        new_ctx = ctx.with_causation(cmd_id)
        assert new_ctx.trace_id == ctx.trace_id
        assert new_ctx.causation_id is not None
        assert str(new_ctx.causation_id) == str(cmd_id)

    def test_with_causation_event(self):
        """with_causation should set causation from an EventId."""
        ctx = TraceContext.new()
        event_id = EventId.generate()
        new_ctx = ctx.with_causation(event_id)
        assert new_ctx.trace_id == ctx.trace_id
        assert new_ctx.causation_id is not None
        assert str(new_ctx.causation_id) == str(event_id)

    def test_trace_id_preserved_across_causation(self):
        """Trace ID should be preserved when adding causation."""
        ctx = TraceContext.new()
        cmd_id = CommandId.generate()
        new_ctx = ctx.with_causation(cmd_id)
        assert new_ctx.trace_id == ctx.trace_id

    def test_str_representation(self):
        """str() should include trace_id and causation_id."""
        ctx = TraceContext.new()
        s = str(ctx)
        assert "trace_id" in s
        assert "causation_id" in s


class TestCausationId:
    def test_wraps_command_id(self):
        """CausationId should wrap a CommandId."""
        cmd_id = CommandId.generate()
        causation = CausationId(cmd_id)
        assert str(causation) == str(cmd_id)

    def test_wraps_event_id(self):
        """CausationId should wrap an EventId."""
        event_id = EventId.generate()
        causation = CausationId(event_id)
        assert str(causation) == str(event_id)

    def test_repr(self):
        """repr() should include CausationId."""
        cmd_id = CommandId.generate()
        causation = CausationId(cmd_id)
        assert "CausationId" in repr(causation)
