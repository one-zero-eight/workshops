from pathlib import Path
import sys
import uvicorn
import os




# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     config.create_db_and_table()
#     yield

# app = FastAPI(
#     title="Task Management API",
#     description="API for managing tasks with FastAPI, SQLModel, and Pydantic",
#     version="0.1.0",
#     lifespan=lifespan
# )

# templates = Jinja2Templates(directory=".")


# app.include_router(workshops.router)
# app.include_router(users.router)


# @app.get("/", response_class=HTMLResponse)
# async def root(request: Request,
#                user: Annotated[Users, Depends(get_current_user)]):
#     if user.role == "admin":
#         return "cock"

#     if user.role == "user":
#         return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/upload")
# async def download(file: UploadFile = File(...)):
#     content = await file.read()
#     content_type = str(file.filename).split(".")[-1]

#     with open(f"handle.{content_type}", "wb") as f:
#         f.write(content)

#     return "hello"

# Change dir to project root (three levels up from this file)
os.chdir(Path(__file__).parents[2])
# Get arguments from command
args = sys.argv[1:]

uvicorn.main.main([
    "src.api.app:app",
    # "--host", "0.0.0.0",
    "--port", "8080",
    "--use-colors",
    "--reload",
])