# CCA AI Training — Podcast Player & Exam Prep

Interactive podcast player and quiz system for the **Claude Certified Architect (CCA)** exam.
16 audio episodes, 8 module quizzes, AI-generated remedial lessons, and a downloadable
knowledge-profile certificate that feeds directly into Claude for personalised further study.

## Quick Start

The player runs as a local HTML file — it needs a web server (not `file://`) for audio to work.

```powershell
# Clone the repo
git clone https://github.com/H1nokam1Kagura/CCA-AI-Training-.git
cd CCA-AI-Training-

# Start local server and open in browser
python -m http.server 8000
# Open http://localhost:8000
```

## What's Inside

| File | Purpose |
|------|---------|
| `index.html` | Podcast player — episodes, quizzes, certificate |
| `Lesson_01_*.mp3 … Lesson_16_*.mp3` | TTS-HD audio for all 16 episodes |
| `generate_podcasts_v2.py` | Episode content source (text, voice, speed) |

## Episode List

| # | Title | Tag |
|---|-------|-----|
| 01 | Why People Fail the CCA Exam | Foundations |
| 02 | Agentic Error Handling | Error Control |
| 03 | Two Critical Failure Modes | Error Control |
| 04 | MCP Manifest & RPC Enforcement | MCP Layer |
| 05 | Claude.md as Control Layer | Policy Layer |
| 06 | Claude.md vs Skill.md — Policy vs Behavior | Policy Layer |
| 07 | Hub-and-Spoke Architecture | Architecture |
| 08 | Three Failures in Slow Motion | Architecture |
| 09 | Goal Decomposition in the Hub | Architecture |
| 10 | Memory, Caching & State | State Mgmt |
| 11 | Managing the Context Window | Context Design |
| 12 | The Boundary Problem | Unstructured |
| 13 | Extraction Failure Taxonomy | Unstructured |
| 14 | Predicting Goals & Defining Elements | Unstructured |
| 15 | Designing Task Schemas | Unstructured |
| 16 | Validating Unstructured Outputs | Validation |

## Player Features

- Play/pause, skip ±5s, 0.75×–2× speed control
- Episode progress tracking (persists via localStorage)
- **8 module quizzes** — unlock after both episodes in a pair are played
- **AI remedial lessons** after each quiz (requires Anthropic API key via ⚙ settings)
- **Knowledge-profile certificate** after all 8 quizzes — downloadable HTML with a
  pre-built Claude prompt you can paste into Claude.ai or Claude Desktop for a
  personalised study plan targeting your exact gaps

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| ← → | Skip ±5s |
| ↑ ↓ | Previous / Next episode |
| J / L | Skip −15s / +30s |
| S | Cycle speed |
| ? | Show shortcut help |

## Regenerating Audio

If you modify episode content in `generate_podcasts_v2.py`, regenerate the MP3s:

```powershell
pip install openai
python generate_audio.py --ep 1 2 3    # specific episodes
python generate_audio.py               # all 16 (~$5.40 at tts-1-hd)
```

Requires `OPENAI_API_KEY` set as an environment variable or in a `.env` file.

## License

Apache 2.0
