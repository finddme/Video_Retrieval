import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
import asyncio
# from motor.motor_asyncio import AsyncIOMotorClient
import streamlit as st
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from run import RUN
from fastapi.responses import StreamingResponse
import io
from utils.formats import UserInput_query, UserInput_url
from pyngrok import conf, ngrok
from fastapi import FastAPI, BackgroundTasks

class ConnectionManager:
    """Web socket connection manager."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

async def app(args):
    fast_api_app = FastAPI(
        title="Video Retrieval"
    )

    origins = ["*"]

    conn_mgr = ConnectionManager()

    fast_api_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    run = RUN(args)

    @fast_api_app.get("/")
    def home():
        return {"message": "Video Retrieval"}

    @fast_api_app.post("/scene_search")
    async def api(user_input: UserInput_query):
        user_input=user_input.user_input
        response = StreamingResponse(
                                run.scene_search_execute(user_input),
                                media_type="text/plain"
                                )
        response.headers["Cache-Control"] ="no-cache"
        return response

    @fast_api_app.post("/data_store")
    async def api(youtube_url: UserInput_url):
        youtube_url=youtube_url.youtube_url
        run.data_processing(youtube_url)
        return {"message": "Data Save Done"} 

    @fast_api_app.post("/summary")
    async def api(youtube_url: UserInput_url):
        youtube_url=youtube_url.youtube_url
        response = StreamingResponse(
                                run.summarization_execute(youtube_url),
                                media_type="text/plain"
                                )
        response.headers["Cache-Control"] ="no-cache"
        return response

    # conf.get_default().region = "eu"
    # http_tunnel = ngrok.connect(8986) 
    # tunnels = ngrok.get_tunnels() 
    # for kk in tunnels: 
    #     print(kk)

    config = uvicorn.Config(fast_api_app, host="0.0.0.0", port=8999)
    server = uvicorn.Server(config)
    await asyncio.to_thread(server.run)

