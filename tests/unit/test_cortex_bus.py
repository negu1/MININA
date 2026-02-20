"""Tests for CortexBus event system."""
import pytest
import asyncio
from core.CortexBus import CortexBus


class TestCortexBus:
    """Test suite for CortexBus pub/sub system."""

    @pytest.fixture
    def bus(self):
        """Create a fresh CortexBus instance."""
        return CortexBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        """Test basic subscribe and publish functionality."""
        received = []
        
        def callback(data):
            received.append(data)
        
        bus.subscribe("test.topic", callback)
        await bus.publish("test.topic", {"message": "hello"}, sender="test")
        
        assert len(received) == 1
        assert received[0] == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        """Test multiple subscribers receive the same message."""
        received1 = []
        received2 = []
        
        bus.subscribe("test.topic", lambda d: received1.append(d))
        bus.subscribe("test.topic", lambda d: received2.append(d))
        
        await bus.publish("test.topic", "data", sender="test")
        
        assert len(received1) == 1
        assert len(received2) == 1
        assert received1[0] == received2[0]

    @pytest.mark.asyncio
    async def test_wildcard_subscriber(self, bus):
        """Test wildcard subscriber receives all events."""
        received = []
        bus.subscribe("*", lambda d: received.append(d))
        
        await bus.publish("topic1", "data1", sender="test")
        await bus.publish("topic2", "data2", sender="test")
        
        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_async_callback(self, bus):
        """Test async callback functions."""
        received = []
        
        async def async_callback(data):
            received.append(data)
        
        bus.subscribe("test.topic", async_callback)
        await bus.publish("test.topic", "async_data", sender="test")
        
        assert len(received) == 1
        assert received[0] == "async_data"

    @pytest.mark.asyncio
    async def test_publish_sync(self, bus):
        """Test synchronous publish works correctly."""
        received = []
        bus.subscribe("test.sync", lambda d: received.append(d))
        
        bus.publish_sync("test.sync", "sync_data", sender="test")
        await asyncio.sleep(0.1)  # Allow async processing
        
        assert len(received) == 1

    def test_subscribe_duplicate_callback(self, bus):
        """Test that duplicate callbacks are handled."""
        def callback(data):
            pass
        
        key1 = bus.subscribe("test.topic", callback)
        key2 = bus.subscribe("test.topic", callback)
        
        # Should return same key for duplicate
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_event_structure(self, bus):
        """Test that published events have correct structure."""
        received_event = []
        bus.subscribe("*", lambda e: received_event.append(e))
        
        await bus.publish("test.topic", {"key": "value"}, sender="TestSender")
        
        event = received_event[0]
        assert "topic" in event
        assert "data" in event
        assert "sender" in event
        assert "timestamp" in event
        assert event["topic"] == "test.topic"
        assert event["sender"] == "TestSender"
        assert event["data"] == {"key": "value"}
