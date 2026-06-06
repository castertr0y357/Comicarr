import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings, SETTINGS_CACHE_FILE
from app.core.db import engine, init_db, get_session
from app.models.settings import SystemSettings
from app.models.provider import SearchProvider
from app.models.comic import Comic
from app.models.issue import Issue
from app.services.settings_service import initialize_settings
from app.services.search import search_issue, check_indexer

MOCK_PROWLARR_JSON = [
    {
        "title": "The Amazing Spider-Man 001 (2020) (Digital) (Zone-Empire)",
        "downloadUrl": "http://localhost/get/101",
        "size": 45000000,
        "indexer": "MockProwlarrGeek",
        "protocol": "usenet",
        "publishDate": "2026-06-06T12:00:00Z"
    },
    {
        "title": "The Amazing Spider-Man 002 (2020) (Digital) (Zone-Empire)",
        "downloadUrl": "http://localhost/get/102",
        "size": 50000000,
        "indexer": "MockProwlarrFinder",
        "protocol": "torrent",
        "publishDate": "2026-06-06T13:00:00Z"
    }
]

@pytest_asyncio.fixture(scope="function")
async def db_session():
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
        await session.execute(delete(SearchProvider))
        await session.execute(delete(SystemSettings))
        await session.commit()
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def _get_session_override():
        yield db_session
    app.dependency_overrides[get_session] = _get_session_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.pop(get_session, None)

@pytest.fixture(autouse=True)
def cleanup_cache_file():
    orig_newznabs = settings.NEWZNAB_PROVIDERS
    orig_torznabs = settings.TORZNAB_PROVIDERS
    yield
    settings.NEWZNAB_PROVIDERS = orig_newznabs
    settings.TORZNAB_PROVIDERS = orig_torznabs
    if os.path.exists(SETTINGS_CACHE_FILE):
        try:
            os.remove(SETTINGS_CACHE_FILE)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_legacy_providers_migration(db_session):
    # Setup legacy providers in settings DB row
    await db_session.execute(delete(SystemSettings))
    await db_session.execute(delete(SearchProvider))
    await db_session.commit()

    legacy_settings = SystemSettings(
        id=1,
        NEWZNAB_PROVIDERS="LegacyNzb|https://nzb.test|key123",
        TORZNAB_PROVIDERS="LegacyTor|http://tor.test|key456"
    )
    db_session.add(legacy_settings)
    await db_session.commit()

    # Run initialize_settings which triggers migration
    await initialize_settings(db_session)

    # Verify providers are migrated to SearchProvider table
    stmt = select(SearchProvider)
    res = await db_session.execute(stmt)
    providers = res.scalars().all()
    assert len(providers) == 2

    # Map name to type/url
    prov_map = {p.name: p for p in providers}
    assert "LegacyNzb" in prov_map
    assert prov_map["LegacyNzb"].type == "newznab"
    assert prov_map["LegacyNzb"].url == "https://nzb.test"
    assert prov_map["LegacyNzb"].apikey == "key123"

    assert "LegacyTor" in prov_map
    assert prov_map["LegacyTor"].type == "torznab"
    assert prov_map["LegacyTor"].url == "http://tor.test"
    assert prov_map["LegacyTor"].apikey == "key456"

    # Verify settings fields are cleared
    stmt_settings = select(SystemSettings).where(SystemSettings.id == 1)
    res_settings = await db_session.execute(stmt_settings)
    db_settings = res_settings.scalars().first()
    assert db_settings.NEWZNAB_PROVIDERS == ""
    assert db_settings.TORZNAB_PROVIDERS == ""

@pytest.mark.asyncio
async def test_provider_crud_endpoints(client, db_session):
    await initialize_settings(db_session)

    # 1. Create a provider
    payload = {
        "name": "EndpointTorznab",
        "type": "torznab",
        "url": "http://indexer.local/",
        "apikey": "endpointkey",
        "enabled": "true",
        "categories": "7030"
    }
    response = await client.post("/api/providers", data=payload)
    assert response.status_code == 200
    assert "EndpointTorznab" in response.text
    assert "http://indexer.local" in response.text

    # Verify in DB
    stmt = select(SearchProvider).where(SearchProvider.name == "EndpointTorznab")
    res = await db_session.execute(stmt)
    prov = res.scalars().first()
    assert prov is not None
    assert prov.type == "torznab"
    assert prov.url == "http://indexer.local"  # Trailing slash stripped
    assert prov.apikey == "endpointkey"
    assert prov.enabled is True
    assert prov.categories == "7030"

    # 2. Update the provider
    update_payload = {
        "name": "UpdatedTorznab",
        "type": "torznab",
        "url": "http://indexer.updated",
        "apikey": "newkey",
        "enabled": "false",
        "categories": "7030,8020"
    }
    response = await client.put(f"/api/providers/{prov.id}", data=update_payload)
    assert response.status_code == 200
    assert "UpdatedTorznab" in response.text

    # Verify in DB
    await db_session.refresh(prov)
    assert prov.name == "UpdatedTorznab"
    assert prov.url == "http://indexer.updated"
    assert prov.apikey == "newkey"
    assert prov.enabled is False
    assert prov.categories == "7030,8020"

    # 3. Delete the provider
    response = await client.delete(f"/api/providers/{prov.id}")
    assert response.status_code == 200

    # Verify deletion in DB
    stmt_del = select(SearchProvider).where(SearchProvider.id == prov.id)
    res_del = await db_session.execute(stmt_del)
    assert res_del.scalars().first() is None

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_provider_connection_checks(mock_get):
    # Test Prowlarr success connection check
    mock_prowlarr_resp = MagicMock()
    mock_prowlarr_resp.status_code = 200
    mock_prowlarr_resp.json.return_value = {"version": "1.2.3"}
    mock_get.return_value = mock_prowlarr_resp

    assert await check_indexer("http://prowlarr", "key", "prowlarr") is True

    # Test Prowlarr fail connection check
    mock_prowlarr_fail = MagicMock()
    mock_prowlarr_fail.status_code = 401
    mock_get.return_value = mock_prowlarr_fail

    assert await check_indexer("http://prowlarr", "key", "prowlarr") is False

    # Test standard XML Newznab success connection check
    mock_xml_resp = AsyncMock()
    mock_xml_resp.status_code = 200
    mock_xml_resp.content = b"<caps><server></server></caps>"
    mock_get.return_value = mock_xml_resp

    assert await check_indexer("http://newznab", "key", "newznab") is True

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_prowlarr_search_integration(mock_get, db_session):
    # Insert Prowlarr provider to DB
    prov = SearchProvider(
        name="TestProwlarr",
        type="prowlarr",
        url="http://prowlarr.local",
        apikey="prowlarrkey",
        enabled=True,
        categories="7030"
    )
    db_session.add(prov)
    await db_session.commit()

    # Mock indexer network response returning JSON search results
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_PROWLARR_JSON
    mock_get.return_value = mock_resp

    comic = Comic(comic_id="1", comic_name="The Amazing Spider-Man", comic_year=2020, publisher="Marvel")
    issue = Issue(issue_id="1", comic_id="1", issue_number="1", status="Wanted")

    # Run search
    matches = await search_issue(comic, issue)

    # Verify results
    assert len(matches) == 1
    assert matches[0].title == "The Amazing Spider-Man 001 (2020) (Digital) (Zone-Empire)"
    assert matches[0].download_url == "http://localhost/get/101"
    assert matches[0].size == 45000000
    assert matches[0].provider_name == "MockProwlarrGeek"
    assert matches[0].type == "nzb"
