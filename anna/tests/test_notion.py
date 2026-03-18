"""
Unit tests for Notion Skill.

Tests Notion integration and page creation.
"""

import pytest
import os
import sys

# Add project root to sys.path to ensure modules can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from skills.notion_skill import NotionSkill
import config


class TestNotionSkill:
    """Test suite for NotionSkill class."""
    
    @pytest.fixture
    def notion_skill(self):
        """Create Notion skill instance for testing."""
        return NotionSkill()
    
    def test_initialization(self, notion_skill):
        """Test that Notion skill initializes."""
        assert notion_skill is not None
        assert notion_skill.name == "notion"
    
    def test_skill_properties(self, notion_skill):
        """Test skill properties."""
        assert isinstance(notion_skill.description, str)
        assert isinstance(notion_skill.trigger_phrases, list)
        assert len(notion_skill.trigger_phrases) > 0
    
    @pytest.mark.skipif(not config.NOTION_API_KEY, reason="Notion not configured")
    def test_notion_client_exists(self, notion_skill):
        """Test that Notion client is initialized if configured."""
        if config.NOTION_API_KEY and config.NOTION_PARENT_PAGE_ID:
            assert notion_skill.notion is not None
    
    def test_execute_requires_action(self, notion_skill):
        """Test that execute requires action parameter."""
        result = notion_skill.execute({})
        assert "action" in result.lower() or "need" in result.lower()
    
    @pytest.mark.skipif(not config.NOTION_API_KEY, reason="Notion not configured")
    def test_create_checklist(self, notion_skill):
        """Test creating a checklist (integration test)."""
        if not notion_skill.notion:
            pytest.skip("Notion not configured")
        
        params = {
            "action": "create_page",
            "title": "pytest Checklist",
            "structure": "checklist",
            "items": ["Test item 1", "Test item 2"]
        }
        
        result = notion_skill.execute(params)
        
        # Should succeed
        assert "added" in result.lower() or "created" in result.lower()
        assert "2" in result  # 2 items
    
    @pytest.mark.skipif(not config.NOTION_API_KEY, reason="Notion not configured")
    def test_create_table(self, notion_skill):
        """Test creating a table (integration test)."""
        if not notion_skill.notion:
            pytest.skip("Notion not configured")
        
        params = {
            "action": "create_page",
            "title": "pytest Table",
            "structure": "table",
            "columns": ["Name", "Value", "Status"],
            "rows": []
        }
        
        result = notion_skill.execute(params)
        
        # Should succeed
        assert "created" in result.lower()
        assert "3 columns" in result.lower()
    
    def test_empty_checklist_error(self, notion_skill):
        """Test that empty checklist is rejected."""
        params = {
            "action": "create_page",
            "title": "Empty List",
            "structure": "checklist",
            "items": []
        }
        
        result = notion_skill.execute(params)
        assert "need" in result.lower() or "empty" in result.lower()


class TestNotionConfiguration:
    """Test Notion configuration."""
    
    def test_config_values_exist(self):
        """Test that Notion config values exist."""
        assert hasattr(config, 'NOTION_API_KEY')
        assert hasattr(config, 'NOTION_PARENT_PAGE_ID')
    
    def test_api_key_format(self):
        """Test API key format if configured."""
        if config.NOTION_API_KEY:
            # Check for secret_ or other common formats if applicable
            assert len(config.NOTION_API_KEY) > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
