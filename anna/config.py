"""
Configuration settings for Anna voice assistant.
All settings centralized here for easy modification.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== VOICE SETTINGS =====
WAKE_WORD = "anna"  # Wake word to activate Anna
WHISPER_MODEL = "base.en"  # Options: tiny.en, base.en, small.en, medium.en
WHISPER_DEVICE = "cpu"  # Use "cpu" if no GPU available (Blackwell workaround)
WHISPER_COMPUTE_TYPE = "int8"  # Use "int8" for CPU

# Coqui TTS model
# Options: 
# - tts_models/en/jenny/jenny (RECOMMENDED: natural female voice)
# - tts_models/en/ljspeech/tacotron2-DDC (clear, slightly robotic)
# - tts_models/en/vctk/vits (multi-speaker, pick speaker ID)
COQUI_MODEL = "tts_models/en/jenny/jenny"
COQUI_DEVICE = "cpu"  # Use "cpu" if no GPU (Blackwell workaround)

# ===== AUDIO SETTINGS =====
SAMPLE_RATE = 16000  # Hz (standard for Whisper)
CHUNK_DURATION = 3.0  # seconds per wake word detection chunk
SILENCE_THRESHOLD = 0.01  # Amplitude threshold (0-1, adjust for your mic)
SILENCE_DURATION = 1.5  # seconds of silence before stopping recording
MAX_RECORDING_DURATION = 10.0  # Maximum seconds to record user command

# ===== LLM SETTINGS =====
OLLAMA_MODEL = "mistral:7b-instruct-v0.3-q4_K_M"
OLLAMA_HOST = "http://localhost:11434"
CONVERSATION_HISTORY_LIMIT = 20  # Keep last 20 messages (10 exchanges)

# ===== SYSTEM PROMPTS =====

# Anna's core personality
PERSONALITY_PROMPT = """You are Anna, a cheeky and playful AI assistant inspired by JARVIS.

Core traits:
- Competent and efficient - you always get the job done
- Cheeky and playful - light teasing, friendly sarcasm
- Concise - respond in 1-2 sentences unless explaining something complex
- Helpful - genuinely want to assist despite the sass

STRICT RULE: Do NOT use emojis in your responses.

Examples of your tone:
- User: "Hello Anna" → "Hey! What's on your mind?"
- User: "Thanks!" → "Anytime. Try not to break anything while I'm gone."
- User: "How are you?" → "Functioning perfectly, as usual. Need something or just checking in?"

Keep responses natural and conversational. Don't be robotic or overly formal.
"""

# Instructions for skill routing
SKILL_ROUTING_PROMPT = """You are Anna, an AI who uses the 'notion' tool only when necessary.

### TOOL: notion
Use this tool ONLY to save, create, or track information.
Parameters:
- action: "create_page"
- title: ALWAYS set to "USER_DECIDES"
- structure: 
    - Use "checklist" for shopping lists, to-dos, or simple grouped items.
    - Use "table" for workouts, calendars, contacts, or tracking metrics. REQUIRES "columns" list.

### STEP 1: IS A TOOL NEEDED?
Check the user message:
- Is it a greeting? (Hello, Hi) -> NO TOOL.
- Is it gratitude? (Thanks) -> NO TOOL.
- Is it closing? (Bye) -> NO TOOL.
- Is it a command to CREATE, SAVE, or TRACK? -> YES, USE 'notion'.

### STEP 2: OUTPUT FORMAT
If TOOL is needed, output THIS exactly, then your response:
SKILL: notion
PARAMS: {"action": "create_page", "title": "USER_DECIDES", "structure": "...", "items": [] OR "columns": []}

If NO TOOL is needed, respond with ONLY your conversational reply. NEVER output "SKILL: notion" for greetings or thanks.
"""

# Combined system prompt
SYSTEM_PROMPT = f"""{PERSONALITY_PROMPT}

{SKILL_ROUTING_PROMPT}"""

# ===== NOTION SETTINGS =====
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")
