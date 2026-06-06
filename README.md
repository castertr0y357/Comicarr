# Comicarr 📚✨

Comicarr is a modern, lightweight, type-safe comic book downloader and manager. Built for comic book enthusiasts who want automated library organization, snatched releases, metadata scraping, and OPDS server capabilities, all wrapped in a high-performance modern web framework.

---

## ❤️ Credits & Respect to Mylar

**Comicarr was created directly from the original [Mylar](https://github.com/mylar3/mylar3) application (specifically the Python 3 fork, Mylar3).**

Without the years of hard work, codebase evolution, filename parsing rules, search patterns, and metadata syncing structures created by the Mylar team, Comicarr would not exist. We hold the utmost respect and appreciation for the Mylar project, its maintainers, and its contributors.

While Comicarr completely overhauls the technology stack to leverage modern backend APIs, database management, and interactive UI frameworks, the underlying domain logic—specifically filename parsing exception lists, ComicVine indexing conventions, publisher mapping models, and search logic—is heavily derived from and built upon the solid foundation laid by Mylar.

We thank the Mylar contributors for their incredible service to the comic book archiving community.

---

## 🚀 Key Improvements & Tech Stack

Comicarr is a complete modernization of the CherryPy-based legacy architecture:

* **FastAPI Backend (Python 3.11+)**: Replaced CherryPy with FastAPI, utilizing asynchronous route handlers, dependency injection, and native Pydantic validation.
* **SQLModel & PostgreSQL**: Replaced SQLite/custom DB queries with SQLModel (SQLAlchemy + Pydantic) for type-safe database schemas and models. Database migrations are managed programmatically via **Alembic** on startup.
* **HTMX & Alpine.js Web GUI**: A fast, single-page application (SPA) UX styled with a premium, fully-responsive dark-themed design. No bloated React/Vue build step required.
* **Celery & Redis Task Queue**: Offloaded long-running workflows (wanted issue searches, metadata updates, library imports, post-processing) into asynchronous background workers using a Celery Beat scheduled task runner.
* **Modern Apprise Notifications**: Out-of-the-box support for 70+ notification services (Discord, Telegram, Pushover, Email, etc.) using unified Apprise URLs.

---

## 🛠️ Feature Overview

1. **Filename Parser**: Rebuilt and optimized logic extracted from Mylar's parser, parsing issue numbers, year, publisher, volume, and special matches.
2. **ComicVine Integration**: Automatic metadata updates, series synchronization, and publisher mappings.
3. **Weekly Release Lists**: Synchronizes releases via Diamond lists, auto-matching against your watchlist and flagging them as `Wanted`.
4. **Advanced Downloader Clients**: Fully-typed interfaces supporting SABnzbd, NZBGet, qBittorrent, and Transmission.
5. **Direct Download Links (DDL)**: Integrates GetComics scraping, optional FlareSolverr request bypassing, and submissions directly to JDownloader2 (JD2).
6. **Failed Download Handling**: Automated release blacklisting and retry queues when Snatch submissions or post-processing fails.
7. **Post-Processing & Metatagging**: Automated file movement, path formatting, and metatagging via ComicTagger.
8. **OPDS Catalog Server**: Serves standard OPDS feeds (Recent, Publishers, Series) with Page Streaming Extension (PSE) 1.0 support for dynamic comic page/thumbnail streaming.
9. **Library Sync**: Walks directories, parses existing collections, maps them to ComicVine, and resolves watchlist statuses.

---

## ⚙️ Setup & Installation

### Prerequisites
* Docker & Docker Compose
* A ComicVine API Key (Required for metadata matching)

### Getting Started

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/Comicarr.git
   cd Comicarr
   ```

2. **Configure Environment Variables**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your `COMICVINE_API_KEY`. You can also configure other variables like database credentials, ports, and default downloader configurations.

3. **Start the Application**
   Spin up the container stack using Docker Compose:
   ```bash
   docker compose up -d
   ```
   This starts the following services:
   * `comicarr-db` (PostgreSQL 15)
   * `comicarr-redis` (Redis 7)
   * `comicarr-web` (FastAPI Server on port 8090)
   * `comicarr-worker` (Celery Worker)
   * `comicarr-beat` (Celery Beat Scheduler)

4. **Access the Interface**
   Open your browser and navigate to `http://localhost:8090` (or the custom port you defined in `COMICARR_PORT`).

---

## 🧪 Development and Testing

If you want to run tests or run in a local development environment:

### Local Environment Setup
1. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests
To run unit and integration tests inside the Docker container:
```bash
docker compose exec web pytest tests
```

To run tests locally:
```bash
pytest tests
```
