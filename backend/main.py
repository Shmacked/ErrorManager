from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import error_logs, projects

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(error_logs.router)
app.include_router(projects.router)
