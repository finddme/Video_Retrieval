import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import anthropic
from utils.config import *
import openai
from openai import OpenAI
from groq import Groq
import anthropic
from together import Together
import numpy as np
import random
import torch
import gc
import string
# from diffusers import DiffusionPipeline
from huggingface_hub import login
import io
from io import BytesIO
from utils.formats import *
import instructor
import json 
from tavily import TavilyClient
import cohere
import requests

class LLM_Definition:
    @staticmethod
    def openai_llm():
        global Openai_API_KEY
        llm = OpenAI(api_key=Openai_API_KEY)
        return llm

    @staticmethod 
    def groq_llm():
        global GROQ_API_KEY
        llm = Groq(api_key=GROQ_API_KEY)
        return llm

    @staticmethod
    def claude_llm():
        global Claude_API_KEY
        llm = anthropic.Anthropic(api_key=Claude_API_KEY)
        return llm

    @staticmethod
    def together_llm():
        global Together_API_KEY
        llm = Together(api_key=Together_API_KEY)
        return llm

def get_embedding_openai(text, engine="text-embedding-3-large") : 
    global Openai_API_KEY
    os.environ["OPENAI_API_KEY"] =  Openai_API_KEY
    openai.api_key =os.getenv("OPENAI_API_KEY")

    # res = openai.Embedding.create(input=text,engine=engine)['data'][0]['embedding']
    embedding_client = OpenAI()
    res= embedding_client.embeddings.create(input = text, model=engine).data[0].embedding
    return res

def cohere_engine():
    global coher_API_KEY
    co = cohere.Client(coher_API_KEY)
    return co

def tavily_engine(TAVILY_API_KEY=TAVILY_API_KEY):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    return tavily
