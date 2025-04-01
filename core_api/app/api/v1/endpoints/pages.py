# core_api/app/api/v1/endpoints/pages.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Assuming templates are in the 'templates' directory relative to the 'app' directory
# Adjust the path if your directory structure is different
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# --- Page Endpoints --- #

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serves the login page."""
    # Pass the request object to the template context
    # This is needed for features like CSRF tokens if used later
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Serves the main dashboard page.
    The JavaScript within the template will handle fetching user data.
    We might add a dependency here later to check for the token cookie/header
    before even rendering the page, as an extra layer of protection.
    """
    # TODO: Optionally add a dependency here that checks for a valid token
    # before rendering the page, redirecting if not found.
    # Example: def check_token_dependency(token: str = Cookie(None)):
    #              if not token: redirect('/login') ...

    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Roles Management Page --- #
@router.get("/roles", response_class=HTMLResponse)
async def roles_page(request: Request):
    """
    Serves the roles management page.
    Requires authentication (handled by JS for now, maybe add dependency later).
    """
    # TODO: Add dependency to check superuser status before rendering?
    return templates.TemplateResponse("roles.html", {"request": request})

# Add more page routes here if needed 