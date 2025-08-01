from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from fastapi.staticfiles import StaticFiles
import logging
import json
import re
import os
from gtts import gTTS
import uuid
from dotenv import load_dotenv
import whisper
import tempfile
from deepface import DeepFace # 雖然目前沒有影像串流，但先引入

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 請設在 .env 或環境變數

logging.basicConfig(level=logging.INFO)

app = FastAPI()
# 提供靜態檔案（TTS 音訊）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 允許前端跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或具體設為 ["http://127.0.0.1:5500"]（如果你用 VSCode Live Server）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/jobs")
async def get_jobs(keyword: str = "前端工程師"):
    logging.info(f"接收到搜尋職缺關鍵字：{keyword}")
    
    url = (
        "https://www.104.com.tw/jobs/search/list"
        f"?ro=0&keyword={keyword}&jobcatExpMore=1&order=11&page=1"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.104.com.tw/jobs/search/"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        logging.info(f"104 JSON API 回應狀態碼：{resp.status_code}")
        if resp.status_code != 200:
            return {"jobs": []}

        try:
            data = resp.json()
            job_list = data.get("data", {}).get("list", [])
            logging.info(f"擷取到職缺數量：{len(job_list)}")

            result = []
            for job in job_list[:10]:
                job_url = f"https://www.104.com.tw/job/{job.get('jobNo')}"
                result.append({
                    "title": job.get("jobName"),
                    "company": job.get("custName"),
                    "url": job_url
                })
            return {"jobs": result}
        except Exception as e:
            logging.error(f"解析 JSON 發生錯誤：{e}")
            return {"jobs": []}
        

async def call_gemini_api(client,payload):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    timeout = httpx.Timeout(30.0, read=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.ReadTimeout:
            logging.error("連線到 Gemini API 時讀取超時")
            return None
        except Exception as e:
            logging.error(f"呼叫 Gemini API 發生錯誤: {e}")
            return None

@app.post("/start_interview")
async def start_interview(request: Request):
    try:
        body = await request.json()
        job = body.get("job", {})
        job_title = job.get("title", "未知職缺")

        prompt = f'''你是一位嚴謹但友善的面試官，
        對一位應徵「{job_title}」的候選人進行第一輪面試。
        請提出第一個問題，例如要求自我介紹或詢問為何想應徵
        你只需要輸出要說給候選人聽的話就可以了
        '''

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient() as client:
            gemini_reply = await call_gemini_api(client,payload)
            logging.info(f"Gemini API 回應：{json.dumps(gemini_reply, ensure_ascii=False, indent=2)}")

            if "candidates" not in gemini_reply:
                raise ValueError("API 回應中缺少 candidates，請檢查 API key 和參數")

            text = gemini_reply["candidates"][0]["content"]["parts"][0]["text"]


        logging.info(f"Gemini 回覆內容：{text}")
        tts = gTTS(text, lang="zh-TW")
        audio_filename = f"{uuid.uuid4().hex}.mp3"
        audio_path = f"static/audio/{audio_filename}"
        os.makedirs("static/audio", exist_ok=True)
        tts.save(audio_path)

        return JSONResponse({
            "text": text,
            "audio_url": f"http://127.0.0.1:8001/static/audio/{audio_filename}"
        })

    except Exception as e:
        logging.exception("處理 /start_interview 發生錯誤")
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_user_input(audio_chunk: bytes, video_frame: bytes = None):
    transcribed_text = ""
    emotion = "neutral"

    # 將音訊資料寫入臨時檔案
    with tempfile.NamedTemporaryFile(delete=True, suffix=".webm") as tmpfile:
        tmpfile.write(audio_chunk)
        tmpfile_path = tmpfile.name

        try:
            # 使用 Whisper 進行語音轉文字
            model = whisper.load_model("turbo")
            result = model.transcribe(tmpfile_path, language="zh")
            transcribed_text = result["text"]
            logging.info(f"Whisper 轉錄結果: {transcribed_text}")
        except Exception as e:
            logging.error(f"Whisper 語音轉文字失敗: {e}")

    # TODO: Implement Deepface emotion recognition here if video_frame is provided
    # if video_frame:
    #     try:
    #         # 將影像資料寫入臨時檔案
    #         with tempfile.NamedTemporaryFile(delete=True, suffix=".jpg") as img_tmpfile:
    #             img_tmpfile.write(video_frame)
    #             img_tmpfile_path = img_tmpfile.name
    #             demographies = DeepFace.analyze(img_tmpfile_path, actions=['emotion'], enforce_detection=False)
    #             if demographies and len(demographies) > 0:
    #                 emotion = demographies[0]['dominant_emotion']
    #                 logging.info(f"Deepface 情緒辨識結果: {emotion}")
    #     except Exception as e:
    #         logging.error(f"Deepface 情緒辨識失敗: {e}")

    return transcribed_text, emotion

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conversation_history = [] # 儲存對話歷史
    try:
        while True:
            data = await websocket.receive_bytes()
            logging.info(f"Received audio chunk of size: {len(data)} bytes")

            user_text, user_emotion = await process_user_input(data)

            if user_text.strip(): # 只有當使用者有說話時才進行處理
                # 將使用者轉錄的文字發送回前端顯示
                await websocket.send_json({"speaker": "你", "text": user_text})

                # 將使用者輸入加入對話歷史
                conversation_history.append({"role": "user", "parts": [{"text": user_text}]})

                # 準備傳給 Gemini 的 payload
                payload = {
                    "contents": conversation_history
                }

                async with httpx.AsyncClient() as client:
                    gemini_reply = await call_gemini_api(client, payload)
                    logging.info(f"Gemini API 回應：{json.dumps(gemini_reply, ensure_ascii=False, indent=2)}")

                    gemini_response_text = ""
                    if "candidates" in gemini_reply and gemini_reply["candidates"]:
                        gemini_response_text = gemini_reply["candidates"][0]["content"]["parts"][0]["text"]
                        # 將 Gemini 的回覆加入對話歷史
                        conversation_history.append({"role": "model", "parts": [{"text": gemini_response_text}]})
                    else:
                        gemini_response_text = "抱歉，我沒有理解您的意思，請再說一次。"

                logging.info(f"Gemini 回覆內容：{gemini_response_text}")
                tts = gTTS(gemini_response_text, lang="zh-TW")
                audio_filename = f"{uuid.uuid4().hex}.mp3"
                audio_path = f"static/audio/{audio_filename}"
                os.makedirs("static/audio", exist_ok=True)
                tts.save(audio_path)
                audio_url = f"http://127.0.0.1:8001/static/audio/{audio_filename}"

                await websocket.send_json({"text": gemini_response_text, "audio_url": audio_url})

    except WebSocketDisconnect:
        logging.info("Client disconnected from WebSocket")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")