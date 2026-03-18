# Anna GUI

Beautiful web-based interface for Anna with animated blue circle.

## Features

- **Animated Blue Circle** — Represents Anna's presence  
- **Particle Field Background** — Subtle ambient atmosphere  
- **State Visualization**:  
  - `idle` → Gentle breathing pulse  
  - `active` → Strong pulse + ripple when wake word detected  
  - `listening` → Audio-reactive pulsing  
  - `speaking` → Expressive emotional animation  
- **Live Transcription** — See what you say and what Anna responds  
- **Auto-Reconnect** — Handles dropped WebSocket gracefully  
- **Responsive** — Works on desktop and mobile browsers  

## Start GUI Mode

```bash
cd anna
python main_gui.py
```

Then open your browser to: **http://localhost:8080**

## Architecture

```
Browser (localhost:8080)
    ↕  WebSocket /ws
FastAPI Server  (gui/server.py)
    ├─ VoiceHandler   (core/voice.py)
    ├─ LLMHandler     (core/llm.py)
    └─ SkillLoader    (core/skill_loader.py)
```

## File Structure

```
gui/
├── __init__.py
├── server.py              # FastAPI + WebSocket server
├── static/
│   ├── index.html         # Main page
│   ├── style.css          # Premium dark theme
│   └── animation.js       # Circle + particle animations
└── README.md              # This file
```

## Customization

### Change Circle Color

Edit `static/animation.js`:
```javascript
this.palette = {
    idle:      { h: 214, s: 85, l: 55 },   // Soft blue
    active:    { h: 207, s: 100, l: 60 },  // Bright blue
    listening: { h: 190, s: 100, l: 58 },  // Cyan
    speaking:  { h: 205, s: 100, l: 62 },  // Bright blue
};
```

### Change Circle Size

Edit `static/animation.js`:
```javascript
this.baseRadius = Math.min(window.innerWidth, window.innerHeight) * 0.1;
```

### Change Port

Edit `gui/server.py`:
```python
uvicorn.run(server.app, host="0.0.0.0", port=8081)
```

## Troubleshooting

| Issue | Fix |
|---|---|
| Port in use | Change port in `server.py` |
| Circle not visible | Press F12 → Console for JS errors |
| WebSocket won't connect | Check firewall, try different port |
| Animation laggy | Update GPU drivers; circle uses Canvas 2D |
