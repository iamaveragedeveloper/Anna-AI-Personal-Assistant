"""
End-to-end scenario tests.

Tests complete user workflows.
"""

import pytest
import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.voice import VoiceHandler
from core.llm import LLMHandler
from core.skill_loader import SkillLoader
import config


@pytest.fixture
def full_system():
    """Initialize complete Anna system components."""
    return {
        'voice': VoiceHandler(),
        'llm': LLMHandler(),
        'loader': SkillLoader()
    }


class TestShoppingListScenario:
    """Test shopping list creation scenario."""
    
    def test_shopping_list_flow(self, full_system):
        """Test: User creates shopping list."""
        llm = full_system['llm']
        loader = full_system['loader']
        
        # Get skills context
        skills_context = loader.get_skills_context()
        
        # User command
        user_input = "Add butter, milk, and sugar to my shopping list"
        
        # Get LLM response
        response = llm.get_response(
            user_input,
            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
        )
        
        # Parse skill request
        skill_request = llm.parse_skill_request(response)
        
        # Verify correct structure chosen
        assert skill_request is not None
        assert skill_request['skill'] == 'notion'
        assert skill_request['params']['structure'] == 'checklist'
        assert len(skill_request['params']['items']) == 3
        
        print(f"\n✅ Shopping list flow validated")
        print(f"   Items: {skill_request['params']['items']}")


class TestWorkoutTrackerScenario:
    """Test workout tracker creation scenario."""
    
    def test_workout_tracker_flow(self, full_system):
        """Test: User creates workout tracker."""
        llm = full_system['llm']
        loader = full_system['loader']
        llm.reset_conversation()
        
        skills_context = loader.get_skills_context()
        
        # User command (explicitly trigger table structure if needed)
        user_input = "Track my workouts with date, exercise, sets, and reps"
        
        # Get LLM response
        response = llm.get_response(
            user_input,
            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
        )
        print(f"\nRAW WORKOUT RESPONSE:\n{response}\n")
        
        # Parse skill request
        skill_request = llm.parse_skill_request(response)
        
        # Verify correct structure chosen
        assert skill_request is not None
        assert skill_request['skill'] == 'notion'
        assert skill_request['params']['structure'] == 'table'
        assert 'columns' in skill_request['params']
        
        # Should have date or exercise column
        columns = skill_request['params']['columns']
        assert any('date' in col.lower() or 'exercise' in col.lower() for col in columns)
        
        print(f"\n✅ Workout tracker flow validated")
        print(f"   Columns: {columns}")


class TestConversationalScenario:
    """Test conversational interactions."""
    
    def test_greeting_flow(self, full_system):
        """Test: User greets Anna."""
        llm = full_system['llm']
        llm.reset_conversation()
        
        # Greeting
        response = llm.get_response("Hello Anna")
        print(f"\nRAW GREETING RESPONSE:\n{response}\n")
        
        # Should be conversational (no skill)
        skill_request = llm.parse_skill_request(response)
        assert skill_request is None
        
        # Should respond with content
        assert len(response) > 5
        
        print(f"\n✅ Greeting flow validated")
        print(f"   Anna: {response.strip()}")
    
    def test_thanks_flow(self, full_system):
        """Test: User thanks Anna."""
        llm = full_system['llm']
        llm.reset_conversation()
        
        # Thanks
        response = llm.get_response("Thanks!")
        print(f"\nRAW THANKS RESPONSE:\n{response}\n")
        
        # Should be conversational
        skill_request = llm.parse_skill_request(response)
        assert skill_request is None
        
        print(f"\n✅ Thanks flow validated")
        print(f"   Anna: {response.strip()}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
