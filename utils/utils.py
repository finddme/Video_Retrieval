import ast
import json

def seconds_to_time(seconds):
    hours = seconds // 3600 
    minutes = (seconds % 3600) // 60  
    seconds = seconds % 60  
    
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def time_to_seconds(time_str):
    if isinstance(time_str, str) and ':' in time_str:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    return time_str

def json_available_check(data):
    try:
        result_ast = ast.literal_eval(data)
        print("AST done")
        return result_ast
    except:
        print("AST failed")
        return None

def extract_hashtags(text):
    words = text.replace('\n', ' ').split()
    
    hashtags = [word.strip() for word in words if word.startswith('#')]
    
    return hashtags