from mcp.server.fastmcp import FastMCP
from config import settings
from clients import LidarrClient, RadarrClient, SonarrClient
import logging
import os
from typing import List, Dict, Any, Optional
from starlette.responses import PlainTextResponse
from starlette.applications import Starlette

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arr-mcp")

# Instantiate MCP with network configurations
mcp = FastMCP(
    "Arr-MCP",
    host=settings.mcp_host,
    port=settings.mcp_port
)

# Initialize Clients
lidarr = LidarrClient(settings.lidarr_url, settings.lidarr_api_key, settings.arr_ssl_verify)
radarr = RadarrClient(settings.radarr_url, settings.radarr_api_key, settings.arr_ssl_verify)
sonarr = SonarrClient(settings.sonarr_url, settings.sonarr_api_key, settings.arr_ssl_verify)


def paginate_list(items: list, page: int, page_size: int, nopager: bool) -> list:
    """Helper to paginate a list of items locally."""
    if nopager:
        return items
    page = max(1, page)
    page_size = max(1, page_size)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


# ----------------- Lidarr Tools -----------------

@mcp.tool()
def lidarr_get_status() -> dict:
    """Get the system status and version information from the Lidarr server."""
    logger.info("lidarr_get_status called")
    return lidarr.get_system_status()

@mcp.tool()
def lidarr_list_artists(
    page: int = 1,
    page_size: int = 20,
    nopager: bool = False
) -> list:
    """List all artists in the Lidarr library, with pagination.
    
    WARNING: Do NOT use this tool to find/lookup a specific artist. Use `lidarr_search_artists` instead.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
        nopager: If True, returns all artists without pagination.
    """
    logger.info(f"lidarr_list_artists called (page={page}, page_size={page_size}, nopager={nopager})")
    artists = lidarr.get_artists()
    return paginate_list(artists, page, page_size, nopager)

@mcp.tool()
def lidarr_search_artists(term: str) -> list:
    """Search for new artists to add (artist lookup on musicbrainz/Lidarr metadata service).
    
    Args:
        term: Search term/artist name (e.g. 'Adele').
    """
    logger.info(f"lidarr_search_artists called with term: {term}")
    return lidarr.search_artists(term)

@mcp.tool()
def lidarr_list_albums(
    artist_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    nopager: bool = False
) -> list:
    """List albums in the Lidarr library, optionally filtered by artist ID, with pagination.
    
    WARNING: Do NOT use this tool to find/lookup a specific album. Use a search tool instead.
    
    Args:
        artist_id: Optional artist ID to filter albums.
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
        nopager: If True, returns all albums without pagination.
    """
    logger.info(f"lidarr_list_albums called with artist_id: {artist_id} (page={page}, page_size={page_size}, nopager={nopager})")
    albums = lidarr.get_albums(artist_id)
    return paginate_list(albums, page, page_size, nopager)

@mcp.tool()
def lidarr_trigger_command(name: str, params: Optional[dict] = None) -> dict:
    """Execute a system command in Lidarr.
    
    Args:
        name: Name of the command (e.g., 'RefreshArtist', 'ApplicationUpdate').
        params: Optional dictionary of additional command parameters.
    """
    logger.info(f"lidarr_trigger_command called: {name}")
    p = params or {}
    return lidarr.post_command(name, **p)

@mcp.tool()
def lidarr_get_queue(page: int = 1, page_size: int = 10) -> dict:
    """Show the download queue with pagination.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 10).
    """
    logger.info(f"lidarr_get_queue called (page={page}, page_size={page_size})")
    return lidarr.get_queue(page, page_size)

@mcp.tool()
def lidarr_get_history(page: int = 1, page_size: int = 10) -> dict:
    """Show activity history with pagination.

    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 10).
    """
    logger.info(f"lidarr_get_history called (page={page}, page_size={page_size})")
    return lidarr.get_history(page, page_size)

@mcp.tool()
def lidarr_get_blocklist(page: int = 1, page_size: int = 10) -> dict:
    """Show blocklisted releases with pagination.

    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 10).
    """
    logger.info(f"lidarr_get_blocklist called (page={page}, page_size={page_size})")
    return lidarr.get_blocklist(page, page_size)

