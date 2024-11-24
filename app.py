import time
import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

class ChromaChatBot:
    def __init__(self, model_name='all-MiniLM-L6-v2', chroma_dir='./chroma_data'):
        self.embedding_function = HuggingFaceEmbeddings(model_name=model_name)
        self.chroma_dir = chroma_dir
        self.vectorstore = None

    def load_vectorstore(self):
        """
        Load the Chroma vectorstore.
        """
        try:
            self.vectorstore = Chroma(
                persist_directory=self.chroma_dir,
                embedding_function=self.embedding_function,
                collection_name="documents_collection",
            )
        except Exception as e:
            st.error(f"Error loading Chroma vectorstore: {e}")
            raise RuntimeError(f"Error loading Chroma vectorstore: {e}")

    def search(self, query, top_k=2):
        """
        Search for relevant documents in the Chroma vectorstore based on the query.
        """
        if not self.vectorstore:
            self.load_vectorstore()
        try:
            results = self.vectorstore.similarity_search(query, k=top_k)
            return results
        except Exception as e:
            st.error(f"Error searching Chroma vectorstore: {e}")
            raise RuntimeError(f"Error searching Chroma vectorstore: {e}")

    def stream_results(self, query, top_k=2):
        """
        Stream search results dynamically.
        """
        results = self.search(query, top_k)

        if not results:
            yield "I'm sorry, I couldn't find any relevant information."
        else:
            for result in results:
                for letter in result.page_content:
                    yield letter
                    time.sleep(0.002)  # Simulate a typing delay


@st.cache_resource
def get_chatbot():
    chatbot = ChromaChatBot()
    try:
        chatbot.load_vectorstore()
    except RuntimeError as e:
        st.error(f"Failed to initialize chatbot: {e}")
    return chatbot


chatbot = get_chatbot()

st.image("logo.png", width=90)

# Title

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "👋 Hello, How can I assist you today?"}]

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"]):  
            st.write(msg["content"])
    else:
        st.chat_message(msg["role"]).write(msg["content"])

# User input
if prompt := st.chat_input("Type your question here..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        with st.chat_message("assistant"):  
            response = st.write_stream(chatbot.stream_results(prompt))
        
        st.session_state["messages"].append({"role": "assistant", "content": response})
    except RuntimeError as e:
        response = f"An error occurred: {e}"
        with st.chat_message("assistant"):  
            st.write(response)
        st.session_state["messages"].append({"role": "assistant", "content": response})
