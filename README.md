# WorkshopsAPI | Backend for summer team project

## About
[In process...]
Backend part for summer team project. FastAPI + PostgreSQL

## How to start
0. Python >= 3.13 && PostgreSQL >= 15
1. Clone project
```bash
git clone https://github.com/tomatoCoderq/workshops_api
cd workshops_api
```
2. Download uv (package manager as Poetry and pip)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh #Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Create venv 
```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
4. Install dependencies
```bash
uv pip install -e .
```

5. Create .env. Check out .example.env. for more details

6. Create directory logs in the root of the project

7. To finally start: 
```bash
uv run src/api/__main__.py
```