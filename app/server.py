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

if __name__ == '__main__':

    with gr.Blocks(fill_height=True) as demo:
        model_selector = gr.Dropdown(models, label="Select Model", value="openai/gpt-4o-mini", scale=0)
        gr.ChatInterface(
            predict,
            type="messages",
            additional_inputs=[model_selector],
        )

    # for simplicity, force the port to be 7860
    demo.launch(server_name='0.0.0.0', server_port=7860)
