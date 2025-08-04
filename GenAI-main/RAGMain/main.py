from utils import bcolors
from apikeys import ApiAccess
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.indices.query.query_transform.base import (
    HyDEQueryTransform,
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.query_engine import TransformQueryEngine
from llama_index.llms.openai import OpenAI

import openai
import os.path
import logging
import sys
import nltk
nltk.download('stopwords')
nltk.download('punkt')


logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


llm = OpenAI(model="gpt-3.5-turbo")
openai.api_key = ApiAccess.OPEN_API_KEY
llm.api_key =   ApiAccess.OPEN_API_KEY

query_engine = None
retriever = None
def loadDocumentsToVectorStore():
    global query_engine
    global retriever
    global open_api_key
    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        StorageContext,
        load_index_from_storage,
    )

    # check if storage already exists
    PERSIST_DIR = "./storage"
    if not os.path.exists(os.path.join(PERSIST_DIR, "docstore.json")):
        # load the documents and create the index
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    retriever = index.as_retriever()

    query_engine = index.as_query_engine()
    #hyde = HyDEQueryTransform(include_original=True)
    #query_engine = TransformQueryEngine(query_engine, query_transform=hyde)


def generate_stepback_query(query):
    global llm
    global open_api_key
    context = f"""
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
    response_str=llm.complete(formatted_prompt)

    return response_str

def CheckForMatches(query_str):
    global retriever
    retrieved_nodes = retriever.retrieve(query_str)
    has_good_match = False
    if retrieved_nodes is not None:
        for node in retrieved_nodes:
            #print(node)
            if node.get_score() > 0.8:
                has_good_match = True
                break
    return has_good_match

def printSuccess(response):
    print(bcolors.OKGREEN + bcolors.BOLD + "Response: " + bcolors.ENDC + str(response))

def printFailure():
    print(bcolors.FAIL + "Not able to answer this question" + bcolors.ENDC)

def printStepBackQuery(query):
    print(bcolors.OKBLUE + bcolors.BOLD + "StepBack - Refined Query:" + bcolors.ENDC + str(query))

#load
loadDocumentsToVectorStore()
run = True
while run:
    query_str = input("Enter query (type quit to exit):")
    if query_str == "quit":
        run = False
        break
    has_good_match = CheckForMatches(query_str)

    if(has_good_match):
        response = query_engine.query(query_str)
        printSuccess(str(response))
    else:
        printFailure()
        response_str =  generate_stepback_query(query_str)
        printStepBackQuery(str(response_str))
        if(response_str is None or response_str == ''):
            continue
        else:
            response = query_engine.query(str(response_str))
            printSuccess(str(response))