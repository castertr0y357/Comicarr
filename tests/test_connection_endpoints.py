import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.responses import HTMLResponse

from app.routers.api import (
    api_test_comicvine,
    api_test_weekly_pull_proxy,
    api_test_downloader,
    api_test_flaresolverr,
    api_test_external_server,
    api_test_jd2
)

@pytest.mark.asyncio
@patch("app.services.cv_api.ComicVineClient.search_volumes", new_callable=AsyncMock)
async def test_test_comicvine_endpoint(mock_search_volumes):
    mock_search_volumes.return_value = []
    
    response = await api_test_comicvine(
        api_key="dummy_key",
        url="http://dummy_url",
        user_agent="dummy_ua",
        verify="on"
    )
    assert response.status_code == 200
    assert b"ComicVine Connection Successful!" in response.body
    
    # Test failure path
    mock_search_volumes.side_effect = Exception("API Key Invalid")
    response = await api_test_comicvine(
        api_key="dummy_key",
        url="http://dummy_url",
        user_agent="dummy_ua",
        verify="on"
    )
    assert response.status_code == 200
    assert b"ComicVine Connection Failed: API Key Invalid" in response.body

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_test_weekly_pull_proxy_endpoint(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"series": "Test Series"}]
    mock_get.return_value = mock_resp
    
    response = await api_test_weekly_pull_proxy(url="http://proxy.local")
    assert response.status_code == 200
    assert b"Weekly Pull Proxy Connection Successful!" in response.body
    
    # Test failure path
    mock_resp.status_code = 500
    response = await api_test_weekly_pull_proxy(url="http://proxy.local")
    assert response.status_code == 200
    assert b"Proxy returned status code 500" in response.body

@pytest.mark.asyncio
@patch("app.downloaders.sabnzbd.SABnzbdDownloader.test_connection", new_callable=AsyncMock)
@patch("app.downloaders.nzbget.NZBGetDownloader.test_connection", new_callable=AsyncMock)
@patch("app.downloaders.qbittorrent.QBittorrentDownloader.test_connection", new_callable=AsyncMock)
@patch("app.downloaders.transmission.TransmissionDownloader.test_connection", new_callable=AsyncMock)
async def test_test_downloader_endpoints(
    mock_transmission_test, mock_qb_test, mock_nzbget_test, mock_sab_test
):
    # Test SABnzbd
    mock_sab_test.return_value = True
    response = await api_test_downloader(
        downloader_type="sabnzbd", url="http://sabnzbd", apikey="key"
    )
    assert response.status_code == 200
    assert b"SABNZBD Connection Successful!" in response.body
    
    # Test SABnzbd fail
    mock_sab_test.return_value = False
    response = await api_test_downloader(
        downloader_type="sabnzbd", url="http://sabnzbd", apikey="key"
    )
    assert response.status_code == 200
    assert b"SABNZBD Connection Failed" in response.body

    # Test NZBGet
    mock_nzbget_test.return_value = True
    response = await api_test_downloader(
        downloader_type="nzbget", url="http://nzbget", username="user", password="pwd"
    )
    assert response.status_code == 200
    assert b"NZBGET Connection Successful!" in response.body

    # Test qBittorrent
    mock_qb_test.return_value = True
    response = await api_test_downloader(
        downloader_type="qbittorrent", url="http://qb", username="user", password="pwd"
    )
    assert response.status_code == 200
    assert b"QBITTORRENT Connection Successful!" in response.body

    # Test Transmission
    mock_transmission_test.return_value = True
    response = await api_test_downloader(
        downloader_type="transmission", url="http://trans", username="user", password="pwd"
    )
    assert response.status_code == 200
    assert b"TRANSMISSION Connection Successful!" in response.body

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_test_flaresolverr_endpoint(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok"}
    mock_post.return_value = mock_resp
    
    response = await api_test_flaresolverr(url="http://flaresolverr:8191")
    assert response.status_code == 200
    assert b"FlareSolverr Connection Successful!" in response.body
    
    # Test failure path
    mock_resp.status_code = 500
    response = await api_test_flaresolverr(url="http://flaresolverr:8191")
    assert response.status_code == 200
    assert b"FlareSolverr returned status: 500" in response.body

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_test_external_server_endpoint(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    
    response = await api_test_external_server(url="http://ext-server", username="user", apikey="key")
    assert response.status_code == 200
    assert b"External Server Connection Successful!" in response.body
    
    # Test failure path (500 error)
    mock_resp.status_code = 500
    response = await api_test_external_server(url="http://ext-server", username="user", apikey="key")
    assert response.status_code == 200
    assert b"Server returned error code: 500" in response.body

@pytest.mark.asyncio
@patch("app.services.ddl.JDownloader2.test_connection", new_callable=AsyncMock)
async def test_test_jd2_endpoint(mock_jd2_test):
    mock_jd2_test.return_value = True
    
    response = await api_test_jd2(url="http://jd2:3128")
    assert response.status_code == 200
    assert b"JDownloader 2 Connection Successful!" in response.body
    
    # Test failure path
    mock_jd2_test.return_value = False
    response = await api_test_jd2(url="http://jd2:3128")
    assert response.status_code == 200
    assert b"JDownloader 2 Connection Failed" in response.body
