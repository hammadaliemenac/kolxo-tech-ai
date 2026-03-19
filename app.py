from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ai_generator import router as ai_generator_router
from routes.cluster_keywords import router as cluster_keywords_router
from routes.meta_tags import router as meta_tags_router
from routes.plagrism_checker import router as plagiarism_checker_router
from routes.privacy_policy_generator import router as privacy_policy_generator_router

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost/",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1/",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500"
]
# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <- allows all origins
    allow_credentials=True,
    allow_methods=["*"],   # <- allows all HTTP methods
    allow_headers=["*"],   # <- allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI on Ubuntu!"}


app.include_router(ai_generator_router)
app.include_router(cluster_keywords_router)
app.include_router(meta_tags_router)
app.include_router(plagiarism_checker_router)
app.include_router(privacy_policy_generator_router)