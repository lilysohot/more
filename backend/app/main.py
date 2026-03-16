from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, users, api_configs, analyses

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基于三维合一框架的公司分析系统",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["用户"])
app.include_router(api_configs.router, prefix=f"{settings.API_V1_STR}/api-configs", tags=["API配置"])
app.include_router(analyses.router, prefix=f"{settings.API_V1_STR}/analyses", tags=["分析"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


@app.on_event("startup")
async def startup_event():
    from app.database import init_db
    await init_db()
