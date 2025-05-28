from fastapi import APIRouter, HTTPException, status, Response, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from app.auth import (
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user_from_session
)

auth_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@auth_router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # Set cookie and redirect to chatbot
    response = RedirectResponse(url="/chatbot", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    return response



@auth_router.post("/logout")
async def logout():
    """Handle logout"""
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@auth_router.get("/check")
async def check_auth(request: Request):
    """Check if user is authenticated"""
    user = get_user_from_session(request)
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False}
