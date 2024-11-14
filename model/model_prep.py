from .prompt import *
import re
import httpx
import json
from utils.config import *

class Model:
    def __init__(self,llm):
        global basic_functions
        global claude_functions
        global system_prompt
        self.llm=llm
        self.call_res=[]
        self.mode={"openai.OpenAI":self.openai_cpl,
                 "groq.Groq":self.groq_cpl,
                 "anthropic.Anthropic":self.claude_cpl,
                  "together.client.Together":self.together_cpl}
        model_type = str(type(self.llm))
        self.model_type = model_type[model_type.find("'")+1:model_type.rfind("'")]
        # print(f"--- {self.model_type} ---")
        # self.processing=Processing(self.model_type)
        
    def __completion__(self,messages):
        model=self.mode[self.model_type]
        normal_completion=model(messages=messages)
        return normal_completion

    def __funccall__(self,messages,functions):
        model=self.mode[self.model_type]
        response=model(messages,functions)
        self.processing=Processing(self.model_type)
        self.processing.postprocessing(messages,response)
        self.call_res=self.processing.call_res

    def __instructor__(self,messages,response_model):
        model=self.mode[self.model_type]
        structured_output=model(messages=messages,response_model=response_model)
        return structured_output

    def openai_cpl(self,messages,functions=None):
        if functions:
            tool_choice="required"
        else:tool_choice=None
        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=functions,
            tool_choice=tool_choice
            )
        response_message = response.choices[0].message
        if functions:
            return response_message
        else: return response_message.content
        
    def groq_cpl(self,messages,functions=None):
        response = self.llm.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            tools=functions,
            tool_choice="auto",)
        response_message = response.choices[0].message
        if functions:
            return response_message
        else: return response_message.content
        
    def claude_cpl(self,messages,functions=None):
        if functions:
            response = self.llm.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                tools=functions,
                messages=[messages[1]]
            )
        else:
            response = self.llm.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                # system=messages[0]["content"],
                messages=[messages[1]]
            )
        response_message=response.content
        if functions:
            return response_message
        else: return response_message[0].text

    def together_cpl(self,messages,functions=None,response_model=None):
        if response_model:
            response = self.llm.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                messages=messages,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                response_format={
                    "type": "json_object",
                    "schema": response_model.model_json_schema(),
                },
            )
        else:
            response = self.llm.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                messages=messages,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
            )
            
        response_message = response.choices[0].message
        if functions:
            return response_message
        else: return response_message.content