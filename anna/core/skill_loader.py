"""
Skill Loader for Anna - auto-discovers and manages skills.

Responsibilities:
- Scan skills/ directory for skill modules
- Import and instantiate skill classes
- Maintain skill registry
- Route skill execution requests
- Generate LLM context from available skills
"""

import importlib
import inspect
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add project root to sys.path to ensure modules can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from skills.base_skill import BaseSkill


class SkillLoader:
    """
    Auto-discovers and manages Anna's skills.
    
    Skills are Python files in the skills/ directory that:
    1. Follow naming pattern: *_skill.py
    2. Contain classes that inherit from BaseSkill
    3. Are not named base_skill.py (that's the abstract class)
    
    Usage:
        loader = SkillLoader()
        result = loader.execute_skill("notion", {"action": "create_page"})
        context = loader.get_skills_context()  # For LLM prompt
    """
    
    def __init__(self, skills_dir: str = None):
        """
        Initialize skill loader and load all available skills.
        
        Args:
            skills_dir: Directory containing skill modules
        """
        if skills_dir is None:
            # Default to the 'skills' folder in the project root
            self.skills_dir = Path(project_root) / "skills"
        else:
            self.skills_dir = Path(skills_dir)
            
        self.skills: Dict[str, BaseSkill] = {}
        
        # Load skills on initialization
        self.load_all_skills()
    
    def load_all_skills(self):
        """
        Scan skills directory and load all skill classes.
        
        Process:
        1. Find all *_skill.py files
        2. Import each module
        3. Find classes inheriting from BaseSkill
        4. Instantiate and register them
        """
        print("=" * 60)
        print("[INFO] Discovering skills...")
        print("=" * 60)
        
        if not self.skills_dir.exists():
            print(f"[WARN] Skills directory not found: {self.skills_dir}")
            print(f"   Creating directory...")
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Find all skill files (excluding base_skill.py)
        skill_files = [
            f for f in self.skills_dir.glob("*_skill.py")
            if f.stem != "base_skill"
        ]
        
        if not skill_files:
            print("[INFO] No skill files found in skills/")
            print("   Skills will be loaded when you add them")
            return
        
        loaded_count = 0
        
        for skill_file in skill_files:
            try:
                # Convert path to module name (e.g., skills/notion_skill.py -> skills.notion_skill)
                # We use the relative path from the project root
                module_name = f"skills.{skill_file.stem}"
                
                # Import the module
                if module_name in sys.modules:
                    # Reload if already imported (useful for development)
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)
                
                # Find all classes that inherit from BaseSkill
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip BaseSkill itself and non-BaseSkill classes
                    if obj == BaseSkill or not issubclass(obj, BaseSkill):
                        continue
                    
                    # Instantiate the skill
                    try:
                        skill_instance = obj()
                        skill_name = skill_instance.name
                        
                        # Register the skill
                        self.skills[skill_name] = skill_instance
                        
                        print(f"   [OK] Loaded: {skill_name} ({obj.__name__})")
                        loaded_count += 1
                        
                    except Exception as e:
                        print(f"   [WARN] Failed to instantiate {name}: {e}")
            
            except Exception as e:
                print(f"   [WARN] Failed to load {skill_file.name}: {e}")
        
        print("=" * 60)
        if loaded_count > 0:
            print(f"[READY] Loaded {loaded_count} skill(s)")
        else:
            print("[INFO] No skills loaded")
        print("=" * 60 + "\n")
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Get a skill by name.
        
        Args:
            skill_name: Name of the skill (case-insensitive)
        
        Returns:
            Skill instance or None if not found
        """
        return self.skills.get(skill_name.lower())
    
    def get_all_skills(self) -> List[BaseSkill]:
        """
        Get list of all loaded skills.
        
        Returns:
            List of skill instances
        """
        return list(self.skills.values())
    
    def get_skill_names(self) -> List[str]:
        """
        Get list of all skill names.
        
        Returns:
            List of skill names
        """
        return list(self.skills.keys())
    
    def get_skills_context(self) -> str:
        """
        Generate context string for LLM prompt with all available skills.
        
        This is used to tell the LLM what skills are available and how to use them.
        
        Returns:
            Formatted skills description for LLM prompt
        """
        if not self.skills:
            return "No skills currently loaded."
        
        contexts = [skill.get_context() for skill in self.skills.values()]
        
        header = f"Available skills ({len(self.skills)}):"
        full_context = header + "\n\n" + "\n\n".join(contexts)
        
        return full_context
    
    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> str:
        """
        Execute a skill by name with given parameters.
        
        Args:
            skill_name: Name of skill to execute (case-insensitive)
            params: Parameters for the skill
        
        Returns:
            Execution result message (success or error)
        """
        # Get the skill
        skill = self.get_skill(skill_name)
        
        if not skill:
            available = ", ".join(self.skills.keys())
            return f"Unknown skill: '{skill_name}'. Available skills: {available}"
        
        # Execute the skill
        try:
            print(f"🔧 Executing skill: {skill_name}")
            print(f"   Params: {params}")
            
            result = skill.execute(params)
            
            print(f"   [OK] Success: {result}")
            
            return result
            
        except Exception as e:
            error_msg = f"Skill execution failed: {str(e)}"
            print(f"   [ERROR] {error_msg}")
            
            return error_msg
    
    def reload_skills(self):
        """
        Reload all skills (useful during development).
        
        This clears the current registry and re-scans the skills directory.
        """
        print("\n🔄 Reloading skills...\n")
        self.skills.clear()
        self.load_all_skills()


# Standalone test function
def test_skill_system():
    """
    Test the skill system with a mock skill.
    This is the acceptance test for PRD 3.
    """
    print("\n" + "=" * 60)
    print("TESTING SKILL SYSTEM (PRD 3 ACCEPTANCE TEST)")
    print("=" * 60 + "\n")
    
    # Test 1: Create a mock skill dynamically
    print("--- Test 1: Mock Skill Creation ---")
    
    # Create mock skill file
    mock_skill_code = '''
from skills.base_skill import BaseSkill
from typing import Dict, Any, List

class MockSkill(BaseSkill):
    """A simple mock skill for testing."""
    
    @property
    def name(self) -> str:
        return "mock"
    
    @property
    def description(self) -> str:
        return "A test skill that echoes back parameters"
    
    @property
    def trigger_phrases(self) -> List[str]:
        return ["test", "mock", "echo"]
    
    def execute(self, params: Dict[str, Any]) -> str:
        message = params.get("message", "No message provided")
        return f"Mock skill received: {message}"
'''
    
    # Write mock skill to file
    mock_file = Path(project_root) / "skills" / "mock_skill.py"
    
    with open(mock_file, "w") as f:
        f.write(mock_skill_code)
    
    print("[OK] Created mock_skill.py")
    
    # Test 2: Load skills
    print("\n--- Test 2: Skill Loading ---")
    
    loader = SkillLoader()
    
    # Verify mock skill was loaded
    assert "mock" in loader.get_skill_names(), "Mock skill not loaded"
    print("[OK] Mock skill loaded successfully")
    
    # Test 3: Skill execution
    print("\n--- Test 3: Skill Execution ---")
    
    result = loader.execute_skill("mock", {"message": "Hello from test!"})
    
    assert "Hello from test!" in result, "Skill execution failed"
    print(f"[OK] Skill execution successful: {result}")
    
    # Test 4: Error handling
    print("\n--- Test 4: Error Handling ---")
    
    result = loader.execute_skill("nonexistent", {})
    assert "Unknown skill" in result, "Error handling failed"
    print(f"[OK] Error handling works: {result[:50]}...")
    
    # Test 5: Skills context generation
    print("\n--- Test 5: LLM Context Generation ---")
    
    context = loader.get_skills_context()
    
    assert "mock" in context, "Context doesn't include mock skill"
    assert "test skill" in context.lower(), "Context doesn't include description"
    
    print("[OK] Context generated successfully:")
    print("-" * 60)
    print(context)
    print("-" * 60)
    
    # Test 6: Skill reloading
    print("\n--- Test 6: Skill Reloading ---")
    
    # Modify mock skill
    modified_skill_code = mock_skill_code.replace(
        "Mock skill received",
        "Modified mock skill received"
    )
    
    with open(mock_file, "w") as f:
        f.write(modified_skill_code)
    
    loader.reload_skills()
    
    result = loader.execute_skill("mock", {"message": "Test reload"})
    assert "Modified" in result, "Skill reload failed"
    print(f"[OK] Skill reload successful: {result}")
    
    # Cleanup
    print("\n--- Cleanup ---")
    mock_file.unlink()
    print("[OK] Removed mock_skill.py")
    
    print("\n" + "=" * 60)
    print("[PASS] ALL SKILL SYSTEM TESTS PASSED")
    print("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    """
    Run tests:
    python core/skill_loader.py
    """
    test_skill_system()
