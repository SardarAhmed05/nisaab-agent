from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import balance, transactions, chat, auth, user, analytics

app = FastAPI(
    title="Nisaab Agent API",
    description="AI-powered personal finance assistant",
    version="1.0"
)


# Frontend
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)


# API routes
app.include_router(
    balance.router,
    prefix="/api"
)

app.include_router(
    analytics.router,
    prefix="/api"
)

app.include_router(
    transactions.router,
    prefix="/api"
)

app.include_router(
    chat.router,
    prefix="/api"
)

app.include_router(
    auth.router,
    prefix="/api"
)


# Frontend routes
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat.html"
    )

@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )

app.include_router(
    user.router,
    prefix="/api"
)

@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html"
    )

