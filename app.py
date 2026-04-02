from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ai_generator import router as ai_generator_router
from routes.cluster_keywords import router as cluster_keywords_router
from routes.meta_tags import router as meta_tags_router
from routes.plagrism_checker import router as plagiarism_checker_router
from routes.privacy_policy_generator import router as privacy_policy_generator_router
from routes.agreement_contract import router as agreement_contract_router
from routes.remove_bg import router as remove_bg_router
from routes.seo_checker import router as seo_checker_router

app = FastAPI()
origins = ["*"
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
app.include_router(agreement_contract_router)
app.include_router(remove_bg_router)
app.include_router(seo_checker_router)