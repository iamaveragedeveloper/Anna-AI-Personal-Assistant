"""
FastAPI WebSocket server for Anna GUI.

Bridges between web interface and Anna's voice/LLM system.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json
from pathlib import Path
from typing import Optional
import threading
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


class AnnaGUIServer:
    """
    Server that connects web GUI to Anna's core functionality.
    """
    
    def __init__(self):
        self.app = FastAPI(title="Anna GUI")
        self.websocket: Optional[WebSocket] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Initialize Anna components
        print("=" * 60)
        print("[INIT] Initializing Anna core...")
        print("=" * 60)
        self.voice = VoiceHandler()
        self.llm = LLMHandler()
        self.loader = SkillLoader()
        
        # Setup routes
        self._setup_routes()
        
        print("[READY] Anna GUI server ready!")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        # Serve static files (HTML, CSS, JS)
        static_path = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        @self.app.get("/")
        async def root():
            return FileResponse(str(static_path / "index.html"))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket(websocket)
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()
        self.websocket = websocket
        self._loop = asyncio.get_event_loop()
        
        print("[CONNECT] Browser client connected")
        
        try:
            # Start Anna's voice loop in background thread
            loop_thread = threading.Thread(target=self.anna_voice_loop, daemon=True)
            loop_thread.start()
            
            # Keep connection alive - receive any client messages
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Handle client messages if needed
                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    await websocket.send_json({"type": "ping"})
                    
        except WebSocketDisconnect:
            print("[DISCONNECT] Browser client disconnected")
            self.websocket = None
    
    def send_to_client_sync(self, message: dict):
        """Send message to web client (thread-safe, from sync context)."""
        if self.websocket and self._loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.websocket.send_json(message),
                    self._loop
                )
                future.result(timeout=5.0)
            except Exception as e:
                print(f"[WARN] Failed to send to client: {e}")
    
    def anna_voice_loop(self):
        """
        Main Anna voice loop (runs in background thread).
        Sends state updates to web client via WebSocket.
        """
        print("[MIC] Starting Anna voice loop...")
        
        while True:
            try:
                # Wait for wake word
                self.send_to_client_sync({"type": "idle"})
                
                if self.voice.listen_for_wake_word(timeout=30.0):
                    # Wake word detected - alert GUI
                    self.send_to_client_sync({"type": "wakeword_detected"})
                    
                    # Speak acknowledgment
                    ack = "Yes?"
                    self.send_to_client_sync({"type": "speaking", "text": ack})
                    self.voice.speak(ack)
                    
                    # Listen for command
                    self.send_to_client_sync({"type": "listening"})
                    user_input = self.voice.listen_until_silence()
                    
                    if user_input:
                        # Show transcript
                        self.send_to_client_sync({
                            "type": "listening",
                            "transcript": user_input
                        })
                        
                        # Processing
                        self.send_to_client_sync({"type": "processing"})
                        
                        # Get LLM response with skill routing
                        skills_context = self.loader.get_skills_context()
                        response = self.llm.get_response(
                            user_input,
                            system_prompt_override=f"{config.SYSTEM_PROMPT}\n\n{skills_context}"
                        )
                        
                        # Parse skill request
                        skill_request = self.llm.parse_skill_request(response)
                        
                        if skill_request:
                            # Execute skill
                            result = self.loader.execute_skill(
                                skill_request['skill'],
                                skill_request['params']
                            )
                            conversational = self.llm.extract_conversational_response(response)
                            speak_text = conversational if conversational else result
                            
                            self.send_to_client_sync({"type": "speaking", "text": speak_text})
                            self.voice.speak(speak_text)
                        else:
                            # Regular conversational response
                            self.send_to_client_sync({"type": "speaking", "text": response})
                            self.voice.speak(response)
                    
                    # Back to idle
                    self.send_to_client_sync({"type": "idle"})
                    
            except Exception as e:
                print(f"[ERROR] Error in voice loop: {e}")
                import traceback
                traceback.print_exc()


def create_server() -> AnnaGUIServer:
    """Create and return the GUI server instance."""
    return AnnaGUIServer()


def run_server():
    """Run the GUI server."""
    import uvicorn
    
    server = AnnaGUIServer()
    
    print("\n" + "=" * 60)
    print("[WEB] Anna GUI Server Starting")
    print("=" * 60)
    print("\n  Open browser to: http://localhost:8080")
    print("  Say 'Anna' to activate\n")
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
