from typing_extensions import TypedDict
from typing import List
from pydantic import BaseModel, Field,model_serializer
from pydantic import TypeAdapter
from typing import List

class relevant_score_format(BaseModel):
    score:str

# class Output_format(BaseModel):
#     keywords: List[keyword]

class UserInput_query(BaseModel):
    user_input: str

class UserInput_url(BaseModel):
    youtube_url: str