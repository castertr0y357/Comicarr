from typing import Optional, List

from app.core.config import settings
from app.core.logger import logger
from app.downloaders.base import BaseDownloader
from app.downloaders.sabnzbd import SABnzbdDownloader
from app.downloaders.nzbget import NZBGetDownloader
from app.downloaders.qbittorrent import QBittorrentDownloader
from app.downloaders.transmission import TransmissionDownloader


def get_downloader(client_type: Optional[str] = None) -> Optional[BaseDownloader]:
    """
    Factory function that instantiates and returns the configured
    downloader client. Falls back to DOWNLOADER_TYPE from settings
    if no client_type is explicitly provided.

    Returns None if no valid downloader is configured.
    """
    resolved_type = (client_type or settings.DOWNLOADER_TYPE).lower().strip()

    if resolved_type == "sabnzbd":
        return SABnzbdDownloader()

    if resolved_type == "nzbget":
        return NZBGetDownloader()

    if resolved_type == "qbittorrent":
        return QBittorrentDownloader()

    if resolved_type == "transmission":
        return TransmissionDownloader()

    if resolved_type != "none" and resolved_type != "multiple":
        logger.warning(
            f"[Downloaders] Unknown downloader type '{resolved_type}'. "
            "Valid options: sabnzbd, nzbget, qbittorrent, transmission, multiple, none."
        )
    return None


def get_ordered_downloaders(release_type: Optional[str] = None) -> List[BaseDownloader]:
    """
    Returns an ordered list of enabled downloader clients for a given release type
    based on system settings and preferences.
    """
    resolved_type = settings.DOWNLOADER_TYPE.lower().strip()

    if resolved_type != "multiple":
        dl = get_downloader(resolved_type)
        return [dl] if dl else []

    if not release_type:
        enabled = []
        if settings.SABNZBD_ENABLED:
            enabled.append(SABnzbdDownloader())
        if settings.NZBGET_ENABLED:
            enabled.append(NZBGetDownloader())
        if settings.QBITTORRENT_ENABLED:
            enabled.append(QBittorrentDownloader())
        if settings.TRANSMISSION_ENABLED:
            enabled.append(TransmissionDownloader())
        return enabled

    release_type = release_type.lower().strip()
    if release_type == "nzb":
        pref = settings.USENET_PREFERENCE.lower().strip()
        candidates = []
        if pref == "nzbget":
            if settings.NZBGET_ENABLED:
                candidates.append(NZBGetDownloader())
            if settings.SABNZBD_ENABLED:
                candidates.append(SABnzbdDownloader())
        else:
            if settings.SABNZBD_ENABLED:
                candidates.append(SABnzbdDownloader())
            if settings.NZBGET_ENABLED:
                candidates.append(NZBGetDownloader())
        return candidates

    elif release_type == "torrent":
        pref = settings.TORRENT_PREFERENCE.lower().strip()
        candidates = []
        if pref == "transmission":
            if settings.TRANSMISSION_ENABLED:
                candidates.append(TransmissionDownloader())
            if settings.QBITTORRENT_ENABLED:
                candidates.append(QBittorrentDownloader())
        else:
            if settings.QBITTORRENT_ENABLED:
                candidates.append(QBittorrentDownloader())
            if settings.TRANSMISSION_ENABLED:
                candidates.append(TransmissionDownloader())
        return candidates

    return []
