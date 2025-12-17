# JARVIS - Advanced Local AI Consultant

## 🚀 Project Vision
JARVIS is an **autonomous, voice-activated AI consultant** specialized in computer hardware. Unlike standard assistants that simply fetch facts, JARVIS aims for **Level 3 Intelligence (Advisory)**: it doesn't just tell you *what* a component is, it analyzes data to tell you *if it's right for you*.

Built effectively for **Local Execution**, it demonstrates the power of Edge AI by running LLMs, Speech Recognition, and Databases entirely on the user's machine, ensuring maximum privacy and zero latency.

## 🎯 Project Deliverables

### 1. The "Hardware Expert" Core (Level 3 Intelligence)
*Goal: Move from Fact Retrieval to Rational Advisory.*
- **Deep Specification Database**: 
    - Ingest detailed specs (VRAM, TDP, Clock Speeds, Release Date) beyond simple PassMark scores.
    - *Status*: Basic Benchmarks implemented (SQLite). Needs expansion.
- **Review Analysis (RAG)**:
    - Capability to search the web for recent reviews (e.g., TechPowerUp, Tom's Hardware).
    - Synthesize pros/cons to answer: "Is the RTX 4090 worth it over the 4080 for 1440p gaming?"
- **Recommendation Engine**:
    - Logic to weigh Price vs. Performance vs. User Needs (e.g., "For video editing, prefer more VRAM").

### 2. Natural Voice Interface
*Goal: Seamless, hands-free interaction.*
- **Wake Word Detection**:
    - "Hey Jarvis" passive listening using lightweight models (e.g., openWakeWord or Porcupine) to trigger the active agent.
- **Advanced Speech Stack**:
    - **Ears**: Faster Whisper (Local) for human-level accuracy on technical terms.
    - **Voice**: Edge TTS for natural, non-robotic responses.

### 3. Local-First Architecture
*Goal: Portfolio-ready engineering.*
- **Privacy & Speed**: All processing (STT, LLM, TTS) happens locally.
- **Modular Design**: Clean separation of clean code principles (Adapters, Services, Domain).
- **Recruiter Ready**: 
    - **Dockerized Deployment**: Simple `docker-compose up` to replicate the environment.
    - **Architecture Documentation**: Clear diagrams of how the LLM Router, Tools, and Database interact.

## 🛠️ Technical Stack
| Component | Technology | Reasoning |
|-----------|------------|-----------|
| **LLM** | **Llama 3.1 (8B)** via Ollama | Powerful reasoning, runs locally on consumer GPU. |
| **STT** | **Faster Whisper** | Best-in-class accuracy for technical jargon. |
| **TTS** | **Edge TTS** | High-quality neural voices without API costs. |
| **Database** | **SQLite** | Fast, relational storage for structured hardware specs. |
| **Search** | **DuckDuckGo + BS4** | Real-time web access/scraping for reviews. |
| **Wake Word** | *(Planned: openWakeWord)* | Low-latency trigger. |

## 🗺️ Roadmap

### Phase 1: Foundation (✅ Completed)
- [x] Integrate Local LLM (Ollama).
- [x] Implement robust Voice I/O (Whisper + Edge TTS).
- [x] Basic Tool Use (Routing questions to DB vs. Web).
- [x] Ingest basic PassMark benchmarks.

### Phase 2: The Expert (🚧 In Progress)
- [ ] **Data Expansion**: Scrape and ingest detailed GPU/CPU specs (TDP, VRAM, etc.).
- [ ] **Review Intelligence**: create a "Research" tool that reads top search results and summarizes sentiments.
- [ ] **Context Awareness**: Allow the assistant to remember "I have a $500 budget" across turns.

### Phase 3: Autonomy & Polish
- [ ] **Wake Word**: Implement "Hey Jarvis".
- [ ] **Dockerization**: Create a container for easy setup.
- [ ] **Demo Video**: Record a high-quality showcase for the portfolio.

## Setup & usage
```bash
git clone <this-repo>
cd JARVIS
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
# Ensure Ollama is running with llama3.1
assistant listen
```
