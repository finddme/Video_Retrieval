import json
import openai
from typing import List, Dict, Union
from .model_prep_stream import Model as Model_stream
from .model_prep import Model as Model_original
from utils.config import *
from utils.utils import json_available_check

class Completion(Model_original):
    def __init__(self, llm):
        super().__init__(Completion)
        self.llm = llm
        self.model=Model_original(self.llm)
        self.messages = []

    def __call__(self, message, system_prompt):
        self.messages.append({"role": "system", "content":system_prompt})
        self.messages.append({"role": "user", "content": message})
        
        response = self.execute()
        return response
        
    def execute(self):
        response=self.model.__completion__(self.messages)
        return response
    

class Completion_instructor(Model_original):
    def __init__(self, llm):
        super().__init__(Completion_instructor)
        self.llm = llm
        self.model=Model_original(self.llm)
        self.messages = []

    def __call__(self, message, system_prompt, output_format):
        self.output_format=output_format
        self.messages.append({"role": "system", "content":system_prompt})
        self.messages.append({"role": "user", "content": message})
        
        response = self.execute()
        return response
        
    def execute(self):
        response=json_available_check(self.model.__instructor__(self.messages,self.output_format))
        return response
    

class Completion_stream(Model_stream):
    def __init__(self, llm):
        super().__init__(Completion_stream)
        self.llm = llm
        self.model=Model_stream(self.llm)
        self.messages = []

    def __call__(self, message, system_prompt):
        self.messages.append({"role": "system", "content":system_prompt})
        self.messages.append({"role": "user", "content": message})
        
        for chunk in self.execute():
            yield chunk
        
    def execute(self):
        for chunk in self.model.__completion__(self.messages):
            yield chunk