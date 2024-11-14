from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import os
import base64
from PIL import Image
import requests
from io import BytesIO

app = FastAPI()

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct", 
    torch_dtype="auto", 
    device_map="cuda:1"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_response(messages: List[Dict[str, Any]]) -> str:
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda:1" if torch.cuda.is_available() else "cpu")

    generated_ids = model.generate(**inputs, max_new_tokens=512)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    return output_text[0]

def check_file_exists(filename: str) -> Optional[str]:
    file_path = os.path.join(UPLOAD_DIR, filename)
    return file_path if os.path.exists(file_path) else None

def process_uploaded_image(file_content: bytes, filename: str) -> Dict[str, Any]:
    existing_path = check_file_exists(filename)
    
    if existing_path:
        return {
            "type": "image",
            "image": f"file://{existing_path}"
        }
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    encoded_string = base64.b64encode(file_content).decode()
    return {
        "type": "image",
        "image": f"data:image/jpeg;base64,{encoded_string}"
    }

@app.post("/chat")
async def chat(
    text: str = Form(...),
    image_url: str = Form(None),
    image: UploadFile = None,
    image_base64: str = Form(None)
):
    try:
        image_content = None
        
        if image_url and image:
            raise HTTPException(
                status_code=400, 
                detail="Cannot process both image URL and uploaded image"
            )
        
        if image_url:
            response = requests.head(image_url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid image URL")
            image_content = {"type": "image", "image": image_url}
            
        elif image:
            if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise HTTPException(status_code=400, detail="Invalid file format")
                
            file_content = await image.read()
            image_content = process_uploaded_image(file_content, image.filename)
        elif image_base64:
            image_content={
                            "type": "image",
                            "image": f"data:image/jpeg;base64,{image_base64}"
                        }

        messages = [
                        {
                            "role": "user",
                            "content": [
                                image_content,
                                {"type": "text", "text": text}
                            ] if image_content else [
                                {"type": "text", "text": text}
                            ]
                        }
                    ]
        
        response_text = generate_response(messages)
        
        response_data = {
            "response": response_text
        }
        
        if image and check_file_exists(image.filename):
            response_data["file_path"] = os.path.join(UPLOAD_DIR, image.filename)
            
        return JSONResponse(content=response_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)