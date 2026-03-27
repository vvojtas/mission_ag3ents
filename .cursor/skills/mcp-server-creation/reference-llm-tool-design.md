# LLM-oriented tool and MCP design (reference)

Condensed from the AI Devs lesson *Projektowanie API dla efektywnej pracy z modelem* (S01E03). Use with **mcp-server-creation** skill. For **local-first** MCP, emphasize clarity, small context, and helper hints over exposing raw API rough edges.

---

## 1. Know the API before defining tools

Verify:

- **Missing or limited actions** (e.g. cannot create a resource).
- **Resource identity**: id vs human name — the model needs explicit rules (“label X” → id `…`).
- **Inconsistent request/response shapes** (e.g. `content` vs `body`).
- **Unhelpful bodies** (e.g. only HTTP status, no payload).
- **Multi-step business flows** (several calls for one user intent) — simplify or compose at the tool layer.
- **Polling / long-running jobs** — handle in code; do not leave raw polling loops to the model when avoidable.
- **Rate limits** — backoff/retry in the server so the agent does not hammer retries.
- **Pagination and search** — first-class tools or parameters so agents avoid downloading huge lists.

Prefer **official SDKs** when available; validate assumptions (including with AI-assisted exploration).

---

## 2. Planning tool count and boundaries

- Many small endpoints **can** be grouped into fewer tools with **modes** or **clear sub-actions** if grouping improves clarity.
- **Goal is not minimal schema count** — it is **balance** between action set and how reliably the model uses each tool.
- Example pattern (filesystem): **search**, **read**, **write**, **manage** — each covers several low-level operations but stays conceptually clear.

**MCP vs native function calling:** Same design rules. MCP is a **delivery** mechanism; hosts can merge MCP tools with native tools into one list.

---

## 3. Schemas: names, parameters, responses

- **Simple tool names**; **minimal required parameters**; optional **mode** / **detail level** when one tool covers multiple behaviors.
- **Edge cases in implementation:** ambiguous paths, huge files, permission-like failures — return **actionable** messages; optionally **disambiguate** (e.g. resolve filename to path).
- **Mutating tools:** Consider **checksum / version** checks to avoid silent overwrites; **dry_run** to preview changes.
- **Successful writes:** Return **identifiers/paths** the model needs for follow-up (anchors model behavior).
- **Destructive operations:** Narrow scope; consider **undo/history** without model involvement; optional soft-delete / “trash”.

Use **Pydantic `Field(description=...)`** (or equivalent) so the host’s tool schema carries **hints** (“ask the user if not provided”).

---

## 4. Dynamic hints on success and failure

Where useful, include machine-oriented **`hints`** / **`recoveryHints`** (or similar fields) in tool results — **not only on errors**.

Patterns:

- **Error:** what happened **and** what to do next (e.g. “Resource updated; read it again before editing.”).
- **Special state:** surfaced explicitly (e.g. “Exists but not writable under current rules.”).
- **Success:** suggested next step (e.g. “Three matches; read contents before editing.”).
- **Invalid enum-like input:** list **allowed values** in the message.
- **Auto-corrections:** state what was adjusted (e.g. line range clamped to file length).

This increases implementation complexity; use AI assistance for cases, tests, and iteration.

---

## 5. MCP transports (conceptual)

- **STDIO:** Strong for **local** integration (filesystem, local CLIs); often one process per connection — typical for desktop/CLI single-user hosts.
- **Streamable HTTP:** Default for **networked** servers and multiple sessions; local development often uses **`streamable-http`** bound to **`127.0.0.1`** and a chosen port.

**From the agent’s perspective**, the origin of a tool (MCP vs built-in) should not matter if definitions are unified.

---

## 6. MCP beyond tools

MCP may also expose **resources**, **prompts**, **apps**, **sampling**, **elicitation**. Many servers expose **tools only**; add other primitives when the host and use case benefit.

---

## 7. Naming collisions across servers

When multiple MCP servers are loaded, **generic names** (`get`, `search`, `send`) **collide** and confuse models. Prefer **specific** names; hosts may prefix (`service__tool`). Design tool names with that in mind.

---

## 8. Agents vs workflows

- **Workflow:** fixed steps — predictable, less flexible.
 Agent with tools: flexible, less predictable — system prompt and tools must encode guardrails.

If **strict step order** is mandatory, a deterministic workflow may be better than relying on the model alone.

---

## 9. Validation and iteration

- Test tool designs with **smaller or local** models when possible: robust tool use under weaker models often indicates **clear schemas and descriptions**.
- Use **MCP Inspector** (or host equivalent) against **`streamable-http`** servers during development.

---

## 10. Security and auth (awareness only)

The lesson stresses **authorization**, **OAuth**, **sandboxing**, and **abuse** for public or multi-tenant servers. For **local-only** experiments, still **limit destructive tools** and **validate inputs** — the checklist above improves reliability for trusted local use too.
