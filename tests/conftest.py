"""
Test fixtures and configuration for MININA tests.
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Ensure core is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp(prefix="minina_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_bus():
    """Mock CortexBus for testing."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    bus.publish_sync = MagicMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def sample_skill_code():
    """Sample valid skill code for testing."""
    return '''
def execute(context):
    """Sample skill that echoes context."""
    return {
        "success": True,
        "message": f"Received: {context.get('task', 'no task')}",
        "data": context
    }
'''


@pytest.fixture
def sample_skill_yaml():
    """Sample skill.yaml content."""
    return """
name: Test Skill
id: test_skill
version: 1.0.0
permissions:
  - fs_read
  - network
message: Test skill for unit tests
"""


@pytest.fixture
def sample_manifest():
    """Sample manifest.json content."""
    return {
        "id": "test_skill",
        "name": "Test Skill",
        "version": "1.0.0",
        "permissions": ["fs_read", "network"]
    }