@mcp.tool()
def lidarr_delete_blocklist_item(blocklist_id: int) -> dict:
    """Remove an item from the blocklist, allowing it to be grabbed again.

    Args:
        blocklist_id: The ID of the blocklist entry to remove.
    """
    logger.info(f"lidarr_delete_blocklist_item called for blocklist_id={blocklist_id}")
    return lidarr.delete_blocklist_item(blocklist_id)

@mcp.tool()
def lidarr_list_import_list_exclusions() -> list:
    """List artists excluded from being re-added by Lidarr import lists."""
    logger.info("lidarr_list_import_list_exclusions called")
    return lidarr.list_import_list_exclusions()

@mcp.tool()
def lidarr_add_import_list_exclusion(foreign_id: str, artist_name: str) -> dict:
    """Exclude an artist from being added by Lidarr import lists.

    Args:
        foreign_id: The MusicBrainz ID (mbid) of the artist to exclude.
        artist_name: The name of the artist to exclude.
    """
    logger.info(f"lidarr_add_import_list_exclusion called for foreign_id={foreign_id}")
    return lidarr.add_import_list_exclusion(foreign_id, artist_name)

@mcp.tool()
def lidarr_delete_import_list_exclusion(exclusion_id: int) -> dict:
    """Remove an import list exclusion, allowing the artist to be re-added by import lists.

    Args:
        exclusion_id: The ID of the import list exclusion to remove.
    """
    logger.info(f"lidarr_delete_import_list_exclusion called for exclusion_id={exclusion_id}")
    return lidarr.delete_import_list_exclusion(exclusion_id)


# ----------------- Radarr Tools -----------------

@mcp.tool()
def radarr_get_status() -> dict:
    """Get the system status and version information from the Radarr server."""
    logger.info("radarr_get_status called")
    return radarr.get_system_status()

@mcp.tool()
def radarr_list_movies(
    page: int = 1,
    page_size: int = 20,
    nopager: bool = False
) -> list:
    """List all movies in the Radarr library, with pagination.
    
    WARNING: Do NOT use this tool to find/lookup a specific movie. Use `radarr_search_movie` instead.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
        nopager: If True, returns all movies without pagination.
    """
    logger.info(f"radarr_list_movies called (page={page}, page_size={page_size}, nopager={nopager})")
    movies = radarr.list_movies()
    return paginate_list(movies, page, page_size, nopager)

@mcp.tool()
def radarr_get_movie(movie_id: int) -> dict:
    """Get details for a specific movie in the Radarr library by its Radarr ID.
    
    Args:
        movie_id: The ID of the movie in Radarr.
    """
    logger.info(f"radarr_get_movie called with id: {movie_id}")
    return radarr.get_movie(movie_id)

@mcp.tool()
def radarr_search_movie(term: str) -> list:
    """Search for movies to add (term lookup).
    
    Args:
        term: Search term/movie title (e.g. 'Inception').
    """
    logger.info(f"radarr_search_movie called with term: {term}")
    return radarr.search_movie(term)

@mcp.tool()
def radarr_add_movie(
    tmdb_id: int,
    root_folder: Optional[str] = None,
    quality_profile_id: Optional[int] = None,
    monitored: bool = True,
    search_for_movie: bool = False
) -> dict:
    """Add a movie to the Radarr library.
    
    Args:
        tmdb_id: TMDB ID of the movie to add.
        root_folder: Root folder path. If not provided, the first available root folder is used.
        quality_profile_id: Quality profile ID. If not provided, the first available profile is used.
        monitored: Whether to monitor the movie.
        search_for_movie: Search for the movie immediately on addition.
    """
    logger.info(f"radarr_add_movie called for tmdb_id={tmdb_id}")
    return radarr.add_movie(tmdb_id, root_folder, quality_profile_id, monitored, search_for_movie)

