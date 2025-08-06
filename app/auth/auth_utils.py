# redis와 연결
# 이 파일은 Redis 클라이언트를 설정하고 블랙리스트 기능을 구현합니다.
# Redis는 토큰 블랙리스트를 관리하는 데 사용됩니다.

from app.redis.redis_client import redis

async def blacklist_token(token: str, expire_seconds: int):
    # 토큰을 블랙리스트에 추가, expire_seconds 후 자동 삭제
    await redis.set(token, "blacklisted", ex=expire_seconds)

