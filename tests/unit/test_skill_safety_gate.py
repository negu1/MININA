"""Tests for SkillSafetyGate security validation."""
import pytest
import tempfile
import zipfile
from pathlib import Path
from core.SkillSafetyGate import SkillSafetyGate, _ast_check, _safe_zip_members


class TestSkillSafetyGate:
    """Test suite for skill security validation."""

    @pytest.fixture
    def gate(self):
        """Create a SkillSafetyGate instance."""
        return SkillSafetyGate()

    def test_ast_check_valid_skill(self, gate):
        """Test AST check passes for valid skill code."""
        code = '''
def execute(context):
    """Valid skill."""
    return {"success": True, "message": "Hello"}
'''
        reasons = _ast_check(code, permissions=[])
        assert len(reasons) == 0

    def test_ast_check_forbidden_import(self, gate):
        """Test AST check catches forbidden imports."""
        code = '''
import subprocess
def execute(context):
    subprocess.run(["ls"])
    return {"success": True}
'''
        reasons = _ast_check(code, permissions=[])
        assert any("subprocess" in r for r in reasons)

    def test_ast_check_eval_exec(self, gate):
        """Test AST check catches eval/exec calls."""
        code = '''
def execute(context):
    eval("1 + 1")
    return {"success": True}
'''
        reasons = _ast_check(code, permissions=[])
        assert any("eval" in r for r in reasons)

    def test_ast_check_network_without_permission(self, gate):
        """Test AST check requires network permission."""
        code = '''
import requests
def execute(context):
    requests.get("https://example.com")
    return {"success": True}
'''
        reasons = _ast_check(code, permissions=[])
        assert any("network" in r.lower() for r in reasons)

    def test_ast_check_network_with_permission(self, gate):
        """Test AST check allows network with permission."""
        code = '''
import requests
def execute(context):
    requests.get("https://example.com")
    return {"success": True}
'''
        reasons = _ast_check(code, permissions=["network"])
        assert not any("network" in r.lower() for r in reasons)

    def test_ast_check_os_system(self, gate):
        """Test AST check catches os.system."""
        code = '''
import os
def execute(context):
    os.system("rm -rf /")
    return {"success": True}
'''
        reasons = _ast_check(code, permissions=[])
        # Should detect the system call
        assert any("system" in r or "ejecución" in r for r in reasons)

    def test_safe_zip_members_valid(self, tmp_path):
        """Test safe zip validation passes for valid zip."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("skill.py", "def execute(c): pass")
            zf.writestr("manifest.json", '{"id": "test"}')
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            ok, reasons = _safe_zip_members(zf)
            assert ok is True
            assert len(reasons) == 0

    def test_safe_zip_members_path_traversal(self, tmp_path):
        """Test safe zip catches path traversal."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../../../etc/passwd", "malicious")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            ok, reasons = _safe_zip_members(zf)
            assert ok is False
            assert any("traversal" in r.lower() for r in reasons)

    def test_safe_zip_members_absolute_path(self, tmp_path):
        """Test safe zip catches absolute paths."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("/etc/passwd", "malicious")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            ok, reasons = _safe_zip_members(zf)
            assert ok is False
            assert any("absoluta" in r.lower() for r in reasons)

    def test_prepare_extracted_dir_with_yaml(self, tmp_path, gate):
        """Test preparing extracted dir with skill.yaml."""
        extracted = tmp_path / "extracted"
        extracted.mkdir()
        
        yaml_content = """
name: Test Skill
id: test_skill
version: 1.0
permissions:
  - fs_read
message: Hello from test
"""
        (extracted / "skill.yaml").write_text(yaml_content)
        
        report = gate.prepare_extracted_dir(extracted)
        assert report.ok is True
        assert report.skill_id == "test_skill"
        assert report.name == "Test Skill"
        assert "fs_read" in report.permissions

    def test_prepare_extracted_dir_missing_entrypoint(self, tmp_path, gate):
        """Test preparing dir without entrypoint fails."""
        extracted = tmp_path / "extracted"
        extracted.mkdir()
        # No skill.yaml, no main.py, no skill.py
        
        report = gate.prepare_extracted_dir(extracted)
        assert report.ok is False
        assert any("entrypoint" in r.lower() for r in report.reasons)

    def test_safety_report_structure(self, gate):
        """Test SafetyReport dataclass structure."""
        from core.SkillSafetyGate import SafetyReport
        
        report = SafetyReport(
            ok=True,
            skill_id="test",
            name="Test Skill",
            version="1.0",
            permissions=["fs_read"],
            reasons=[]
        )
        
        assert report.ok is True
        assert report.skill_id == "test"
        assert report.name == "Test Skill"
        assert report.version == "1.0"
        assert report.permissions == ["fs_read"]
        assert report.reasons == []
