# Chat Application - הוראות התקנה והרצה
## Group_AN

---

## 🚀 Quick Start

```bash
cd ChatApp
python3 run.py
```
Open the URL shown in terminal. **Done!**

**Requirements:** Python 3.8+ and a browser. No pip packages needed.

---

## 💻 Running with an IDE

1. Open folder `ChatApp`
2. Run `run.py`
3. Copy URL from terminal → open in browser

---

## 👥 Multiple Users (Same Network)

| Who | What to do |
|-----|------------|
| Server | Run `python3 run.py`, share the URL shown |
| Clients | Open browser → go to that URL |

---

## 📁 File Structure

```
ChatApp/
├── run.py                     # ← Run this!
├── server/
│   ├── server.py              # TCP server
│   ├── http_handler.py        # Static files
│   ├── websocket_handler.py   # WebSocket (RFC 6455)
│   └── client_manager.py      # Client management
├── client/
│   ├── index.html             # Chat UI
│   ├── style.css              # Styling
│   └── script.js              # WebSocket client
└── docs/
```

---

## 💬 Using the Chat

1. Enter username
2. Enter server address (auto-filled)
3. Click "Connect"
4. Chat!

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Wait a few seconds, retry |
| Connection refused | Check server is running, firewall allows port 10000 |
| WebSocket failed | Use `ws://` not `wss://` |

---

## 🤖 AI-Assisted Development (AutoMates Framework)

This project was built using **AutoMates**, a self-built AI framework powered by Claude Code.

### Agent Roles

| Agent | Role |
|-------|------|
| **BrainStorm** | Creative exploration, "what if?" questions, approach options |
| **Planner** | Architecture design, blueprints, task breakdown |
| **Builder** | Code implementation |
| **Checker** | Quality assurance, code review, verification |

### Workflow

```
BrainStorm → Planner → Builder → Checker → (iterate if needed)
```

### Documentation

The `AI_Workflow/` folder contains the full development history:
- `1.BRAINSTORM_ChatApp.md` - Initial ideas exploration
- `2.BLUEPRINT.md` - Architecture plan
- `3-7.` - Task distribution, reviews, fixes
- `Status.md` - Project status tracker

Each session with AI agents is documented for transparency and learning.

---

## 🔧 Technical Details

| | |
|---|---|
| Protocol | TCP + WebSocket (RFC 6455) |
| Concurrency | Threading |
| Port | 10000 |

---

## 📚 Libraries Used (Built-in Only)

```python
import socket      # TCP networking
import threading   # Multi-client handling
import hashlib     # SHA1 for WebSocket handshake
import base64      # Base64 encoding
import struct      # Binary frame parsing
import os          # File path handling
```

**No pip packages required!**
