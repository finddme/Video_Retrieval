import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from model.models import *
from typing import List
from langchain_core.prompts import ChatPromptTemplate
import weaviate
import openai
from utils.config import *
import json
import ast

class Retrieve:
    @staticmethod 
    def retrieve(weaviate_client,
                query,
                stt_calss_name,
                stt_embed_key,
                captioning_class_name,
                caption_embed_key):
        query_vector = get_embedding_openai(query)

        print("--- Retrieve STTs ---")
        stt_property_list = list(map(lambda x: x["name"], weaviate_client.schema.get(stt_calss_name)['properties']))
        stt_documents = weaviate_client.query.get(stt_calss_name, stt_property_list).with_hybrid(query, vector=query_vector).with_limit(3).do()


        print("--- Retrieve Captions ---")
        caption_property_list = list(map(lambda x: x["name"], weaviate_client.schema.get(captioning_class_name)['properties']))
        caption_documents = weaviate_client.query.get(captioning_class_name, caption_property_list).with_hybrid(query, vector=query_vector).with_limit(3).do()


        return stt_documents,caption_documents

    @staticmethod 
    def reranker_cohere(weaviate_client,
                        co,
                        query,
                        documents_co,
                        weaviate_class):
        # weaviate_class=weaviate_class.title()
        weaviate_class=weaviate_class.capitalize()

        if "Stt" in weaviate_class:
            print("--- RERANK Stts ---")
            documents=[r["text"] for r in documents_co["data"]["Get"][weaviate_class]]
            time_metas=[r["end"] for r in documents_co["data"]["Get"][weaviate_class]]
            urls=[r["url"] for r in documents_co["data"]["Get"][weaviate_class]]
            titles=[r["vid_title"] for r in documents_co["data"]["Get"][weaviate_class]]
            descriptions=[r["description"] for r in documents_co["data"]["Get"][weaviate_class]]
            documents=list(dict.fromkeys(documents))

            rerank_res = co.rerank(
                model="rerank-multilingual-v3.0",
                query=query,
                documents=documents, 
                top_n=4, 
            )
            
            final_result = []
            
            for idx,result in enumerate(rerank_res.results):
                final_result.append({"doc":documents[result.index],
                                "time":time_metas[result.index],
                                "url":urls[result.index],
                                "title":titles[result.index],
                                "description":descriptions[result.index],
                                })
                
            return final_result

        elif "Captioning" in weaviate_class:
            print("--- RERANK Captionings ---")
            documents=[r["caption"] for r in documents_co["data"]["Get"][weaviate_class]] 
            time_metas=[r["time"] for r in documents_co["data"]["Get"][weaviate_class]] 
            urls=[r["url"] for r in documents_co["data"]["Get"][weaviate_class]] 
            titles=[r["vid_title"] for r in documents_co["data"]["Get"][weaviate_class]] 
            descriptions=[r["description"] for r in documents_co["data"]["Get"][weaviate_class]] 
            documents=list(dict.fromkeys(documents))

            rerank_res = co.rerank(
                model="rerank-multilingual-v3.0",
                query=query,
                documents=documents, 
                top_n=4, 
            )
            
            final_result = []
            
            for idx,result in enumerate(rerank_res.results):
                final_result.append({"doc":documents[result.index],
                                "time":time_metas[result.index],
                                "url":urls[result.index],
                                "title":titles[result.index],
                                "description":descriptions[result.index],
                                })
                
            return final_result