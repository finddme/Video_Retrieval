import re, sys
from threading import Thread
import weaviate
import json,os,random
import string
from tqdm import tqdm
from model.models import *
from typing import List, Dict

class_name_path="/".join(__file__.split("/")[:-1])+"/DB_class_name.json"

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
    with open(class_name_path) as f:
        saved_class_list = json.load(f)
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
        with open(class_name_path) as f:
            saved_info = json.load(f)
            saved_info.append({"class":class_name,"file":video_name})
        with open(class_name_path, 'w', encoding='utf-8') as outfile:
            json.dump(saved_info, outfile,indent="\t",ensure_ascii=False)

    classes=get_all_classes(weaviate_client)
    db_class_list=list(map(lambda x: x["class"], classes))
    if class_name.capitalize() not in db_class_list:
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

def get_all_classes(weaviate_client) -> List[Dict]:
    try:
        schema = weaviate_client.schema.get()
        
        classes = schema.get('classes', [])
        
        for idx, class_info in enumerate(classes, 1):
            class_name = class_info.get('class')
            description = class_info.get('description', 'No description')
            property_count = len(class_info.get('properties', []))
            
            # 속성 정보 출력 (optional)
            if property_count > 0:
                for prop in class_info.get('properties', []):
                    prop_name = prop.get('name')
                    prop_type = prop.get('dataType', [])
        
        return classes

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

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