from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import gradio as gr
from langchain.schema import AIMessage, HumanMessage
from utils.langchain_adapter import ChatOpenRouter
from app.model_list import models
from app.auth_routes import auth_router
from app.auth import get_user_from_session, refresh_token_if_needed, ACCESS_TOKEN_EXPIRE_MINUTES

def predict(message, history, model_name):

    chat_model = ChatOpenRouter(model_name=model_name)

    history_langchain_format = []
    for msg in history:
        if msg['role'] == "user":
            history_langchain_format.append(HumanMessage(content=msg['content']))
        elif msg['role'] == "assistant":
            history_langchain_format.append(AIMessage(content=msg['content']))

    history_langchain_format.append(HumanMessage(content=message))
    gpt_response = chat_model.invoke(history_langchain_format)

    return gpt_response.content

def cost_to_str(cost):
    return ('$' + '%6s' % str(cost)) if cost is not None else ' N/A '

def cost_to_template(cost_input, cost_output, cost_img):

    cost_input_str = cost_to_str(cost_input)
    cost_output_str = cost_to_str(cost_output)
    cost_img_str = cost_to_str(cost_img)

    template = '%s / M input tokens  ||  %s / M output tokens  ||  %s / K input imgs' % (
        cost_input_str, cost_output_str, cost_img_str
    )

    return template

def cost_fn(evt: gr.SelectData):

    global models

    model_name_input = evt.value
    cost_input, cost_output, cost_img = models[model_name_input]['cost']

    return cost_to_template(cost_input, cost_output, cost_img)


def create_protected_gradio_app():
    """Create the Gradio app with authentication wrapper"""
    model_choices = [(model_conf['display_name'], model_name) for model_name, model_conf in models.items()]
    model_name_default = 'openai/gpt-4o-mini'

    # Include token monitor script
    head_html = '<script src="/static/js/token-monitor.js"></script>'

    with gr.Blocks(title='Chatbot', fill_height=True, head=head_html) as demo:

        with gr.Row():

            with gr.Column(scale=4, min_width=300):
                model_selector = gr.Dropdown(model_choices, label="Select Model", value=model_name_default, scale=0)

            with gr.Column(scale=5, min_width=300):
                cost_display = gr.Textbox(info='Cost of model', value=cost_to_template(*models[model_name_default]['cost']), show_label=False)

        model_selector.select(cost_fn, inputs=None, outputs=cost_display)
        gr.ChatInterface(
            predict,
            type="messages",
            additional_inputs=[model_selector],
        )

        # Add logout button using simple link approach
        with gr.Row():
            gr.Button("🚪 Logout", link="/logout")

    return demo

if __name__ == '__main__':
    app = FastAPI()

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include authentication routes
    app.include_router(auth_router, prefix="/auth")

    # Simple logout endpoint for Gradio button
    @app.get("/logout")
    async def logout():
        # ideally this would better be POST request, but gradio is....
        response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key="access_token")  # Correct cookie name
        return response

    # Root redirect to login
    @app.get("/")
    async def root():
        return RedirectResponse(url="/auth/login")

    # Protected chatbot route
    @app.get("/chatbot")
    async def chatbot_redirect(request: Request):
        user = get_user_from_session(request)
        if not user:
            return RedirectResponse(url="/auth/login")
        # If authenticated, continue to gradio app
        return RedirectResponse(url="/chatbot/")

    # Create and mount the protected Gradio app
    demo = create_protected_gradio_app()

    # Custom middleware to check authentication and refresh tokens for gradio routes
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Check if the request is for the chatbot gradio app
        if request.url.path.startswith("/chatbot/"):
            current_token = request.cookies.get("access_token")
            if not current_token:
                return RedirectResponse(url="/auth/login")

            # Try to refresh token if needed (within 2 hours of expiry)
            new_token = refresh_token_if_needed(current_token, threshold_hours=2)

            # Verify user is still valid
            user = get_user_from_session(request)
            if not user:
                return RedirectResponse(url="/auth/login")

            # Continue with the request
            response = await call_next(request)

            # If token was refreshed, update the cookie in response
            if new_token:
                response.set_cookie(
                    key="access_token",
                    value=new_token,
                    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    httponly=True,
                    secure=False  # Set to True in production with HTTPS
                )

            return response

        response = await call_next(request)
        return response

    app = gr.mount_gradio_app(app, demo, path='/chatbot')

    # for simplicity, force the port to be 7860
    uvicorn.run(app, host='0.0.0.0', port=7860)
