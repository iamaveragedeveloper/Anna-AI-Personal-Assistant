"""
Integration tests for Anna.

Tests component interactions and data flow.
"""

import pytest
import os
import sys

# Add project root to sys.path to ensure modules can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.llm import LLMHandler
from core.skill_loader import SkillLoader
import config


class TestLLMSkillIntegration:
    """Test LLM and skill system integration."""
    
    @pytest.fixture
    def llm(self):
        """Create LLM handler."""
        return LLMHandler()
    
    @pytest.fixture
    def loader(self):
        """Create skill loader."""
        return SkillLoader()
    
    def test_llm_sees_skills(self, llm, loader):
        """Test that LLM can see available skills."""
        skills_context = loader.get_skills_context()
        
        # Skills context should include notion skill
        if "notion" in loader.get_skill_names():
            assert "notion" in skills_context.lower()
    
    def test_llm_generates_skill_request(self, llm, loader):
        """Test that LLM generates valid skill requests."""
        skills_context = loader.get_skills_context()
        
        # User input that should trigger notion skill
        user_input = "Add milk and bread to my shopping list"
        
        # System prompt override with skills context
        response = llm.get_response(
            user_input,
            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
        )
        
        # Parse skill request
        skill_request = llm.parse_skill_request(response)
        
        # Should detect skill request (assuming LLM is smart enough)
        assert skill_request is not None
        assert skill_request['skill'] == 'notion'
        assert 'action' in skill_request['params']
    
    def test_skill_execution_from_llm(self, llm, loader):
        """Test executing skill from LLM output."""
        skills_context = loader.get_skills_context()
        
        # Get LLM response for a command
        user_input = "Create a checklist of eggs and butter"
        
        response = llm.get_response(
            user_input,
            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
        )
        
        # Parse and execute if skill detected
        skill_request = llm.parse_skill_request(response)
        
        if skill_request:
            result = loader.execute_skill(
                skill_request['skill'],
                skill_request['params']
            )
            
            # Should get a result string
            assert isinstance(result, str)
            assert len(result) > 0


class TestEndToEndFlow:
    """Test complete flow without voice."""
    
    @pytest.fixture
    def components(self):
        """Create all components."""
        return {
            'llm': LLMHandler(),
            'loader': SkillLoader()
        }
    
    def test_complete_flow_without_voice(self, components):
        """Test complete flow (LLM → Skill routing)."""
        llm = components['llm']
        loader = components['loader']
        
        # Get skills context
        skills_context = loader.get_skills_context()
        
        # User input
        user_input = "Add butter to my shopping list"
        
        # Get LLM response
        response = llm.get_response(
            user_input,
            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
        )
        
        # Parse skill request
        skill_request = llm.parse_skill_request(response)
        
        # Verify flow
        assert skill_request is not None, "LLM should generate skill request"
        assert skill_request['skill'] in loader.get_skill_names(), "Skill should exist"
        
        # Extract conversational response
        conversational = llm.extract_conversational_response(response)
        assert len(conversational) > 0, "Should have conversational response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
