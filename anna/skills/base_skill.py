"""
Base Skill class for Anna's skill system.

All skills must inherit from this class and implement:
- name: Unique identifier
- description: What the skill does (for LLM context)
- trigger_phrases: Keywords that suggest this skill
- execute(): The actual skill logic
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseSkill(ABC):
    """
    Abstract base class for all Anna skills.
    
    Skills are auto-discovered and loaded by SkillLoader.
    Each skill must implement all abstract methods.
    
    Example skill structure:
    
    ```python
    from skills.base_skill import BaseSkill
    
    class MySkill(BaseSkill):
        @property
        def name(self) -> str:
            return "my_skill"
        
        @property
        def description(self) -> str:
            return "Does something useful"
        
        @property
        def trigger_phrases(self) -> List[str]:
            return ["do thing", "perform action"]
        
        def execute(self, params: Dict[str, Any]) -> str:
            # Do the thing
            return "Success!"
    ```
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique skill identifier (lowercase, no spaces).
        
        Used by LLM to specify which skill to invoke.
        
        Example: "notion", "calendar", "file_manager"
        
        Returns:
            Unique skill name
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this skill does.
        
        Used by LLM to decide when to invoke this skill.
        Be specific about capabilities.
        
        Example: "Create and manage Notion pages, tables, and checklists. 
                  Can dynamically structure data based on context."
        
        Returns:
            Skill description
        """
        pass
    
    @property
    @abstractmethod
    def trigger_phrases(self) -> List[str]:
        """
        List of phrases/keywords that suggest this skill should be used.
        
        Used by LLM for context. Not exhaustive - LLM can infer usage
        from description alone, but these help.
        
        Example: ["add task", "create page", "save to notion", "update database"]
        
        Returns:
            List of trigger phrases
        """
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute the skill with given parameters.
        
        This is the main entry point called by SkillLoader when
        the LLM requests this skill.
        
        Args:
            params: Dictionary of parameters from LLM.
                   Structure depends on skill - validate appropriately.
        
        Returns:
            Success/failure message to be spoken to user.
            Should be conversational (e.g., "Added 3 items to your list")
        
        Raises:
            Can raise exceptions - they'll be caught and converted to
            friendly error messages by SkillLoader.
        """
        pass
    
    def validate_params(
        self, 
        params: Dict[str, Any], 
        required_keys: List[str]
    ) -> bool:
        """
        Helper method to validate required parameters exist.
        
        Args:
            params: Parameters dictionary from LLM
            required_keys: List of required parameter keys
        
        Returns:
            True if all required keys present, False otherwise
        
        Example:
            if not self.validate_params(params, ["title", "items"]):
                raise ValueError("Missing required parameters")
        """
        missing_keys = [key for key in required_keys if key not in params]
        
        if missing_keys:
            return False
        
        return True
    
    def get_context(self) -> str:
        """
        Generate context string for LLM prompt.
        
        This is automatically called by SkillLoader to build the
        system prompt that tells the LLM about available skills.
        
        Returns:
            Formatted skill description for LLM
        """
        triggers = ", ".join(self.trigger_phrases)
        
        return f"""
{self.name}:
  Description: {self.description}
  Trigger phrases: {triggers}
""".strip()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}: {self.name}>"
