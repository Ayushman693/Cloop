# coding-agent

Foundational scaffold for a coding agent harness, built from scratch
without an agent orchestration framework (no LangChain/CrewAI/AutoGen).
This phase establishes the architecture and interfaces only — there are
no file-editing, shell-execution, repository-indexing, or planning
tools yet, and no concrete LLM provider is wired up. Those are later
phases.

## Architecture

The harness is split into five components with a single responsibility
each, connected through small interfaces rather than direct
dependencies. The `AgentLoop` is the only component that knows about
all the others; everything else is independently testable in
isolation.

```
app/
├── core/            AgentLoop, AgentConfig, exceptions
├── models/          Pydantic data models (Message, ToolCall, ToolResult, ModelResponse)
├── llm/             ModelClient interface + provider adapter scaffold
├── tools/           BaseTool interface, ToolRegistry, ToolExecutor
├── context/         MessageHistory
└── main.py          Wiring example (uses a trivial EchoModelClient)
```

### AgentLoop (`app/core/agent_loop.py`)
Owns the run lifecycle for one user turn:

1. Add the user message to history.
2. Call the model with the current history and available tool
   definitions.
3. If the model returns tool calls, dispatch each one through
   `ToolExecutor`, append the tool message and assistant message to
   history, and loop again.
4. If the model returns a final response (no tool calls), record it
   and return.
5. If `max_iterations` is reached without a final response, raise
   `MaxIterationsExceededError` rather than looping forever.

The loop depends only on the `ModelClient` and `ToolRegistry`/
`ToolExecutor` *interfaces*, injected through its constructor. It has
no knowledge of which provider or which concrete tools are in use —
that's what keeps it provider-agnostic and testable with a mock.

### ModelClient (`app/llm/base.py`)
Abstract interface with a single method, `generate(messages, tools) ->
ModelResponse`. Any provider integration implements this and is
responsible for translating to/from that provider's wire format.
`provider_adapter.py` is a deliberately unimplemented base class
marking where a real provider (OpenAI, Anthropic, etc.) will plug in
during a later phase.

### ToolRegistry vs. ToolExecutor (`app/tools/`)
Split into two components on purpose:

- `ToolRegistry` only knows *what tools exist* — registration, lookup
  by name, and producing the schema list to hand the model.
- `ToolExecutor` only knows *how to run a tool call* — resolving it
  against a registry, invoking it, and catching any exception so a
  single failing tool can't crash the loop. It always returns a
  structured `ToolResult`, with `is_error=True` and a message on
  failure instead of raising.

This separation means registering a new tool never touches execution
logic, and execution/error-handling logic never touches registration.

### MessageHistory (`app/context/message_history.py`)
A thin, ordered list of `Message`. Provides `add_user`,
`add_assistant`, and `add_tool_result` so the loop never constructs
`Message` objects by hand, and `get_messages()` returns a copy so
callers can't mutate internal state.

### Data models (`app/models/`)
All cross-component data is a Pydantic model, not a dict:

- `Message` — one turn in the conversation (`role`, `content`,
  optional `tool_calls`/`tool_call_id`/`name`).
- `ToolCall` — a requested invocation (`id`, `name`, `arguments`).
- `ToolResult` — the outcome of executing a `ToolCall`
  (`tool_call_id`, `name`, `content`, `is_error`).
- `ModelResponse` — the normalized result of a model turn (`content`,
  `tool_calls`, `finish_reason`).
- `AgentConfig` — run configuration (`max_iterations`, `model_name`).

## Execution flow

```
User Input
    |
    v
AgentLoop.run()
    |
    v
MessageHistory.add_user()
    |
    v
ModelClient.generate(messages, tools)
    |
    v
ModelResponse
    |
    +---- no tool_calls ----> record assistant message, return content
    |
    +---- tool_calls --------> record assistant message (with tool_calls)
              |
              v
         ToolExecutor.execute(tool_call)   (per call; errors become ToolResult.is_error=True)
              |
              v
         ToolResult
              |
              v
         MessageHistory.add_tool_result()
              |
              v
         AgentLoop loops back to ModelClient.generate()
```

## Design decisions

- **Sync first, async-ready.** `ModelClient.generate` and `BaseTool.run`
  are synchronous. Nothing here precludes adding `AsyncModelClient`/
  `async def run` variants later; the loop's shape (call model,
  dispatch tools, repeat) doesn't change, so we didn't pay the
  complexity cost of async up front.
- **Dependency injection over globals.** `AgentLoop` takes its
  `ModelClient`, `ToolRegistry`, and `ToolExecutor` as constructor
  arguments. This is what makes it testable with `MockModelClient` and
  no network access, and what keeps provider/tool choice a wiring
  decision made in `main.py`, not baked into the loop.
- **Structured results, not dicts.** Every boundary (model response,
  tool call, tool result) is a Pydantic model so invalid shapes fail
  fast and IDEs/type checkers can catch mistakes before runtime.
- **Errors are contained, not caught everywhere.** Only
  `ToolExecutor.execute` swallows exceptions (converting them to an
  error `ToolResult`) because a single tool failing is an expected,
  recoverable event. Everything else (e.g.
  `MaxIterationsExceededError`) is allowed to propagate — silently
  swallowing those would hide real bugs.
- **No framework dependency.** Only `pydantic` and `pytest`. The intent
  of this project is to understand the harness architecture, not to
  configure an existing one.

## Running

```bash
cd coding-agent
pip install -r requirements.txt
python -m app.main        # runs the wiring demo with EchoModelClient
pytest                     # runs the test suite
```

## Testing

All tests use `tests/mock_model_client.py`'s `MockModelClient`, which
returns a scripted queue of `ModelResponse` objects — no API key or
network access required. Coverage includes: a final response with no
tool calls, a single tool call, multiple tool calls in one turn, a
failing tool call, exceeding `max_iterations`, and verifying message
history ordering (`user` → `assistant` → `tool` → `assistant`).

## Explicitly out of scope for this phase

File editing tools, terminal execution, repository indexing, vector
databases, multi-agent systems, planning engines, memory systems, and
web search. These are later phases, once this foundation is in place.
