from flask import Flask, request, render_template
from utils import bcolors
from apikeys import ApiAccess
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
import os
import nltk

os.environ["OPENAI_API_KEY"] = ApiAccess.OPEN_API_KEY


nltk.download('stopwords')
nltk.download('punkt')

app = Flask(__name__)

# Globals for your chatbot
llm = OpenAI(model="gpt-3.5-turbo")
llm.api_key = ApiAccess.OPEN_API_KEY

query_engine = None
retriever = None

def loadDocumentsToVectorStore():
    global query_engine, retriever
    PERSIST_DIR = "./storage"
    if not os.path.exists(os.path.join(PERSIST_DIR, "docstore.json")):
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    retriever = index.as_retriever()
    query_engine = index.as_query_engine()

def generate_stepback_query(query):
    context = """
    #1
    You are an expert at world knowledge. Your task is to step back
    and paraphrase a question to a more generic step-back question, which
    is easier to answer. Here are a few examples
    #2
    "input": "Could the members of The Police perform lawful arrests?"
    "output": "what can the members of The Police do?"
    "input": "Jan Sindel’s was born in what country?"
    "output": "what is Jan Sindel’s personal history?"
    "input": "What are muscle strains"
    "output": "what are muscle strains related to Massage"
    """

    template_str = (
        "We have provided context information below. \n"
        "---------------------\n"
        "{context_str}"
        "\n---------------------\n"
        "Given this information, please rephrase the question: {question_str}\n"
    )
    prompt_template = PromptTemplate(template_str)
    formatted_prompt = prompt_template.format(context_str=context, question_str=query)
    response_str = llm.complete(formatted_prompt)
    return response_str

def check_for_matches(query_str):
    global retriever
    retrieved_nodes = retriever.retrieve(query_str)
    if retrieved_nodes:
        for node in retrieved_nodes:
            if node.get_score() > 0.8:
                return True
    return False

# Load data and index once on startup
loadDocumentsToVectorStore()

@app.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_query = request.form["query"]
        if user_query.lower() == "quit":
            return render_template("index.html", chat_log="Goodbye!")
        
        has_match = check_for_matches(user_query)
        if has_match:
            response = query_engine.query(user_query)
            chat_response = str(response)
        else:
            stepback_query = generate_stepback_query(user_query)
            if not stepback_query:
                chat_response = "Sorry, I could not understand your query."
            else:
                response = query_engine.query(stepback_query.text)
                chat_response = str(response)
        return render_template("index.html", chat_log=chat_response, user_query=user_query)

    # GET request: just show empty chat
    return render_template("index.html", chat_log="")

if __name__ == "__main__":
    app.run(debug=True)
