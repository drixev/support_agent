import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command=sys.executable, args=["-m", "support_agent.mcp_server.server"]
)


@asynccontextmanager # helper (no fixture): evita líos de cancel scopes de anyio con pytest
async def mcp_session() -> AsyncIterator[ClientSession]:
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as s:
        await s.initialize()
        yield s
        
        
async def test_lists_tools_with_annotations():
    async with mcp_session() as s:
        tools = {t.name: t for t in (await s.list_tools()).tools}
        assert set(tools) == {"search_tickets", "get_ticket", "update_ticket_status"}
        assert tools["get_ticket"].annotations.readOnlyHint is True
        assert tools["update_ticket_status"].annotations.readOnlyHint is False
        

async def test_search_returns_strcutured_content():
    async with mcp_session() as s:
        r = await s.call_tool("search_tickets", {"query": "SSO"})
        assert not r.isError
        assert r.structuredContent["count"] == 1
        assert r.structuredContent["tickets"][0]["id"] == "TCK-0001"
        
        
async def test_invalid_id_is_tool_error_not_crash():
    async with mcp_session() as s:
        r = await s.call_tool("get_ticket", {"ticket_id":"abc"})
        assert r.isError # el LLM verá el error y podrá corregirse
        

async def test_status_transitions():
    async with mcp_session() as s:
        bad = await s.call_tool("update_ticket_status",{
            "ticket_id": "TCK-0001", "new_status": "resolved",
            "reason": "skip steps"
        })
        
        assert bad.isError
        ok = await s.call_tool("update_ticket_status",{
            "ticket_id": "TCK-0001", "new_status": "in_progress",
            "reason": "picked up by on-call"
        })
        assert ok.structuredContent["status"] == "in_progress"
        
        
