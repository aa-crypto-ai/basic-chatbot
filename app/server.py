import gradio as gr
from langchain.schema import AIMessage, HumanMessage
from utils.langchain_adapter import ChatOpenRouter

models = [
    ("OpenAI - ChatGPT 4o mini",    "openai/gpt-4o-mini"),
    ("Google Gemini 2.0 Flash Lite","google/gemini-2.0-flash-lite-001"),
    ("Claude Sonnet 3.7",           "anthropic/claude-3.7-sonnet"),
    ("Claude Sonnet 3.7 (thinking)","anthropic/claude-3.7-sonnet:thinking"),
    ("Llama 3.1 70B",               "meta-llama/llama-3.1-70b-instruct:free"),  # actually not free
]

def predict(model_name, message, history):

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

def respond(msg, chat_history, model_name):
    if not msg.strip():
        return "", chat_history
    bot_msg = predict(model_name, msg, chat_history)
    chat_history.append({"role": "user", "content": msg})
    chat_history.append({"role": "assistant", "content": bot_msg})
    return "", chat_history

if __name__ == '__main__':
    with gr.Blocks() as demo:
        model_selector = gr.Dropdown(models, label="Select Model", value="openai/gpt-4o-mini")
        chatbot = gr.Chatbot(type="messages")
        msg = gr.Textbox(label="Your Message", submit_btn=True)
        msg.submit(respond, [msg, chatbot, model_selector], [msg, chatbot])


    # for simplicity, force the port to be 7860
    demo.launch(server_name='0.0.0.0', server_port=7860)
