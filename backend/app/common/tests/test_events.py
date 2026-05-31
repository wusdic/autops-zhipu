"""EventBus 单元测试."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.events import (
    DomainEvent,
    EventBus,
    EventPriority,
    get_event_bus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bus():
    """Provide a fresh EventBus for each test."""
    b = EventBus()
    return b


def _make_event(**overrides) -> DomainEvent:
    defaults = dict(
        event_type="test.event",
        domain="test",
        payload={"key": "value"},
        priority=EventPriority.NORMAL,
        source="test_suite",
    )
    defaults.update(overrides)
    return DomainEvent(**defaults)


# ---------------------------------------------------------------------------
# Test: publish / subscribe basics
# ---------------------------------------------------------------------------

class TestPubSub:
    async def test_sync_handler_called(self, bus):
        handler = MagicMock()
        bus.subscribe("test.event", handler)

        event = _make_event()
        await bus.publish(event)

        handler.assert_called_once_with(event)

    async def test_async_handler_called(self, bus):
        handler = AsyncMock()
        bus.subscribe("test.event", handler)

        event = _make_event()
        await bus.publish(event)

        handler.assert_called_once_with(event)

    async def test_multiple_handlers(self, bus):
        h1 = MagicMock()
        h2 = AsyncMock()
        bus.subscribe("test.event", h1)
        bus.subscribe("test.event", h2)

        event = _make_event()
        await bus.publish(event)

        h1.assert_called_once_with(event)
        h2.assert_called_once_with(event)

    async def test_handler_not_called_for_different_event(self, bus):
        handler = MagicMock()
        bus.subscribe("test.event", handler)

        event = _make_event(event_type="other.event")
        await bus.publish(event)

        handler.assert_not_called()

    async def test_wildcard_handler(self, bus):
        handler = MagicMock()
        bus.subscribe_all(handler)

        event = _make_event()
        await bus.publish(event)

        handler.assert_called_once_with(event)


# ---------------------------------------------------------------------------
# Test: unsubscribe
# ---------------------------------------------------------------------------

class TestUnsubscribe:
    async def test_unsubscribe(self, bus):
        handler = MagicMock()
        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)

        event = _make_event()
        await bus.publish(event)

        handler.assert_not_called()

    async def test_unsubscribe_only_removes_specific_handler(self, bus):
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe("test.event", h1)
        bus.subscribe("test.event", h2)
        bus.unsubscribe("test.event", h1)

        event = _make_event()
        await bus.publish(event)

        h1.assert_not_called()
        h2.assert_called_once_with(event)


# ---------------------------------------------------------------------------
# Test: event logging
# ---------------------------------------------------------------------------

class TestEventLog:
    async def test_event_logged(self, bus):
        event = _make_event()
        await bus.publish(event)

        log = bus.get_recent_events()
        assert len(log) == 1
        assert log[0]["event_type"] == "test.event"
        assert log[0]["domain"] == "test"

    async def test_event_log_limit(self, bus):
        bus._max_log_size = 5
        for i in range(10):
            await bus.publish(_make_event(payload={"i": i}))

        log = bus.get_recent_events()
        assert len(log) == 5

    async def test_get_recent_events_with_limit(self, bus):
        for i in range(20):
            await bus.publish(_make_event(payload={"i": i}))

        log = bus.get_recent_events(limit=5)
        assert len(log) == 5


# ---------------------------------------------------------------------------
# Test: clear
# ---------------------------------------------------------------------------

class TestClear:
    async def test_clear_removes_all(self, bus):
        bus.subscribe("test.event", MagicMock())
        bus.subscribe_all(MagicMock())
        await bus.publish(_make_event())

        bus.clear()

        assert len(bus._handlers) == 0
        assert len(bus._wildcard_handlers) == 0
        assert len(bus._event_log) == 0


# ---------------------------------------------------------------------------
# Test: event priority
# ---------------------------------------------------------------------------

class TestEventPriority:
    def test_priority_values(self):
        assert EventPriority.LOW == 0
        assert EventPriority.NORMAL == 1
        assert EventPriority.HIGH == 2
        assert EventPriority.CRITICAL == 3

    def test_priority_ordering(self):
        assert EventPriority.LOW < EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL

    async def test_event_with_priority(self, bus):
        handler = MagicMock()
        bus.subscribe("critical.event", handler)

        event = DomainEvent(
            event_type="critical.event",
            domain="test",
            priority=EventPriority.CRITICAL,
        )
        await bus.publish(event)

        handler.assert_called_once()
        logged = bus.get_recent_events()
        assert logged[0]["priority"] == EventPriority.CRITICAL.value


# ---------------------------------------------------------------------------
# Test: handler exceptions don't break other handlers
# ---------------------------------------------------------------------------

class TestHandlerErrorHandling:
    async def test_failing_handler_does_not_stop_others(self, bus):
        good_handler = MagicMock()

        def bad_handler(event):
            raise RuntimeError("boom")

        bus.subscribe("test.event", bad_handler)
        bus.subscribe("test.event", good_handler)

        event = _make_event()
        await bus.publish(event)

        # Good handler should still be called even after bad handler fails
        good_handler.assert_called_once_with(event)

    async def test_async_failing_handler_does_not_stop_others(self, bus):
        good_handler = MagicMock()

        async def bad_handler(event):
            raise RuntimeError("async boom")

        bus.subscribe("test.event", bad_handler)
        bus.subscribe("test.event", good_handler)

        event = _make_event()
        await bus.publish(event)

        good_handler.assert_called_once_with(event)


# ---------------------------------------------------------------------------
# Test: DomainEvent
# ---------------------------------------------------------------------------

class TestDomainEvent:
    def test_to_dict(self):
        event = DomainEvent(
            event_type="test.event",
            domain="test",
            payload={"key": "value"},
            priority=EventPriority.HIGH,
            source="unittest",
            correlation_id="corr-001",
        )
        d = event.to_dict()

        assert d["event_type"] == "test.event"
        assert d["domain"] == "test"
        assert d["payload"] == {"key": "value"}
        assert d["priority"] == EventPriority.HIGH.value
        assert d["source"] == "unittest"
        assert d["correlation_id"] == "corr-001"
        assert "event_id" in d
        assert "timestamp" in d

    def test_default_values(self):
        event = DomainEvent(event_type="test", domain="test")
        assert event.priority == EventPriority.NORMAL
        assert event.source == ""
        assert event.correlation_id == ""
        assert event.payload == {}
        assert event.event_id  # non-empty UUID string
        assert event.timestamp  # non-empty ISO timestamp

    def test_unique_event_ids(self):
        e1 = DomainEvent(event_type="test", domain="test")
        e2 = DomainEvent(event_type="test", domain="test")
        assert e1.event_id != e2.event_id


# ---------------------------------------------------------------------------
# Test: get_event_bus singleton
# ---------------------------------------------------------------------------

class TestGetEventBus:
    def test_returns_event_bus(self):
        bus = get_event_bus()
        assert isinstance(bus, EventBus)

    def test_singleton(self):
        # Clear lru_cache first to ensure consistency
        get_event_bus.cache_clear()
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2