@mcp.tool()
def radarr_update_movie(
    movie_id: int,
    monitored: Optional[bool] = None,
    quality_profile_id: Optional[int] = None
) -> dict:
    """Update settings for a movie in the Radarr library.
    
    Args:
        movie_id: The Radarr ID of the movie to update.
        monitored: Set monitored status.
        quality_profile_id: Set quality profile ID.
    """
    logger.info(f"radarr_update_movie called for movie_id={movie_id}")
    return radarr.update_movie(movie_id, monitored, quality_profile_id)

@mcp.tool()
def radarr_delete_movie(
    movie_id: int,
    delete_files: bool = False,
    add_import_exclusion: bool = False
) -> dict:
    """Delete a movie from the Radarr library.
    
    Args:
        movie_id: The Radarr ID of the movie to delete.
        delete_files: Also delete movie files from disk.
        add_import_exclusion: Add the movie to import exclusions to prevent re-adding.
    """
    logger.info(f"radarr_delete_movie called for movie_id={movie_id}")
    return radarr.delete_movie(movie_id, delete_files, add_import_exclusion)

@mcp.tool()
def radarr_list_root_folders() -> list:
    """List root folders configured in Radarr, along with free/total space."""
    logger.info("radarr_list_root_folders called")
    return radarr.list_root_folders()

@mcp.tool()
def radarr_list_quality_profiles() -> list:
    """List quality profiles configured in Radarr."""
    logger.info("radarr_list_quality_profiles called")
    return radarr.list_quality_profiles()

@mcp.tool()
def radarr_get_queue(page: int = 1, page_size: int = 20) -> dict:
    """Show the download queue in Radarr with pagination.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
    """
    logger.info(f"radarr_get_queue called (page={page}, page_size={page_size})")
    return radarr.get_queue(page, page_size)

@mcp.tool()
def radarr_get_history(page: int = 1, page_size: int = 20) -> dict:
    """Show activity history in Radarr with pagination.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
    """
    logger.info(f"radarr_get_history called (page={page}, page_size={page_size})")
    return radarr.get_history(page, page_size)

@mcp.tool()
def radarr_trigger_command(name: str, params: Optional[dict] = None) -> dict:
    """Execute a system command in Radarr.
    
    Args:
        name: Name of the command (e.g., 'RefreshMovie', 'RenameMovie', 'RssSync').
        params: Optional dictionary of additional command parameters.
    """
    logger.info(f"radarr_trigger_command called: {name}")
    p = params or {}
    return radarr.post_command(name, **p)

@mcp.tool()
def radarr_list_indexers() -> list:
    """List configured indexers in Radarr."""
    logger.info("radarr_list_indexers called")
    return radarr.list_indexers()

@mcp.tool()
def radarr_test_indexer(indexer_id: int) -> dict:
    """Test a specific indexer configuration.

    Args:
        indexer_id: The ID of the indexer to test.
    """
    logger.info(f"radarr_test_indexer called for indexer_id={indexer_id}")
    return radarr.test_indexer(indexer_id)

@mcp.tool()
def radarr_get_blocklist(page: int = 1, page_size: int = 20) -> dict:
    """Show blocklisted releases with pagination.

    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
    """
    logger.info(f"radarr_get_blocklist called (page={page}, page_size={page_size})")
    return radarr.get_blocklist(page, page_size)

@mcp.tool()
def radarr_delete_blocklist_item(blocklist_id: int) -> dict:
    """Remove an item from the blocklist, allowing it to be grabbed again.

    Args:
        blocklist_id: The ID of the blocklist entry to remove.
    """
    logger.info(f"radarr_delete_blocklist_item called for blocklist_id={blocklist_id}")
    return radarr.delete_blocklist_item(blocklist_id)

@mcp.tool()
def radarr_list_import_list_exclusions() -> list:
    """List movies excluded from being re-added by Radarr import lists."""
    logger.info("radarr_list_import_list_exclusions called")
    return radarr.list_import_list_exclusions()

