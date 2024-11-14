import whisper
import os
from pytubefix import YouTube
from pytubefix.cli import on_progress
import json

class VideoSTT:
    def createDirectory(self, directory):
        try:
            if not os.path.exists(directory):
                print(f"--- Directory created successfully: {directory} ---")
                os.makedirs(directory)
        except OSError:
            print("Error: Failed to create the directory.")

    def youtube_video_download(self,url,vid_title,main_directory):
        yt = YouTube(url, on_progress_callback = on_progress)
        
        ys = yt.streams.get_highest_resolution()

        # vid_title=yt.title.replace(" ","_").replace("/","_")

        output_directory=f"{main_directory}/{vid_title}/"
        self.createDirectory(output_directory)
        filename=f"youtube_video.mp4"
        
        file_path = os.path.join(output_directory, filename)
        
        if os.path.isfile(file_path):
            print(f"--- Video already exists ---")
            pass
        else: 
            print(f"--- Download ... {yt.title} ---")
            ys.download(output_path=output_directory, filename=filename)
            print(f"--- Video Download Done ---")
        
        return output_directory, file_path

    # @staticmethod
    def stt_with_whisper(self, directory, video_path):
        print("--- Whisper Model load ---")
        whisper_model = whisper.load_model("turbo")
        # transcription = whisper_model.transcribe(f"./{yt.title}.mp4", fp16 = False)["text"].strip()
        print("--- Start Transcribe ---")
        # path=directory+video_path
        stt_result=whisper_model.transcribe(video_path, fp16 = False)

        return stt_result

    def process_stt_by_minute(self, stt_data,url,vid_title):
        print("--- Segment STT Result ---")
        result = []
        
        segments = stt_data['segments']
        
        if not segments:
            return result
            
        current_minute = 0
        current_texts = []
        current_start = 0
        
        for segment in segments:
            segment_start_minute = int(segment['start'] // 60)
            
            if segment_start_minute == current_minute:
                current_texts.append(segment['text'].strip())
            else:
                if current_texts:
                    result.append({
                        "start": current_start,
                        "end": (current_minute + 1) * 60,
                        "text": " ".join(current_texts),
                        "url":url,
                        "vid_title":vid_title
                    })
                
                while current_minute + 1 < segment_start_minute:
                    current_minute += 1
                    result.append({
                        "start": current_minute * 60,
                        "end": (current_minute + 1) * 60,
                        "text": "",
                        "url":url,
                        "vid_title":vid_title
                    })
                
                current_minute = segment_start_minute
                current_texts = [segment['text'].strip()]
                current_start = current_minute * 60
        
        if current_texts:
            result.append({
                "start": current_start,
                "end": (current_minute + 1) * 60,
                "text": " ".join(current_texts),
                "url":url,
                "vid_title":vid_title
            })
        
        return result

    def save_transcription_to_file(self, directory,result):
        self.stt_output_path=f"{directory}/transcription.json"
        with open(self.stt_output_path, 'w', encoding='utf-8') as outfile:
            json.dump(result, outfile,indent="\t",ensure_ascii=False)

    def execute(self,url,vid_title,yt,main_directory):
        directory, self.video_path=self.youtube_video_download(url,vid_title,main_directory)
        stt_result=self.stt_with_whisper(directory, self.video_path)
        self.minute_res=self.process_stt_by_minute(stt_result,url,vid_title)
        self.save_transcription_to_file(directory,self.minute_res)
