"""
Unit tests for LLM Handler.

Tests LLM integration, conversation management, and skill parsing.
"""

import pytest
from core.llm import LLMHandler
import config


class TestLLMHandler:
    """Test suite for LLMHandler class."""
    
    @pytest.fixture
    def llm_handler(self):
        """Create LLM handler instance for testing."""
        return LLMHandler()
    
    def test_initialization(self, llm_handler):
        """Test that LLM handler initializes correctly."""
        assert llm_handler is not None
        assert llm_handler.client is not None
        assert llm_handler.conversation_history == []
    
    def test_simple_response(self, llm_handler):
        """Test getting a simple response."""
        response = llm_handler.get_response("Hello")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_conversation_history(self, llm_handler):
        """Test that conversation history is maintained."""
        llm_handler.get_response("My favorite color is blue")
        llm_handler.get_response("What's my favorite color?")
        
        # Should have 4 messages (2 user, 2 assistant)
        assert len(llm_handler.conversation_history) == 4
    
    def test_reset_conversation(self, llm_handler):
        """Test conversation history reset."""
        llm_handler.get_response("Test message")
        assert len(llm_handler.conversation_history) > 0
        
        llm_handler.reset_conversation()
        assert len(llm_handler.conversation_history) == 0
    
    def test_skill_parsing_valid(self, llm_handler):
        """Test parsing valid skill request."""
        response = """
SKILL: notion
PARAMS: {"action": "create_page", "title": "Test"}

I'll create that for you!
"""
        
        skill_request = llm_handler.parse_skill_request(response)
        
        assert skill_request is not None
        assert skill_request['skill'] == 'notion'
        assert 'action' in skill_request['params']
        assert skill_request['params']['action'] == 'create_page'
    
    def test_skill_parsing_no_skill(self, llm_handler):
        """Test parsing response without skill request."""
        # Clean response text
        response = "Just a regular conversational response."
        
        skill_request = llm_handler.parse_skill_request(response)
        
        assert skill_request is None
    
    def test_extract_conversational_response(self, llm_handler):
        """Test extracting conversational part from skill response."""
        response = """
SKILL: notion
PARAMS: {"action": "test"}

This is the conversational part.
"""
        
        conversational = llm_handler.extract_conversational_response(response)
        
        assert "SKILL" not in conversational
        assert "PARAMS" not in conversational
        assert "conversational" in conversational.lower()
    
    @pytest.mark.timeout(30) # Increased timeout for CPU LLM
    def test_response_latency(self, llm_handler):
        """Test that response latency is acceptable."""
        import time
        
        start = time.time()
        llm_handler.get_response("Hello")
        latency = time.time() - start
        
        # Should respond within reasonable time (Ollama on CPU might be slow)
        assert latency < 15.0, f"Response too slow: {latency:.2f}s"


class TestLLMConfiguration:
    """Test LLM configuration settings."""
    
    def test_config_values_exist(self):
        """Test that all required config values are set."""
        assert hasattr(config, 'OLLAMA_MODEL')
        assert hasattr(config, 'OLLAMA_HOST')
        assert hasattr(config, 'SYSTEM_PROMPT')
        assert hasattr(config, 'PERSONALITY_PROMPT')
    
    def test_system_prompt_includes_personality(self):
        """Test that system prompt includes personality."""
        assert "Anna" in config.SYSTEM_PROMPT
        assert "cheeky" in config.SYSTEM_PROMPT.lower() or "playful" in config.SYSTEM_PROMPT.lower()


def test_llm_module_imports():
    """Test that LLM module imports successfully."""
    from core import llm
    assert hasattr(llm, 'LLMHandler')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
