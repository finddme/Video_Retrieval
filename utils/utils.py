import ast
import json

def seconds_to_time(seconds):
    hours = seconds // 3600 
    minutes = (seconds % 3600) // 60  
    seconds = seconds % 60  
    
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def json_available_check(data):
    try:
        result_ast = ast.literal_eval(data)
        print("AST done")
        return result_ast
    except:
        print("AST failed")
        return None