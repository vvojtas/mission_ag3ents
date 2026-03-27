---
name: mcp-server-creation
description: >-
  Guides discussion, planning, documentation, and implementation of a FastMCP
  server with one Python module per tool under a user-chosen directory. Servers
  must be usable in-process via fastmcp Client(mcp). Use when designing MCP
  tools, splitting tools across files, scaffolding servers, or applying
  LLM-friendly tool schemas for local agents.
---

# MCP server creation

Follow **Discuss → Plan (document) → Implement**. Do not skip discussion when requirements are unclear.

## Convention: user-provided root

At the start of **Phase 1**, ask the user for the **MCP root directory** (absolute or repo-relative path). All artifacts for that server live under this root unless they specify otherwise.

Record that path at the top of **`TOOLS.md`** and use it consistently below.

Recommended layout (adjust names only if the user requests):

```text
{MCP_ROOT}/
  TOOLS.md              # spec — tool catalog, schemas, requirements
  server.py             # FastMCP instance, lifespan, compose registrations
  tools/                # package: one module per MCP tool
    __init__.py         # optional: re-export register functions
    <tool_module>.py    # exactly one logical tool per file
```

- **One MCP tool ↔ one module** under `{MCP_ROOT}/tools/`. If two operations are intentionally merged into **one** MCP tool (grouping), they still live in **one** module.
- **`server.py`** must not grow monolithic tool bodies — it wires **`mcp`**, **lifespan**, and calls **`register_*`** (or equivalent) from each tool module.

## Scope

- **Stack**: Python 3.12+, **`fastmcp`**, **`pydantic`** / `Field` for parameter descriptions; use the project’s own package manager and entrypoints when known.
- **OS**: Prefer **Windows-friendly** shell examples where relevant (PowerShell; avoid bash-only chaining in docs).

### In-process host: `Client(FastMCP)`

The composed server must work when a host connects with **FastMCP’s `Client` using the server object itself** (not only via `mcp.run()` over HTTP/stdio):

```python
from fastmcp import Client, FastMCP

mcp: FastMCP = ...  # the same instance built in server.py (imported from your package)

async with Client(mcp) as client:
    await client.list_tools()
    await client.call_tool("tool_name", {"arg": "value"})
```

**Requirements for the agent implementing the server:**

- Expose the **single** shared **`FastMCP`** instance (convention: name it **`mcp`** in `server.py` and re-export it from the package root if the user’s layout expects that).
- Register **all** tools on that instance before the host creates **`Client(mcp)`**.
- **`mcp.run(...)`** remains the entrypoint for **standalone** processes (e.g. `streamable-http`); **`Client(mcp)`** is for **same-process** embedding, tests, and app hosts that already construct the app object.
- Record in **`TOOLS.md`** how consumers attach: **in-process** (`Client(mcp)`) vs **URL** vs **STDIO**, so callers know which path to use.

If the consumer needs connection strings instead, document the equivalent **`Client("http://...")`** (or STDIO command) alongside the in-process pattern.

## Phase 1 — Discuss (requirements and API)

**Goal:** Gather enough detail to define tools without guessing.

Work through this with the user; record answers in **`{MCP_ROOT}/TOOLS.md`** (create or extend a “Requirements” section).

### 1.0 Locations

- [ ] **MCP root** — Path confirmed and written into **`TOOLS.md`**.
- [ ] **Tool module names** — Agreed snake_case stem per tool (e.g. `check_package.py`); list them in **`TOOLS.md`**.

### 1.1 Problem and host

- [ ] **Use case**: Who invokes tools (IDE, CLI agent, custom host)? **Local vs remote** MCP transport?
- [ ] **Success criteria**: What must the agent accomplish end-to-end?

### 1.2 Backend / API facts (if tools wrap an API)

- [ ] **Surface**: Endpoints or actions, HTTP methods, request/response JSON shapes.
- [ ] **Identity**: How are resources addressed (**id vs name**)? Any lookup step the model must know?
- [ ] **Gaps**: Missing actions, ambiguous fields (`content` vs `body`), success with no useful body (e.g. only status code).
- [ ] **Multi-step flows**: One user goal requiring several calls — combine in one tool vs expose a small **workflow** of tools?
- [ ] **Async / polling / rate limits**: Should the **server hide** polling and backoff so the model does not retry blindly?
- [ ] **Pagination / search**: How does the model get **small, relevant** slices of data?

