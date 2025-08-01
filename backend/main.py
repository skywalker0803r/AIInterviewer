from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
import logging
import json
import re
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 允許前端跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
