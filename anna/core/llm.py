"""
LLM Handler for Anna - manages conversation with Mistral via Ollama.

This module handles:
- Communication with Ollama (Mistral 7B)
- Conversation history management
- Personality injection via system prompts
- Parsing skill execution requests from LLM output
"""

import ollama
import json
import re
import os
import sys
from typing import Dict, Any, Optional, List

# Add the parent directory to sys.path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class LLMHandler:
    """
    Handles LLM interactions for Anna using Mistral 7B via Ollama.
    
    Responsibilities:
    - Maintain conversation history
    - Inject personality via system prompts
    - Parse structured skill requests from responses
    - Provide text-based conversation interface
    """
    
    def __init__(self):
        """Initialize LLM handler and verify Ollama connection."""
        print("=" * 60)
        print("[INIT] Initializing LLM Handler...")
        print("=" * 60)
        
        self.client = ollama.Client(host=config.OLLAMA_HOST)
        self.conversation_history: List[Dict[str, str]] = []
        
        # Verify Ollama is running and model is available
        self._verify_ollama()
        
        print("\n" + "=" * 60)
        print("[READY] LLM Handler ready!")
        print("=" * 60 + "\n")
    
    def _verify_ollama(self):
        """Verify Ollama is running and model is available."""
        try:
            # Check if Ollama is running
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            print(f"\n[INFO] Available models: {len(model_names)}")
            
            # Check if our model is available
            model_found = any(config.OLLAMA_MODEL in name for name in model_names)
            
            if not model_found:
                print(f"\n[WARN] Model '{config.OLLAMA_MODEL}' not found!")
                print(f"   Available models: {model_names}")
                print(f"\n   [LOAD] Pulling model now (this may take a few minutes)...")
                
                self.client.pull(config.OLLAMA_MODEL)
                print(f"   [OK] Model downloaded!")
            else:
                print(f"   [OK] Model '{config.OLLAMA_MODEL}' ready")
                
        except Exception as e:
            print(f"\n[ERROR] Failed to connect to Ollama: {e}")
            print(f"   Make sure Ollama is running: ollama serve")
            raise
    
    def get_response(
        self, 
        user_input: str, 
        system_prompt_override: Optional[str] = None,
        inject_skills: bool = False
    ) -> str:
        """
        Get LLM response for user input.
        
        Args:
            user_input: User's message
            system_prompt_override: Optional override for system prompt
                                   (useful for testing or specialized contexts)
        
        Returns:
            Anna's response text
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Trim history if too long (keep last N messages)
        if len(self.conversation_history) > config.CONVERSATION_HISTORY_LIMIT:
            # Keep only recent messages, but preserve important context
            self.conversation_history = self.conversation_history[-config.CONVERSATION_HISTORY_LIMIT:]
        
        # Build messages for API
        if system_prompt_override:
            system_prompt = system_prompt_override
        elif inject_skills:
            system_prompt = config.SYSTEM_PROMPT
        else:
            # Pure conversational mode: personality only, no skill routing
            system_prompt = config.PERSONALITY_PROMPT
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]
        
        try:
            # Call Ollama
            response = self.client.chat(
                model=config.OLLAMA_MODEL,
                messages=messages,
                options={
                    "temperature": 0.7,  # Balance creativity and consistency
                    "top_p": 0.9,
                    "num_predict": 500,  # Max tokens (keep responses concise)
                }
            )
            
            # Extract response text
            assistant_message = response['message']['content']
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"Oops, my circuits are a bit fried. Error: {str(e)}"
            print(f"[ERROR] LLM Error: {e}")
            
            # Add error to history to maintain context
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            
            return error_msg
    
    def parse_skill_request(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response for skill execution requests.
        
        Expected format:
        SKILL: skill_name
        PARAMS: {"key": "value"}
        
        Args:
            response: LLM response text
        
        Returns:
            Dict with 'skill' and 'params' keys, or None if no skill request
        """
        # Look for SKILL: pattern
        skill_match = re.search(r'SKILL:\s*(\w+)', response, re.IGNORECASE)
        
        if not skill_match:
            return None
        
        skill_name = skill_match.group(1).lower()
        
        # Look for PARAMS: pattern (handle multiline JSON)
        params_match = re.search(
            r'PARAMS:\s*(\{.*?\})',
            response,
            re.IGNORECASE | re.DOTALL
        )
        
        if not params_match:
            print(f"[WARN] Found SKILL but no PARAMS in response")
            return None
        
        try:
            # Parse JSON params
            params_str = params_match.group(1)
            params = json.loads(params_str)
            
            return {
                "skill": skill_name,
                "params": params
            }
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse PARAMS JSON: {e}")
            print(f"   Raw params: {params_match.group(1)}")
            return None
    
    def extract_conversational_response(self, response: str) -> str:
        """
        Extract the conversational part of response (after SKILL/PARAMS block).
        
        Args:
            response: Full LLM response
        
        Returns:
            Just the conversational text, without SKILL/PARAMS
        """
        # Remove SKILL and PARAMS lines
        cleaned = re.sub(
            r'SKILL:.*?$',
            '',
            response,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        cleaned = re.sub(
            r'PARAMS:.*?\}',
            '',
            cleaned,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        # Clean up whitespace
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else response
    
    def reset_conversation(self):
        """Clear conversation history (useful for testing or fresh starts)."""
        self.conversation_history = []
        print("[INFO] Conversation history cleared")
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.
        
        Returns:
            Formatted string with conversation history
        """
        if not self.conversation_history:
            return "No conversation history yet."
        
        summary = []
        for i, msg in enumerate(self.conversation_history):
            role = "User" if msg["role"] == "user" else "Anna"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary.append(f"{i+1}. {role}: {content}")
        
        return "\n".join(summary)


# Standalone test function
def test_llm_handler():
    """
    Test LLM handler with text-based conversation.
    This is the acceptance test for PRD 2.
    """
    print("\n" + "=" * 60)
    print("TESTING LLM HANDLER (PRD 2 ACCEPTANCE TEST)")
    print("=" * 60 + "\n")
    
    # Initialize handler
    llm = LLMHandler()
    
    # Test 1: Basic personality
    print("\n--- Test 1: Personality ---")
    print("Testing Anna's personality and tone...")
    
    test_inputs = [
        "Hello Anna",
        "How are you?",
        "Thanks for helping!"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = llm.get_response(user_input)
        print(f"Anna: {response}")
    
    # Test 2: Skill routing
    print("\n\n--- Test 2: Skill Routing ---")
    print("Testing skill detection and JSON parsing...")
    
    llm.reset_conversation()  # Fresh start
    
    user_input = "Add butter, milk, and sugar to my shopping list"
    print(f"\nUser: {user_input}")
    
    response = llm.get_response(user_input)
    print(f"\nAnna (full response):\n{response}")
    
    # Parse skill request
    skill_request = llm.parse_skill_request(response)
    
    if skill_request:
        print(f"\n[OK] Skill detected: {skill_request['skill']}")
        print(f"   Params: {json.dumps(skill_request['params'], indent=2)}")
        
        # Extract conversational part
        conversational = llm.extract_conversational_response(response)
        print(f"   Conversational response: {conversational}")
    else:
        print("[FAIL] No skill detected in response")
    
    # Test 3: Conversation memory
    print("\n\n--- Test 3: Conversation Memory ---")
    print("Testing context retention...")
    
    llm.reset_conversation()
    
    # First message
    print("\nUser: My favorite color is blue")
    response1 = llm.get_response("My favorite color is blue")
    print(f"Anna: {response1}")
    
    # Follow-up (should remember)
    print("\nUser: What's my favorite color?")
    response2 = llm.get_response("What's my favorite color?")
    print(f"Anna: {response2}")
    
    if "blue" in response2.lower():
        print("[PASS] Anna remembered the context!")
    else:
        print("[FAIL] Anna didn't retain context")
    
    # Test 4: Structured output variations
    print("\n\n--- Test 4: Different Task Types ---")
    print("Testing Anna's structure decisions...")
    
    llm.reset_conversation()
    
    test_tasks = [
        "Remind me about the meeting tomorrow at 3pm",
        "Track my workouts this week",
        "Create a contact list with name, email, and phone"
    ]
    
    for task in test_tasks:
        print(f"\nUser: {task}")
        response = llm.get_response(task)
        
        skill_request = llm.parse_skill_request(response)
        if skill_request:
            structure = skill_request['params'].get('structure', 'unknown')
            print(f"   Structure chosen: {structure}")
        else:
            print(f"   Conversational: {response[:100]}...")
    
    # Print conversation summary
    print("\n\n--- Conversation Summary ---")
    print(llm.get_conversation_summary())
    
    print("\n" + "=" * 60)
    print("[PASS] LLM HANDLER TESTS COMPLETE")
    print("=" * 60 + "\n")
    
    return True


def interactive_mode():
    """
    Interactive chat mode for manual testing.
    Run with: python core/llm.py --interactive
    """
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE - Chat with Anna")
    print("=" * 60)
    print("Type 'quit' to exit, 'reset' to clear history\n")
    
    llm = LLMHandler()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                llm.reset_conversation()
                continue
            
            # Get response
            response = llm.get_response(user_input)
            
            # Check for skill request
            skill_request = llm.parse_skill_request(response)
            
            if skill_request:
                print(f"\n🔧 [SKILL DETECTED]")
                print(f"   Skill: {skill_request['skill']}")
                print(f"   Params: {json.dumps(skill_request['params'], indent=6)}")
                print()
                
                # Show conversational part
                conversational = llm.extract_conversational_response(response)
                if conversational:
                    print(f"Anna: {conversational}\n")
            else:
                print(f"Anna: {response}\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] Error: {e}\n")


if __name__ == "__main__":
    """
    Run tests or interactive mode:
    
    python core/llm.py              # Run tests
    python core/llm.py --interactive  # Interactive chat
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        test_llm_handler()
