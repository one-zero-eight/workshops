from pathlib import Path
import sys
import uvicorn
import os



# Change dir to project root (three levels up from this file)
os.chdir(Path(__file__).parents[2])
# Get arguments from command
args = sys.argv[1:]

if __name__ == "__main__":
    uvicorn.main.main([
        "src.api.app:app",
        # "--host", "0.0.0.0",
        "--port", "9000",
        "--use-colors",
        "--proxy-headers",
        "--forwarded-allow-ips=*",
        "--reload",
        *args
    ])
