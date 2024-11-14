import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.model_request import image_caption_request
import cv2
import numpy as np
from datetime import timedelta
import torch
from PIL import Image
import io
import base64
import json

class VideoCaptioning:
    def extract_frames(self, video_path, interval_seconds=60):
        print("--- Extract Frames from Video ---")
        print(f"--- interval_seconds: {interval_seconds} ---")
        frames = []
        video = cv2.VideoCapture(video_path)
        
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        for second in range(0, int(duration), interval_seconds):
            print(f"processe : {second}/{duration}")
            frame_idx = int(second * fps)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = video.read()
            
            if ret:
                # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # pil_image = Image.fromarray(frame_rgb)
                # timestamp = timedelta(seconds=second)
                # frames.append((timestamp, pil_image))

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                timestamp = timedelta(seconds=second)
                
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")
                encoded_string = base64.b64encode(buffer.getvalue()).decode()
                
                frames.append((timestamp, encoded_string))
                
        video.release()
        print("--- Frame Extraction Done ---")
        return frames
    
    def process_video(self, url, vid_title,video_path, interval_seconds=60):
        frames = self.extract_frames(video_path, interval_seconds)
        
        print("--- Extracted Frame captioning Start ---")
        captions = []
        for idx,(timestamp, image) in enumerate(frames):
            print(f"{idx}/{len(frames)}")
            caption_result={"time":"","caption":"","url":"","vid_title":""}
            caption = image_caption_request(
                                    text="이미지에 대한 상세 caption을 생성해줘. caption에는 객체들 간의 관계와 각 객체의 특징(색상, 모양, 형태, 위치 등)이 상세히 포함되어야 해.",
                                    image_base64=image
                                       )["response"]
            # captions[str(timestamp)] = caption
            caption_result["time"] = str(timestamp)
            caption_result["caption"] = caption
            caption_result["url"] = url
            caption_result["vid_title"] = vid_title
            captions.append(caption_result)
            # print(f"Processed frame at {timestamp}: {caption}")
        print("--- Frame Captioning Done ---")
        return captions

    def save_captions_to_file(self, captions, output_path):
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     for timestamp, caption in sorted(captions.items()):
        #         f.write(f"[{timestamp}] {caption}\n")
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(captions, outfile,indent="\t",ensure_ascii=False)
    
    def execute(self, url, vid_title,video_path, interval_seconds=60):
        video_directory="/".join(video_path.split("/")[:-1])
        self.save_path=video_directory+"/video_captions.json"
        self.captions = self.process_video(url,vid_title,video_path, interval_seconds=60)
        self.save_captions_to_file(self.captions, self.save_path)

if __name__ == "__main__":
    captioning_system = VideoCaptioning()
    
    video_path = "/workspace/.gen/VLM/Video_to_chat/assets/[#유퀴즈온더블럭]_💥지드래곤의_컴백을_격하게_환영합니다💥_7년_만에_신곡_〈POWER〉로_돌아온_지디💕/youtube_video.mp4"
    video_directory="/".join(video_path.split("/")[:-1])
    save_path=video_directory+"/video_captions.json"
    
    captions = captioning_system.process_video(video_path, interval_seconds=60)
    captioning_system.save_captions_to_file(captions, save_path)