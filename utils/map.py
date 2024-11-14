from model.prompt import *
from model.models import LLM_Definition

llm_df = LLM_Definition()

# fc_mode={"openai.OpenAI":[basic_function_list,basic_toolprompt],
#                 "groq.Groq":[basic_function_list,llama_toolprompt],
#                 "anthropic.Anthropic":[claude_function_list,basic_toolprompt],
#                 "together.client.Together":[llama_function_list,llama_toolprompt]}


llm_map={"openai":llm_df.openai_llm(),
        "groq":llm_df.groq_llm(),
        "claude":llm_df.claude_llm(),
        "together":llm_df.together_llm(),
        }