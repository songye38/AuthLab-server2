# redis 클라이언트 세팅 (redis 4.x 이상 사용 시)

import redis.asyncio as redis_async
from dotenv import load_dotenv
import os

load_dotenv()  # 필수

REDIS_URL = os.getenv("REDIS_URL")
redis = redis_async.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
