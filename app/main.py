from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Compliance Backend",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================
# CORS CONFIGURATION — MUST BE FIRST MIDDLEWARE
# ============================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://stewartcomplianceai.com",
    "https://www.stewartcomplianceai.com",
    "https://api.stewartcomplianceai.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROUTER IMPORTS
# ============================================================

# Workflow engine routes
from app.api.routes.workflow_history import router as workflow_history_router
from app.api.routes.workflow_retry import router as workflow_retry_router
from app.api.routes.workflow_run import router as workflow_run_router
from app.api.routes.workflow_activity import router as workflow_activity_router
from app.api.routes.workflow_cancel import router as workflow_cancel_router
from app.api.routes.workflow_pause_resume import router as workflow_pause_resume_router
from app.api.routes.workflow_step_retry import router as workflow_step_retry_router
from app.api.routes.workflow_create import router as workflow_create_router

# Auth + admin dashboard
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.admin import router as admin_router

# User management
from app.api.routes.users import router as users_router

# Admin workflow management
from app.api.routes.workflows import router as workflows_router
from app.api.routes.analytics import router as analytics_router

# Audit logs
from app.api.routes.audit_logs import router as audit_logs_router

# Onboarding
from app.api.routes.onboarding import router as onboarding_router

# Uploads
from app.api.routes.upload import router as upload_router

# System maintenance agent
from app.api.routes.system_agent import router as system_agent_router

# Extraction pipeline
from app.api.routes.extraction import router as extraction_router

# Admin dashboard JSON API
from app.api.routes.admin_dashboard import router as admin_dashboard_router

# Public workflow API
from app.api.workflows_public import router as workflows_public_router

# ⭐ Local workflow router
from backend.routers.workflows import router as local_workflows_router

# ⭐ NEW — Business Promotion Agents Router
from app.api.routes.business_promotion import router as business_promotion_router

# ============================================================
# MODEL IMPORTS
# ============================================================

from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.db.models.onboarding import OnboardingSession
from app.db.models.onboarding_document import OnboardingDocument
from app.db.models.extracted_data import ExtractedData
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

from app.db.base import Base
from app.db.session import engine

def create_tables():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    create_tables()

# ============================================================
# HTTPS ENFORCEMENT
# ============================================================

if os.getenv("ENV", "development") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# ============================================================
# SECURITY HEADERS
# ============================================================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Resource not found"})

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# ============================================================
# ROUTES
# ============================================================

# Workflow engine routes
app.include_router(workflow_history_router)
app.include_router(workflow_retry_router)
app.include_router(workflow_run_router)
app.include_router(workflow_activity_router)
app.include_router(workflow_cancel_router)
app.include_router(workflow_pause_resume_router)
app.include_router(workflow_step_retry_router)
app.include_router(workflow_create_router)

# Auth + admin dashboard
app.include_router(auth_router, prefix="/auth")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(admin_router, prefix="/admin")

# User management
app.include_router(users_router, prefix="/admin/users")

# Admin workflow management
app.include_router(workflows_router, prefix="/admin/workflows")
app.include_router(analytics_router, prefix="/admin/analytics")

# Audit logs
app.include_router(audit_logs_router, prefix="/audit_logs")

# Onboarding
app.include_router(onboarding_router)

# Uploads
app.include_router(upload_router, prefix="/upload")

# System maintenance agent
app.include_router(system_agent_router)

# Extraction pipeline
app.include_router(extraction_router)

# Admin dashboard JSON API
app.include_router(admin_dashboard_router)

# Public workflow API
app.include_router(workflows_public_router)

# Local workflows router
app.include_router(local_workflows_router)

# ⭐ NEW — Business Promotion Agents
app.include_router(business_promotion_router, prefix="/agent/business")

# ============================================================
# OPENAPI SECURITY SCHEME — JWT BEARER ONLY
# ============================================================

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AI Compliance Backend",
        version="1.0.0",
        description="API with JWT Bearer Authentication",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================================================
# HEALTH CHECK + VERSION
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "AI Compliance Backend Running"}
