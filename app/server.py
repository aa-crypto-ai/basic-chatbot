import gradio as gr
from langchain.schema import AIMessage, HumanMessage
from utils.langchain_adapter import ChatOpenRouter

chat_model = ChatOpenRouter(model_name='meta-llama/llama-3.1-70b-instruct:free')  # actually not free
chat_model = ChatOpenRouter(model_name='anthropic/claude-3.7-sonnet')   # the most expensive one but the best one
chat_model = ChatOpenRouter(model_name='openai/gpt-4o-mini')


def predict(message, history):
    history_langchain_format = []
    for msg in history:
        if msg['role'] == "user":
            history_langchain_format.append(HumanMessage(content=msg['content']))
        elif msg['role'] == "assistant":
            history_langchain_format.append(AIMessage(content=msg['content']))
    history_langchain_format.append(HumanMessage(content=message))
    gpt_response = chat_model.invoke(history_langchain_format)
    return gpt_response.content

demo = gr.ChatInterface(
    predict,
    type="messages",
)

# for simplicity, force the port to be 7860
demo.launch(server_name='0.0.0.0', server_port=7860)
