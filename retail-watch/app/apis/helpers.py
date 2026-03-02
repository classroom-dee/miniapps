import httpx
from fastapi import Request


# Use session context as dependency
async def get_session(request: Request) -> httpx.AsyncClient:
    return request.app.state.client
