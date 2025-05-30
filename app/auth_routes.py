from fastapi import APIRouter, HTTPException, status, Response, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from app.auth import (
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user_from_session,
    refresh_token_if_needed,
    is_token_near_expiry
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

@auth_router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh access token if needed"""
    current_token = request.cookies.get("access_token")
    if not current_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token found"
        )

    # Check if token needs refresh (within 2 hours of expiry)
    new_token = refresh_token_if_needed(current_token, threshold_hours=2)

    if new_token:
        # Token was refreshed
        response_data = {"refreshed": True, "message": "Token refreshed successfully"}
        response_obj = JSONResponse(content=response_data)
        response_obj.set_cookie(
            key="access_token",
            value=new_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        return response_obj
    else:
        # No refresh needed or token invalid
        user = get_user_from_session(request)
        if user:
            return {"refreshed": False, "message": "Token refresh not needed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
