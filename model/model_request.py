import requests

def image_caption_request(text, image_path=None,image_url=None,image_base64=None):
    url = "http://115.71.28.105:8000/chat"
    
    headers = {
                'accept': 'application/json'
                }
    
    files = {
            'text': (None, text),
            'image_url': (None, image_url), 
            'image': ('image.png', open(image_path, 'rb'), 'image/png') if image_path else None,
            'image_base64': (None, image_base64), 
            }
    try:
        response = requests.post(
                                url,
                                headers=headers,
                                files=files
                                )
        
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        raise
        
    finally:
        if image_path:
            files['image'][1].close()

if __name__ == "__main__":
    try:
        response = image_caption_request(
            text="이미지에 대한 상세 caption을 생성해줘. caption에는 객체들 간의 관계와 각 객체의 특징이 상세히 포함되어야 해.",
            image_path="/workspace/.gen/VLM/Video_to_chat/assets/image_test/8eb0e95c-a30c-442b-ac4b-e6ba90d4a730.png"
            # image_url="https://png.pngtree.com/thumb_back/fh260/background/20230609/pngtree-three-puppies-with-their-mouths-open-are-posing-for-a-photo-image_2902292.jpg"
            )
        
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")