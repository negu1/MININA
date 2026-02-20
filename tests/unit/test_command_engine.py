"""Tests for CommandEngine."""
import pytest
from core.CommandEngine.engine import CommandEngine, ParsedCommand


class TestCommandEngine:
    """Test suite for CommandEngine."""

    @pytest.fixture
    def engine(self):
        """Create a CommandEngine instance."""
        return CommandEngine()

    def test_parse_empty_string(self, engine):
        """Test parsing empty string returns None."""
        result = engine.parse("")
        assert result is None

    def test_parse_whitespace_only(self, engine):
        """Test parsing whitespace returns None."""
        result = engine.parse("   \t\n  ")
        assert result is None

    def test_parse_list_skills_intent(self, engine):
        """Test parsing list skills commands."""
        commands = [
            "lista skills",
            "listar skills",
            "skills",
            "lista skill",
            "listar skill",
        ]
        for cmd in commands:
            result = engine.parse(cmd)
            assert result is not None
            assert result.intent == "list_skills"
            assert result.raw == cmd

    def test_parse_status_intent(self, engine):
        """Test parsing status commands."""
        commands = [
            "estado",
            "status",
            "estado miia",
            "estado miia product",
        ]
        for cmd in commands:
            result = engine.parse(cmd)
            assert result is not None
            assert result.intent == "status"

    def test_parse_use_skill_with_task(self, engine):
        """Test parsing use skill command with task."""
        result = engine.parse("usa skill pc_control abrir chrome")
        assert result is not None
        assert result.intent == "use_skill"
        assert result.skill_name == "pc_control"
        assert result.task == "abrir chrome"

    def test_parse_use_skill_without_task(self, engine):
        """Test parsing use skill command without task."""
        result = engine.parse("usa skill pc_control")
        assert result is not None
        assert result.intent == "use_skill"
        assert result.skill_name == "pc_control"
        assert result.task == ""

    def test_parse_chat_intent(self, engine):
        """Test parsing chat commands."""
        result = engine.parse("hola como estas")
        assert result is not None
        assert result.intent == "chat"
        assert result.task == "hola como estas"

    def test_to_context(self, engine):
        """Test converting ParsedCommand to context."""
        cmd = ParsedCommand(raw="test", intent="chat", task="hello")
        context = engine.to_context(cmd, user_id="test_user")
        assert context["task"] == "hello"
        assert context["user_id"] == "test_user"
