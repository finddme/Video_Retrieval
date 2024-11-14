import re, sys
from threading import Thread
import weaviate
import json,os,random
import string
from tqdm import tqdm
from model.models import *

class_name_path="/".join(__file__.split("/")[:-1])+"/DB_class_name.txt"

import openai
from langchain_community.embeddings.openai import OpenAIEmbeddings

def get_embedding_openai(text, engine="text-embedding-3-large") : 
    Openai_API_KEY = ""
    os.environ["OPENAI_API_KEY"] =  Openai_API_KEY
    openai.api_key =os.getenv("OPENAI_API_KEY")

    # res = openai.Embedding.create(input=text,engine=engine)['data'][0]['embedding']
    from openai import OpenAI
    embedding_client = OpenAI()
    res= embedding_client.embeddings.create(input = text[:6000], model=engine).data[0].embedding
    return res

def load_weaviate_class_list():
    saved_class_list=[]
    with open(class_name_path, 'r') as ff:
        class_data=ff.readlines()
        for cd in class_data:
            saved_class_list.append({"class":cd.split("/////")[0],"file":cd.split("/////")[1].replace("\n","")})
    class_name_list=list(dict.fromkeys([cdl['class'] for cdl in saved_class_list]))
    file_name_list=list(dict.fromkeys([cdl['file'] for cdl in saved_class_list]))
    return saved_class_list,class_name_list, file_name_list

def save_weaviate(weaviate_client,
                    data_type,
                    data,
                    video_name,
                    embed_key_name,
                    main_class_name,
                    file_name_list):
    print("--- Save DB ---")

    class_name=f"{data_type}_{main_class_name}"

    class_obj = {
        "class": class_name,
        "vectorizer": "none",
    }
    
    if video_name not in file_name_list:
        temp_save=f"{class_name}/////{video_name}"

        with open(class_name_path, 'a') as ff:
            ff.write(f"{temp_save}\n")
        
    weaviate_client.schema.create_class(class_obj)

    for d in tqdm(data):
        embed = get_embedding_openai(d[embed_key_name])
        with weaviate_client.batch as batch:
            batch.add_data_object(data_object=d, class_name=class_name, vector=embed)

    print("--- vecotr DB store complete ---")
    
    return class_name

def del_weaviate_class(weaviate_client,file_name):
    saved_class_list, class_name_list, file_name_list=load_weaviate_class_list()
    del_class_name=[cdl['class'] for cdl in saved_class_list if cdl['file'] ==file_name]
    for dcn in del_class_name:
        print(f"--- delte db class {dcn} ---")
        client.schema.delete_class(dcn)

def db_class_sync_check(weaviate_client):
    global client
    print("--- Synchronizing vecotr DB ---")
    db_classes=list(map(lambda x : x["class"].lower(), weaviate_client.schema.get()["classes"]))
    _, class_name_list, _=load_weaviate_class_list()
    for dc in db_classes:
        if dc not in class_name_list:
            print(f"--- delte db class {dc} ---")
            weaviate_client.schema.delete_class(dc)

def get_all_data_in_specific_value(weaviate_client,
                                    class_name,
                                    return_values:list,
                                    path_value,
                                    valuestring):
    class_name=class_name.capitalize()
    try:
        result = (
            weaviate_client.query
            .get(class_name, return_values)
            .with_where({
                "path": [path_value],
                "operator": "Equal",
                "valueString": valuestring
            })
            .do()
        )
        
        if result and "data" in result and "Get" in result["data"]:
            objects = result["data"]["Get"][class_name]
            print(f"results: {len(objects)}")
            # for obj in objects:
            #     print(json.dumps(obj, indent=2, ensure_ascii=False))
            return objects
        else:
            print(f"no result abour {class_name} - {path_value} - {valuestring}")
            return []

    except Exception as e:
        print(f"Error: {str(e)}")
        return []