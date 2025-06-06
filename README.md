to start project 

clone
```bash
git clone https://github.com/tomatoCoderq/workshops_api
cd workshops_api
```

create venv
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

download uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

install dependencies
```bash
uv pip install -e .
```