@mcp.tool()
def radarr_add_import_list_exclusion(tmdb_id: int, movie_title: str, movie_year: int) -> dict:
    """Exclude a movie from being added by Radarr import lists.

    Args:
        tmdb_id: The TMDB ID of the movie to exclude.
        movie_title: The title of the movie to exclude.
        movie_year: The release year of the movie to exclude.
    """
    logger.info(f"radarr_add_import_list_exclusion called for tmdb_id={tmdb_id}")
    return radarr.add_import_list_exclusion(tmdb_id, movie_title, movie_year)

@mcp.tool()
def radarr_delete_import_list_exclusion(exclusion_id: int) -> dict:
    """Remove an import list exclusion, allowing the movie to be re-added by import lists.

    Args:
        exclusion_id: The ID of the import list exclusion to remove.
    """
    logger.info(f"radarr_delete_import_list_exclusion called for exclusion_id={exclusion_id}")
    return radarr.delete_import_list_exclusion(exclusion_id)


# ----------------- Sonarr Tools -----------------

@mcp.tool()
def sonarr_get_health() -> dict:
    """Check Sonarr health and system status."""
    logger.info("sonarr_get_health called")
    return sonarr.get_health()

@mcp.tool()
def sonarr_list_series(
    page: int = 1,
    page_size: int = 20,
    nopager: bool = False
) -> list:
    """List all TV series in the Sonarr library, with pagination.
    
    WARNING: Do NOT use this tool to find/lookup a specific TV show/series. Use `sonarr_search_series` instead.
    
    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
        nopager: If True, returns all series without pagination.
    """
    logger.info(f"sonarr_list_series called (page={page}, page_size={page_size}, nopager={nopager})")
    series = sonarr.list_series()
    return paginate_list(series, page, page_size, nopager)

@mcp.tool()
def sonarr_search_series(term: str) -> list:
    """Search for new series (lookup).
    
    Args:
        term: Search term/series title (e.g. 'The Boys').
    """
    logger.info(f"sonarr_search_series called with term: {term}")
    return sonarr.search_series(term)

@mcp.tool()
def sonarr_get_configs() -> dict:
    """Get root folders, quality profiles, and language profiles from Sonarr."""
    logger.info("sonarr_get_configs called")
    return sonarr.get_configs()

@mcp.tool()
def sonarr_add_series(series_data: dict) -> dict:
    """Add a series to the Sonarr library.
    
    Args:
        series_data: Dictionary of series data (obtained from sonarr_search_series and sonarr_get_configs).
            Example fields: title, tvdbId, qualityProfileId, rootFolderPath, monitored, seriesType.
    """
    logger.info("sonarr_add_series called")
    return sonarr.add_series(series_data)

@mcp.tool()
def sonarr_delete_series(series_id: int, delete_files: bool = False) -> dict:
    """Delete a TV series from the Sonarr library.
    
    Args:
        series_id: The ID of the series in Sonarr.
        delete_files: Also delete series files from disk.
    """
    logger.info(f"sonarr_delete_series called for series_id={series_id}")
    return sonarr.delete_series(series_id, delete_files)

@mcp.tool()
def sonarr_get_queue() -> dict:
    """Show the download queue in Sonarr."""
    logger.info("sonarr_get_queue called")
    return sonarr.get_queue()

@mcp.tool()
def sonarr_get_history(limit: int = 20) -> dict:
    """Show activity history in Sonarr.
    
    Args:
        limit: Max number of history items to return (default: 20).
    """
    logger.info(f"sonarr_get_history called (limit={limit})")
    return sonarr.get_history(limit)

@mcp.tool()
def sonarr_trigger_command(name: str, params: Optional[dict] = None) -> dict:
    """Execute a system command in Sonarr.
    
    Args:
        name: Name of the command (e.g., 'SeriesSearch', 'RescanSeries').
        params: Optional dictionary of additional command parameters.
    """
    logger.info(f"sonarr_trigger_command called: {name}")
    p = params or {}
    return sonarr.post_command(name, **p)

@mcp.tool()
def sonarr_list_episodes(series_id: int) -> list:
    """List episodes for a specific TV series in Sonarr.

    Args:
        series_id: The ID of the series in Sonarr.
    """
    logger.info(f"sonarr_list_episodes called for series_id={series_id}")
    return sonarr.get_episodes(series_id)

