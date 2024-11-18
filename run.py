from frame_caption.frame_caption import VideoCaptioning
from audio_transcription.audio_transcription import VideoSTT
from db.db_management import *
from pytubefix import YouTube
from pytubefix.cli import on_progress
from utils.logging_wrapper import LoggingWrapper
from video_scene_search.retrieve import Retrieve
from video_summarization.summarization import Summarization
from model.models import *
from model.prompt import *
from utils.formats import relevant_score_format
from model.completion import Completion, Completion_stream,Completion_instructor
from utils.map import *
from utils.utils import seconds_to_time, extract_hashtags, time_to_seconds
import emoji
from functools import reduce

logger = LoggingWrapper('ayaan_logger')
logger.add_file_handler("info")
logger.add_stream_handler("error")

class RUN:
    def __init__(self,args):
        self.args=args 

        self.stt_embed_key="text"
        self.caption_embed_key="caption"

        self.stt_class_name=f"stt_{self.args.main_class_name}"
        self.captioning_class_name=f"captioning_{self.args.main_class_name}"

        self.llm=llm_map[self.args.llm]
        model_type = str(type(self.llm))
        self.model_type = model_type[model_type.find("'")+1:model_type.rfind("'")]
        self.completion_stream=Completion_stream(self.llm)
        self.completion_instructor=Completion_instructor(self.llm)
        self.completion=Completion(self.llm)

        self.weaviate_client = weaviate.Client(waviate_url) 
        self.co = cohere_engine()

    def data_processing(self,youtube_url):
        logger.info(f"Operation: [Data Processing]")

        yt = YouTube(youtube_url, on_progress_callback = on_progress)
        
        replacements={"/":"_",
                    "\\":"_",
                    "#": "_",
                    "|": "_",
                    " ":"_",
                    ".":"_"}
        replace_func = lambda text: reduce(lambda t, kv: t.replace(kv[0], kv[1]), replacements.items(), text)
        self.vid_title=yt.title
        self.vid_title=emoji.replace_emoji(self.vid_title, '_')
        self.vid_title = replace_func(self.vid_title)
        logger.info(f"[Data Processing] Video: {youtube_url} -> {self.vid_title}")

        self.description=yt.description
        self.description=extract_hashtags(self.description)
        self.description=" ".join(self.description)

        if self.args.db_sync:
            db_class_sync_check(self.weaviate_client)
        saved_class_list, class_name_list, file_name_list=load_weaviate_class_list()

        print("--- check DB ---")
        if self.vid_title in file_name_list:
            class_name = list(map(lambda x: x['class'], filter(lambda x: x['file']==self.vid_title, saved_class_list)))
            print(f"--- Video data exist ---")
            logger.info(f"[Data Processing] Video data exist")
        else:
            print(f"--- Video data not exist, STT and Captioning Start ---")
            logger.info(f"[Data Processing] Video data not exist, STT and Captioning Start")

            vid_stt=VideoSTT()
            captioning_system = VideoCaptioning()

            main_directory="./assets"
            vid_stt.execute(youtube_url,self.vid_title,self.description,yt,main_directory)
            video_path=vid_stt.video_path
            stt_saved_path=vid_stt.stt_output_path
            stt_result=vid_stt.minute_res

            captioning_system.execute(youtube_url,self.vid_title,self.description,video_path)
            caption_saved_path=captioning_system.save_path
            caption_result=captioning_system.captions

            print("--- STT DB processing ---")
            _=save_weaviate(self.weaviate_client,
                            "stt",
                            stt_result,
                            self.vid_title,
                            self.stt_embed_key,
                            self.args.main_class_name,
                            file_name_list
                            )
            print("--- Captioning DB processing ---")
            _=save_weaviate(self.weaviate_client,
                            "captioning",
                            caption_result,
                            self.vid_title,
                            self.caption_embed_key,
                            self.args.main_class_name,
                            file_name_list
                            )
        
            logger.info(f"[Data Processing] Done")
            logger.info(f"==============================================================================================")

    def scene_search_execute(self,query):
        logger.info(f"Operation: [Scene Search]")
        logger.info(f"[Scene Search] Query: {query}")
        final_generate=""
        # retrieve
        (stt_documents,caption_documents)=Retrieve.retrieve(self.weaviate_client,
                                            query,
                                            self.stt_class_name,
                                            self.stt_embed_key,
                                            self.captioning_class_name,
                                            self.caption_embed_key)
        # rerank
        stt_rerank_res=Retrieve.reranker_cohere(self.weaviate_client,
                                                self.co,
                                                query,
                                                stt_documents,
                                                self.stt_class_name)
        captioning_rerank_res=Retrieve.reranker_cohere(self.weaviate_client,
                                                        self.co,
                                                        query,
                                                        caption_documents,
                                                        self.captioning_class_name)

        # stt retreival result
        relevant_stt_res=[]
        for srr in stt_rerank_res:
            try:
                stt_doc=srr["doc"]
                stt_description=srr["description"]
                stt_doc=f"{stt_description}\n{stt_doc}"
                print("--- Video Relevant Check ---")
                scoring_prompt=relevant_scoring_prompt.format(stt_doc,query)
                score=self.completion_instructor(scoring_prompt,"",relevant_score_format)
                score=score["score"]
                if score.lower() == "yes":
                    logger.info(f"[Scene Search] STT relevant doc: {stt_doc}")
                    relevant_stt_res.append(srr)

            except Exception as e: 
                print(f"Error: {e}")

        # captioning retreival result
        relevant_caption_res=[]
        for crr in captioning_rerank_res:
            try:
                caption_doc=crr["doc"]
                caption_description=crr["description"]
                caption_doc=f"{caption_description}\n{caption_doc}"
                print("--- Video Relevant Check ---")
                scoring_prompt=relevant_scoring_prompt.format(query, caption_doc)
                score=self.completion_instructor("",scoring_prompt,relevant_score_format)["score"]
                if score.lower() == "yes":
                    logger.info(f"[Scene Search] Caption relevant doc: {caption_doc}")
                    relevant_caption_res.append(crr)
                    # return answer and youtube url
                    # 
            except Exception as e: 
                print(f"Error: {e}")

        relevant_datas_by_time=[]

        captions_by_time = {time_to_seconds(item['time']): item for item in relevant_caption_res} # {60:{data}, 120:{data}, ...}
        stt_by_time = {int(item['time']): item for item in relevant_stt_res}
        all_times = set(captions_by_time.keys()) | set(stt_by_time.keys()) # {60,120,180, ...}

        for time in sorted(all_times):
            data_entry = {
                'time': seconds_to_time(time),
                'stt_data': stt_by_time.get(time, None),
                'caption_data': captions_by_time.get(time, None)
            }
            relevant_datas_by_time.append(data_entry)

        logger.info(f"[Scene Search] Result: {relevant_datas_by_time}")

        for rdbt in relevant_datas_by_time:
            stt_data_format,stt_data,caption_data_format,caption_data="transcription: {}","","frame caption: {}",""

            common_info={"url":"","title":""}
            time_info=rdbt["time"]

            if rdbt["stt_data"]:
                stt_doc= rdbt["stt_data"]["doc"]
                stt_desc= rdbt["stt_data"]["description"]

                common_info["url"]= rdbt["stt_data"]["url"]
                common_info["title"]= rdbt["stt_data"]["title"]

                stt_data+=stt_data_format.format(f"{stt_desc}\n{stt_doc}")

            if rdbt["caption_data"]:
                caption_doc= rdbt["caption_data"]["doc"]
                caption_desc= rdbt["caption_data"]["description"]

                common_info["url"]= rdbt["caption_data"]["url"]
                common_info["title"]= rdbt["caption_data"]["title"]

                caption_data+=caption_data_format.format(f"{caption_desc}\n{caption_doc}")

            url_info=common_info["url"]
            title_info=common_info["title"]
            yield f"Video:{url_info}\nVideo title:{title_info}\nTime:{time_info}\n\n"

            doc_data= f"{stt_data}\n{caption_data}\n\n"
            prompt=explain_prompt_merged_v1.format(doc_data)
            for chunk in self.completion_stream(query,prompt):
                final_generate+=chunk
                yield f"{chunk}"
            yield f"\n\n=============================================================\n\n"

        logger.info(f"[Scene Search] Result: {final_generate}")
        logger.info(f"==============================================================================================")

    def scene_search_execute_bk(self,query):
        logger.info(f"Operation: [Scene Search]")
        logger.info(f"[Scene Search] Query: {query}")
        final_generate=""
        # retrieve
        (stt_documents,caption_documents)=Retrieve.retrieve(self.weaviate_client,
                                            query,
                                            self.stt_class_name,
                                            self.stt_embed_key,
                                            self.captioning_class_name,
                                            self.caption_embed_key)
        # rerank
        stt_rerank_res=Retrieve.reranker_cohere(self.weaviate_client,
                                                self.co,
                                                query,
                                                stt_documents,
                                                self.stt_class_name)
        captioning_rerank_res=Retrieve.reranker_cohere(self.weaviate_client,
                                                        self.co,
                                                        query,
                                                        caption_documents,
                                                        self.captioning_class_name)

        # top 1 each stt, caption
        # stt_rerank_res=[srr for idx,srr in enumerate(stt_rerank_res) if idx==0] 
        # captioning_rerank_res=[crr for idx,crr in enumerate(captioning_rerank_res) if idx==0] 

        # stt retreival result
        relevant_stt_res=[]
        for srr in stt_rerank_res:
            try:
                stt_doc=srr["doc"]
                stt_time=seconds_to_time(srr["time"])
                stt_url=srr["url"]
                stt_title=srr["title"]
                stt_description=srr["description"]

                stt_doc=f"{stt_description}\n{stt_doc}"

                print("--- Video Relevant Check ---")
                scoring_prompt=relevant_scoring_prompt.format(stt_doc,query)
                score=self.completion_instructor(scoring_prompt,"",relevant_score_format)

                score=score["score"]
                if score.lower() == "yes":
                    logger.info(f"[Scene Search] STT relevant doc: {stt_doc}")
                    relevant_stt_res.append(stt_doc)
                    # return answer and youtube url
                    yield f"Video:{stt_url}\nVideo title:{stt_title}\nTime:{stt_time}\n\n"

                    stt_prompt=stt_explain_prompt.format(stt_doc)
                    for chunk in self.completion_stream(query,stt_prompt):
                        final_generate+=chunk
                        yield f"{chunk}"
                    yield f"\n\n=============================================================\n\n"
            except Exception as e: 
                print(f"Error: {e}")

        # captioning retreival result
        relevant_caption_res=[]
        for crr in captioning_rerank_res:
            try:
                caption_doc=crr["doc"]
                caption_time=crr["time"]
                caption_url=crr["url"]
                caption_title=crr["title"]
                caption_description=crr["description"]

                caption_doc=f"{caption_description}\n{caption_doc}"

                print("--- Video Relevant Check ---")
                scoring_prompt=relevant_scoring_prompt.format(query, caption_doc)
                score=self.completion_instructor("",scoring_prompt,relevant_score_format)["score"]
                if score.lower() == "yes":
                    logger.info(f"[Scene Search] Caption relevant doc: {caption_doc}")
                    relevant_caption_res.append(caption_doc)
                    # return answer and youtube url
                    yield f"Video:{caption_url}\nVideo title:{caption_title}\nTime:{caption_time}\n\n"

                    captioning_prompt=caption_explain_prompt.format(caption_doc)
                    for chunk in self.completion_stream(query,captioning_prompt):
                        final_generate+=chunk
                        yield f"{chunk}"
                    yield f"\n\n=============================================================\n\n"
            except Exception as e: 
                print(f"Error: {e}")
        logger.info(f"[Scene Search] Result: {final_generate}")
        logger.info(f"==============================================================================================")

    def summarization_execute(self,youtube_url):
        logger.info(f"Operation: [Summarization]")
        final_generate=""
        self.data_processing(youtube_url)
        logger.info(f"[Summarization] Video: {youtube_url} -> {self.vid_title}")
        stt_summary,caption_summary=Summarization.summarization(self.weaviate_client,
                                                                self.vid_title,
                                                                self.description,
                                                                self.stt_class_name,
                                                                self.captioning_class_name,
                                                                self.completion)

        summary_prompt=final_summary_prompt.format(caption_summary,stt_summary)[:30000]
        for chunk in self.completion_stream(summary_prompt,final_summary_system_prompt):
            final_generate+=chunk
            yield f"{chunk}"
        
        logger.info(f"[Summarization] Result: {final_generate}")
        logger.info(f"==============================================================================================")