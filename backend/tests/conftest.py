import asyncio
import os

import httpx
import pytest

os.environ["EVALFORGE_DATABASE_URL"] = "sqlite:////tmp/evalforge-pytest.db"
os.environ["EVALFORGE_INLINE_JOBS"] = "true"

from evalforge.database import Base, SessionLocal, engine  # noqa: E402
from evalforge.main import app  # noqa: E402
from evalforge.seed import seed_demo_data  # noqa: E402


class ASGIClient:
    def request(self, method: str, path: str, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as async_client:
                return await async_client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_demo_data(session)
    test_client = ASGIClient()
    yield test_client
    Base.metadata.drop_all(engine)