@mcp.tool()
def sonarr_get_blocklist(page: int = 1, page_size: int = 20) -> dict:
    """Show blocklisted releases with pagination.

    Args:
        page: Page number to fetch (default: 1).
        page_size: Number of items per page (default: 20).
    """
    logger.info(f"sonarr_get_blocklist called (page={page}, page_size={page_size})")
    return sonarr.get_blocklist(page, page_size)

@mcp.tool()
def sonarr_delete_blocklist_item(blocklist_id: int) -> dict:
    """Remove an item from the blocklist, allowing it to be grabbed again.

    Args:
        blocklist_id: The ID of the blocklist entry to remove.
    """
    logger.info(f"sonarr_delete_blocklist_item called for blocklist_id={blocklist_id}")
    return sonarr.delete_blocklist_item(blocklist_id)

@mcp.tool()
def sonarr_list_import_list_exclusions() -> list:
    """List series excluded from being re-added by Sonarr import lists."""
    logger.info("sonarr_list_import_list_exclusions called")
    return sonarr.list_import_list_exclusions()

@mcp.tool()
def sonarr_add_import_list_exclusion(tvdb_id: int, title: str) -> dict:
    """Exclude a series from being added by Sonarr import lists.

    Args:
        tvdb_id: The TVDB ID of the series to exclude.
        title: The title of the series to exclude.
    """
    logger.info(f"sonarr_add_import_list_exclusion called for tvdb_id={tvdb_id}")
    return sonarr.add_import_list_exclusion(tvdb_id, title)

@mcp.tool()
def sonarr_delete_import_list_exclusion(exclusion_id: int) -> dict:
    """Remove an import list exclusion, allowing the series to be re-added by import lists.

    Args:
        exclusion_id: The ID of the import list exclusion to remove.
    """
    logger.info(f"sonarr_delete_import_list_exclusion called for exclusion_id={exclusion_id}")
    return sonarr.delete_import_list_exclusion(exclusion_id)


@mcp.custom_route("/version", methods=["GET"])
async def get_version(request) -> PlainTextResponse:
    version_path = os.path.join(os.path.dirname(__file__), "version.txt")
    if os.path.exists(version_path):
        with open(version_path, "r") as f:
            version_info = f.read().strip()
    else:
        version_info = "unknown"
    return PlainTextResponse(version_info)


def create_combined_app(mcp_server: FastMCP = mcp) -> Starlette:
    """Create a Starlette application combining SSE and Streamable HTTP endpoints.
    
    Exposes:
        - SSE endpoint at /sse and /messages
        - Streamable HTTP endpoint at /mcp
        - Custom routes (e.g. /version)
    """
    # Reset session manager if it has already been started in a previous lifecycle
    if getattr(mcp_server, "_session_manager", None) is not None:
        if getattr(mcp_server._session_manager, "_has_started", False):
            mcp_server._session_manager = None

    streamable_app = mcp_server.streamable_http_app()
    sse_app = mcp_server.sse_app()

    routes = []
    seen = set()
    for route in sse_app.routes + streamable_app.routes:
        key = (getattr(route, "path", None), tuple(getattr(route, "methods", []) or []))
        if key not in seen:
            seen.add(key)
            routes.append(route)

    return Starlette(
        routes=routes,
        lifespan=streamable_app.router.lifespan_context
    )


if __name__ == "__main__":
    transport = settings.mcp_transport.lower()
    if transport in ("sse", "http", "streamable-http", "streamable_http", "dual", "all"):
        logger.info(f"Starting Arr-MCP server over HTTP (SSE on /sse, Streamable HTTP on /mcp) on {settings.mcp_host}:{settings.mcp_port}...")
        import uvicorn

        combined_app = create_combined_app(mcp)
        uvicorn.run(combined_app, host=settings.mcp_host, port=settings.mcp_port)
    else:
        logger.info("Starting Arr-MCP server over stdio...")
        mcp.run(transport="stdio")

