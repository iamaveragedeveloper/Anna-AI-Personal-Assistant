"""
Unit tests for Skill System.

Tests BaseSkill, SkillLoader, and skill routing.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to sys.path to ensure modules can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.skill_loader import SkillLoader
from skills.base_skill import BaseSkill
from typing import Dict, Any, List


class MockSkill(BaseSkill):
    """Mock skill for testing."""
    
    @property
    def name(self) -> str:
        return "mock"
    
    @property
    def description(self) -> str:
        return "Mock skill for testing"
    
    @property
    def trigger_phrases(self) -> List[str]:
        return ["test", "mock"]
    
    def execute(self, params: Dict[str, Any]) -> str:
        if params.get("error"):
            raise ValueError("Mock error")
        return f"Mock executed with: {params}"


class TestSkillLoader:
    """Test suite for SkillLoader class."""
    
    @pytest.fixture
    def skill_loader(self):
        """Create skill loader instance for testing."""
        return SkillLoader()
    
    def test_initialization(self, skill_loader):
        """Test that skill loader initializes correctly."""
        assert skill_loader is not None
        assert isinstance(skill_loader.skills, dict)
    
    def test_skill_loading(self, skill_loader):
        """Test that skills are loaded."""
        skill_names = skill_loader.get_skill_names()
        assert isinstance(skill_names, list)
    
    def test_get_skill(self, skill_loader):
        """Test getting skill by name."""
        skill = skill_loader.get_skill("notion")
        
        if skill:
            assert skill.name == "notion"
            assert hasattr(skill, 'execute')
    
    def test_get_nonexistent_skill(self, skill_loader):
        """Test getting skill that doesn't exist."""
        skill = skill_loader.get_skill("nonexistent_skill_xyz")
        assert skill is None
    
    def test_skills_context_generation(self, skill_loader):
        """Test generating context for LLM."""
        context = skill_loader.get_skills_context()
        
        assert isinstance(context, str)
        if skill_loader.skills:
            assert len(context) > 0
    
    def test_execute_invalid_skill(self, skill_loader):
        """Test executing nonexistent skill."""
        result = skill_loader.execute_skill("invalid_skill", {})
        
        assert "Unknown skill" in result or "not found" in result.lower()


class TestBaseSkill:
    """Test suite for BaseSkill base class."""
    
    @pytest.fixture
    def mock_skill(self):
        """Create mock skill instance for testing."""
        return MockSkill()
    
    def test_skill_properties(self, mock_skill):
        """Test that skill properties are accessible."""
        assert mock_skill.name == "mock"
        assert isinstance(mock_skill.description, str)
        assert isinstance(mock_skill.trigger_phrases, list)
    
    def test_skill_execute(self, mock_skill):
        """Test skill execution."""
        result = mock_skill.execute({"test": "data"})
        assert "Mock executed" in result
    
    def test_skill_error_handling(self, mock_skill):
        """Test skill error handling."""
        with pytest.raises(ValueError):
            mock_skill.execute({"error": True})
    
    def test_validate_params(self, mock_skill):
        """Test parameter validation helper."""
        assert mock_skill.validate_params({"a": 1, "b": 2}, ["a", "b"]) == True
        assert mock_skill.validate_params({"a": 1}, ["a", "b"]) == False
    
    def test_get_context(self, mock_skill):
        """Test context generation."""
        context = mock_skill.get_context()
        
        assert "mock" in context
        assert "Mock skill for testing" in context
        # Context no longer includes a SKILL/PARAMS usage block - format defined in config.py
        assert "Trigger phrases" in context


def test_skill_module_imports():
    """Test that skill modules import successfully."""
    from core import skill_loader
    from skills import base_skill
    
    assert hasattr(skill_loader, 'SkillLoader')
    assert hasattr(base_skill, 'BaseSkill')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
