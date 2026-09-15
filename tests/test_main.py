import pytest
from starlette.testclient import TestClient
from main import paginate_list, create_combined_app, mcp, SERVER_INSTRUCTIONS


class TestPaginateList:
    def test_nopager_returns_all_items(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=1, page_size=2, nopager=True)
        assert result == [1, 2, 3, 4, 5]

    def test_first_page(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=1, page_size=2, nopager=False)
        assert result == [1, 2]

    def test_second_page(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=2, page_size=2, nopager=False)
        assert result == [3, 4]

    def test_last_partial_page(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=3, page_size=2, nopager=False)
        assert result == [5]

    def test_page_beyond_range_returns_empty(self):
        items = [1, 2, 3]
        result = paginate_list(items, page=10, page_size=2, nopager=False)
        assert result == []

    def test_empty_list(self):
        result = paginate_list([], page=1, page_size=10, nopager=False)
        assert result == []

    def test_page_zero_treated_as_one(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=0, page_size=2, nopager=False)
        assert result == [1, 2]

    def test_negative_page_treated_as_one(self):
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, page=-1, page_size=2, nopager=False)
        assert result == [1, 2]

    def test_page_size_one(self):
        items = [1, 2, 3]
        result = paginate_list(items, page=2, page_size=1, nopager=False)
        assert result == [2]

    def test_page_size_larger_than_list(self):
        items = [1, 2, 3]
        result = paginate_list(items, page=1, page_size=10, nopager=False)
        assert result == [1, 2, 3]

    def test_nopager_with_empty_list(self):
        result = paginate_list([], page=1, page_size=10, nopager=True)
        assert result == []


class TestCombinedApp:
    @pytest.fixture
    def app(self):
        return create_combined_app(mcp)

    def test_routes_registered(self, app):
        paths = [getattr(route, "path", None) for route in app.routes]
        assert "/version" in paths
        assert "/sse" in paths
        assert "/messages" in paths
        assert "/mcp" in paths

    def test_version_endpoint(self, app):
        with TestClient(app) as client:
            response = client.get("/version")
            assert response.status_code == 200
            assert response.text in ("unknown", "1.0.0") or len(response.text) > 0

    def test_streamable_http_requires_event_stream(self, app):
        with TestClient(app) as client:
            response = client.get("/mcp")
            assert response.status_code == 406
            assert "Client must accept text/event-stream" in response.text

    def test_streamable_http_post_initialize(self, app):
        with TestClient(app) as client:
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
            response = client.post(
                "/mcp",
                json=init_payload,
                headers={"Accept": "application/json, text/event-stream"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            assert "protocolVersion" in response.text
            assert "instructions" in response.text


class TestServerInstructions:
    def test_instructions_configured_on_server(self):
        assert mcp.instructions == SERVER_INSTRUCTIONS

    def test_instructions_non_empty_string(self):
        assert isinstance(SERVER_INSTRUCTIONS, str)
        assert len(SERVER_INSTRUCTIONS.strip()) > 0

    def test_instructions_present_in_initialize_response(self):
        app = create_combined_app(mcp)
        with TestClient(app) as client:
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
            response = client.post(
                "/mcp",
                json=init_payload,
                headers={"Accept": "application/json, text/event-stream"},
            )
            assert response.status_code == 200
            assert SERVER_INSTRUCTIONS in response.text

