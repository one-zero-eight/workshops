from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config import settings

import uvicorn



# Change dir to project root (three levels up from this file)
os.chdir(Path(__file__).parents[2])
# Get arguments from command
args = sys.argv[1:]

if __name__ == "__main__":
    print(settings.is_prod)
    if settings.is_prod == "Prod":
        uvicorn.main.main([
            "src.api.app:app",
            "--host", "0.0.0.0",
            "--port", "9000",
            "--use-colors",
            "--proxy-headers",
            "--forwarded-allow-ips=*",
            "--reload",
            *args
        ])
    else:
        uvicorn.main.main([
            "src.api.app:app",
            "--port", "9000",
            "--use-colors",
            "--proxy-headers",
            "--forwarded-allow-ips=*",
            "--reload",
            *args
        ])