### 1.3 Tool surface (early sketch)

- [ ] **Minimal tool set**: Prefer **grouping** related low-level operations when it improves clarity (balance: fewer tools vs obvious responsibility).
- [ ] **Names**: Specific, **domain-prefixed** if generic words (`search`, `get`) risk collisions across multiple MCP servers.
- [ ] **Mutations**: Need **dry-run**, **version/checksum** checks, or idempotency? Destructive actions — scope and recovery without involving the model?
- [ ] **Responses**: Should successes include **`hints`** / structured “next step” text for the model (see reference)?

### 1.4 Configuration

- [ ] **Secrets**: Load from environment or the host’s config mechanism; no hardcoded credentials.
- [ ] **Transport**: **STDIO** for tightly local, single-user processes; **`streamable-http`** for HTTP hosts unless the user needs STDIO.

**Design principles** (summary): [reference-llm-tool-design.md](reference-llm-tool-design.md)

---

## Phase 2 — Plan (`TOOLS.md` at MCP root)

**Goal:** One living document; update it whenever tools or modules change.

In **`{MCP_ROOT}/TOOLS.md`**, include:

1. **MCP root path** (as agreed).
2. **Overview** — Server display name, purpose, transport, listen address/port (if HTTP), and how hosts attach (**in-process** `Client(mcp)` vs URL vs STDIO command).
3. **Requirements summary** — Short bullets from Phase 1.
4. **Module map** — Table: MCP tool name → Python module path under `{MCP_ROOT}/tools/`.
5. **Tool catalog** — For **each** tool:
   - **Name** and **one-line responsibility**
   - **Description** (what the model sees)
   - **Parameters**: name, type, required/optional, **`Field(description=...)`** text (include “ask user if missing” where relevant)
   - **Returns**: shape; fields the model must **relay to the user** (e.g. confirmation codes)
   - **Errors / edge cases**; **hints** strategy
   - **Maps to**: API action or local behavior
6. **Open questions** — Resolve before or during implementation.

---

## Phase 3 — Implement

### 3.1 Per-tool modules (`{MCP_ROOT}/tools/<name>.py`)

**Goal:** Each file owns **one** tool’s handler and registration logic.

Recommended pattern (adapt to FastMCP version in use):

- Export a **`register_<tool>(mcp: FastMCP, **deps)** function** (or a small protocol agreed with `server.py`) that attaches **`@mcp.tool(...)`** to the async handler.
- Keep helpers **private** in the same module (`_parse_response`, etc.).
- Inject shared resources via **parameters** passed from `server.py` (e.g. client factory) or via **FastMCP lifespan context** — not global singletons unless the user’s project already standardizes on them.

Handlers: **`Annotated[..., Field(description="...")]`** aligned with **`TOOLS.md`**; typed returns where practical.

### 3.2 `server.py` (composer only)

- Construct **`mcp = FastMCP(..., instructions=...)`** — this object must be safe to pass to **`Client(mcp)`** after registrations complete.
- Optional **`@lifespan`**: open shared clients once, **`yield`** a dict into **`lifespan_context`**, close on shutdown.
- Import each tool module and call **`register_*`** so every tool is attached to the **same** `mcp` instance.
- **`if __name__ == "__main__"`**: `mcp.run(...)` with the transport and bind address documented in **`TOOLS.md`** (standalone mode; orthogonal to **`Client(mcp)`**).

### 3.3 Quality bar

- [ ] **`TOOLS.md`** module map and catalog match the code.
- [ ] **`async with Client(mcp):`** — `list_tools` and at least one **`call_tool`** succeed against the exported **`mcp`** (in-process smoke test).
- [ ] Standalone: server starts with the user’s documented command when **`mcp.run`** is required (e.g. `python server.py`).
- [ ] No unused imports; public tool functions / register entrypoints are type-hinted.

---

## Optional: spec freshness

Verify **FastMCP** / MCP APIs against current upstream docs or the lockfile in the target project — training data may lag.

---

## Additional resources

- Design checklist: [reference-llm-tool-design.md](reference-llm-tool-design.md)
