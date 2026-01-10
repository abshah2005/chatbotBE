from langchain_core.runnables.history import RunnableWithMessageHistory
from memory import get_session_history
from llm import llm 
from prompts import chat_prompt
base_chain = chat_prompt | llm

chatbot = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
