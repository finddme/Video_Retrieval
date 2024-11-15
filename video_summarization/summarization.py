import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from model.models import *
from model.prompt import *
from typing import List
from langchain_core.prompts import ChatPromptTemplate
import weaviate
import openai
from utils.config import *
import json
import ast
from db.db_management import get_all_data_in_specific_value

weaviate_client = weaviate.Client(waviate_url) 
co = cohere_engine()

class Summarization:
    @staticmethod 
    def summarization(weaviate_client,
                        vid_title,
                        description,
                        stt_calss_name,
                        captioning_class_name,
                        completion
                        ):
        path_value="vid_title"

        # stt summary
        ## load all stt db about this video
        stt_return_values=["vid_title", "text", "end"]
        stt_data=get_all_data_in_specific_value(weaviate_client,stt_calss_name,stt_return_values,path_value,vid_title)
        stt_data = sorted(stt_data, 
                            key=lambda x: float(x['time']) if x['time'] else float('inf'))
        stt_data="\n".join(list(map(lambda x: x["text"], stt_data)))[:4000]
        print("--- STT Summary start ---")
        stt_data=f"{description}\n{stt_data}"
        stt_prompt=stt_summary_prompt.format(stt_data)
        stt_summary=completion(stt_prompt,stt_summary_system_prompt)
        # with open("./stt_summary.txt", "w") as f: f.write(stt_summary)

        # caption summary
        ## load all caption db about this video
        caption_return_values=["vid_title", "caption", "time"]
        caption_data=get_all_data_in_specific_value(weaviate_client,captioning_class_name,caption_return_values,path_value,vid_title)
        caption_data = sorted(caption_data, 
                            key=lambda x: float(time_to_seconds(x['time'])) if x['time'] else float('inf'))
        caption_data="\n".join(list(map(lambda x: x["caption"], caption_data)))[:4000]
        print("--- Caption Summary start ---")
        caption_data=f"{description}\n{caption_data}"
        caption_prompt=caption_summary_prompt.format(caption_data)
        caption_summary=completion(caption_prompt,caption_summary_system_prompt)
        # with open("./caption_summary.txt", "w") as f: f.write(caption_summary)

        return stt_summary,caption_summary
