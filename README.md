# Assistant (Desktop, Python)

## Prereqs
- Python 3.11+
- Windows for startup helper (Linux/macOS work fine without the helper)
- (Optional) TMDb API key

## Setup
```bash
git clone <this-repo>
cd my_desktop_assistant
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -U pip
pip install -e .
copy .env.example .env    # then edit values
