# coding-agent

Foundational scaffold for a coding agent harness, built from scratch
without an agent orchestration framework (no LangChain/CrewAI/AutoGen).

- **Milestone 1** established the architecture: `AgentLoop`,
  `MessageHistory`, a provider-agnostic `ModelClient`, and a minimal
  tool interface.
- **Milestone 2** (this revision) builds out real tool-calling: JSON
  Schema generation, argument validation, dispatch, execution, and a
  normalized result format, so the LLM can request tools, have them
  run safely, and reason over structured results.

There are still no file-editing, shell-execution, repository-indexing,
or planning tools, and no concrete LLM provider is wired up. Those are
later phases.

## Architecture

```
app/
├── core/            AgentLoop, AgentConfig, exceptions
├── models/          Pydantic data models (Message, ToolCall, ToolResult, ModelResponse)
├── llm/             ModelClient interface, provider adapter scaffold, response normalizer
├── tools/           BaseTool, ToolRegistry, SchemaGenerator, ArgumentValidator,
│                    ToolExecutor, ToolDispatcher, ResultHandler
│   └── examples/    CalculatorTool, TextLengthTool
├── context/         MessageHistory
└── main.py          Wiring example: a scripted DemoModelClient calling CalculatorTool
```

Each tool-related component has exactly one job, and the only
component allowed to depend on more than one of them is
`ToolDispatcher`:

```
ToolRegistry        — what tools exist (register/unregister/get/list, schemas)
SchemaGenerator     — turns a declarative parameter list into JSON Schema
ArgumentValidator   — is this argument dict valid against a schema?
ToolExecutor        — run a resolved tool, catch its exceptions
ResultHandler        — build the structured {status, output, error} result
ToolDispatcher       — the only thing that wires Registry + Validator + Executor together
```

`ToolRegistry` and `ToolExecutor` never import each other — that
decoupling is an explicit constraint, not an accident. `ToolExecutor`
only knows how to run a `BaseTool` it's handed; it has no idea where
that tool came from.

### AgentLoop (`app/core/agent_loop.py`)
Owns the run lifecycle for one user turn:

1. Add the user message to history.
2. Call the model with the current history and the tool schemas from
   `ToolRegistry.list_definitions()`.
3. If the model returns a final response (no tool calls), record it
   and return.
4. If the model returns tool calls, record the assistant message
   (with `tool_calls`), then call
   `ToolDispatcher.dispatch_all(response.tool_calls)` and append each
   resulting `ToolResult` to history as a tool message.
5. Loop back to the model with the updated history.
6. If `max_iterations` is reached without a final response, raise
   `MaxIterationsExceededError` rather than looping forever.

The loop depends only on the `ModelClient`, `ToolRegistry`, and
`ToolDispatcher` *interfaces*, injected through its constructor — it
has no knowledge of which provider or which concrete tools are in use.

### ModelClient and response normalization (`app/llm/`)
`ModelClient.generate(messages, tools) -> ModelResponse` is the single
abstract method every provider integration implements.
`provider_adapter.py` stays a deliberately unimplemented base class —
no concrete provider is wired up yet.

`response_normalizer.py` is new: `ResponseNormalizer` turns a
provider's raw tool-call payload (a list of `{id, name, arguments}`
dicts, where `arguments` may arrive as a JSON-encoded string — common
in real function-calling APIs) into `list[ToolCall]` and a
`ModelResponse`. This logic is shared across future provider adapters
instead of being reimplemented per provider, while staying outside
`AgentLoop` entirely.

### Tool calling infrastructure (`app/tools/`)

**BaseTool** — `name`, `description`, a JSON Schema `parameters` dict,
and a `run(**kwargs) -> Any` method. Tools may still hand-write their
schema directly (as Milestone 1's test fixtures do), or build it with
`SchemaGenerator`.

**SchemaGenerator** (`schema_generator.py`) — converts a list of
declarative `ToolParameter(name, type, description, required, items,
properties)` into a JSON Schema object. Supports `string`, `integer`,
`number`, `boolean`, `array` (via `items`), and `object` (via
`properties`) types, a `required` list built from each parameter's
`required` flag, and `additionalProperties` (defaults to `False` —
strict by default, since loosely-typed tool arguments are a common
source of silent bugs).

**ToolRegistry** (`registry.py`) — registration and lookup only.
`register()` raises `ToolAlreadyRegisteredError` on a duplicate name;
`unregister()` and `get()` raise `ToolNotFoundError` for an unknown
name; `list_tools()` and `list_definitions()` expose what's
registered.

**ArgumentValidator** (`validator.py`) — a static `validate(schema,
arguments) -> list[ValidationError]`. Checks, independent of any
registry or tool instance: missing required parameters, type
mismatches against the schema's declared `type`, and unexpected
parameters when `additionalProperties` is `False`. Returns an empty
list when arguments are valid — it never raises.

**ToolExecutor** (`executor.py`) — `execute(tool, tool_call) ->
ToolResult`. Takes an already-resolved `BaseTool`, runs it with
`tool_call.arguments`, and catches any exception it raises, turning it
into an error result instead of propagating. Stateless, so dispatching
several tool calls from one model turn is just calling it repeatedly.

**ResultHandler** (`result_handler.py`) — the only place that
constructs a `ToolResult`. `success(tool_call_id, name, output)` and
`failure(tool_call_id, name, error_type, message)` guarantee every
outcome — success, tool exception, validation failure, or unknown tool
— ends up in the same shape.

**ToolDispatcher** (`dispatcher.py`) — the orchestrator, and the only
component that depends on both `ToolRegistry` and `ToolExecutor`:

```
dispatch(tool_call):
    1. registry.get(tool_call.name)        -> unknown name: ResultHandler.failure("ToolNotFoundError")
    2. ArgumentValidator.validate(...)      -> invalid args: ResultHandler.failure("ValidationError")
    3. executor.execute(tool, tool_call)    -> ResultHandler.success(...) or .failure(...) on exception
```

`dispatch_all(tool_calls)` runs this for every tool call in a model
turn, in order, and is what `AgentLoop` calls each iteration.

### Tool result shape (`app/models/tool_result.py`)
```json
{
  "tool_call_id": "call_123",
  "status": "success",
  "output": {"result": 75},
  "error": null
}
```
On failure, `status` is `"error"`, `output` is `null`, and `error` is
`{"type": "<ExceptionClassName or 'ToolNotFoundError'/'ValidationError'>", "message": "..."}`.
`MessageHistory.add_tool_result()` serializes this to JSON as the
`content` of the tool-role message, so the model always sees the same
structure regardless of which tool ran or how it failed.

### Example tools (`app/tools/examples/`)
- **CalculatorTool** — `{a: number, b: number}` -> `{"result": a + b}`.
- **TextLengthTool** — `{text: string}` -> `{"length": len(text)}`.

Both build their schema with `SchemaGenerator` rather than hand-writing
JSON Schema, demonstrating the intended authoring path for new tools.

### MessageHistory (`app/context/message_history.py`)
Unchanged from Milestone 1: an ordered list of `Message` with
`add_user`/`add_assistant`/`add_tool_result`, returning copies from
`get_messages()` so callers can't mutate internal state.

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
ModelClient.generate(messages, tools=ToolRegistry.list_definitions())
    |
    v
ModelResponse
    |
    +---- no tool_calls ----> record assistant message, return content
    |
    +---- tool_calls --------> record assistant message (with tool_calls)
              |
              v
         ToolDispatcher.dispatch_all(tool_calls)
              |
              +--> registry.get(name)            (unknown -> error ToolResult)
              +--> ArgumentValidator.validate()   (invalid -> error ToolResult)
              +--> ToolExecutor.execute()         (exception -> error ToolResult)
              |
              v
         list[ToolResult]   (tool_call_id preserved for every call)
              |
              v
         MessageHistory.add_tool_result() per result
              |
              v
         AgentLoop loops back to ModelClient.generate()
```

## Design decisions

- **Dispatcher is the seam, not the loop.** `AgentLoop` never talks to
  `ToolRegistry` for execution and never talks to `ToolExecutor`
  directly — only `ToolDispatcher` sees both. This keeps the
  constraint "`ToolRegistry` independent of `ToolExecutor`" enforceable
  by import graph, not just convention.
- **Validation happens before execution, not inside it.** A tool's
  `run()` method never has to defend against missing/mistyped
  arguments — `ToolDispatcher` rejects those before the tool is ever
  called, so tool implementations stay focused on their actual logic.
- **One result shape, no exceptions crossing the tool boundary.**
  Whether a tool name doesn't exist, arguments fail validation, or the
  tool itself raises, the caller always gets a `ToolResult` with
  `status`/`output`/`error` — never an exception. `AgentLoop` can
  always append it to history and keep going.
- **Schemas are generated, not required to be hand-written.**
  `SchemaGenerator` exists so new tools describe parameters
  declaratively; it's additive — a tool can still set `parameters` to
  a raw dict if that's simpler for a one-off case.
- **No new dependencies for validation.** `ArgumentValidator` hand-rolls
  the small JSON-Schema subset this project needs (type-checking,
  required, additionalProperties) rather than pulling in a `jsonschema`
  package, consistent with the "avoid unnecessary abstractions"
  constraint.
- **Sync first, async-ready; DI over globals; structured Pydantic
  models at every boundary; no framework dependency.** Carried over
  from Milestone 1 — see git history for the original rationale.

## Running

```bash
pip install -r requirements.txt
python -m app.main   # scripted DemoModelClient calls CalculatorTool, then answers
pytest                # runs the test suite
```

Expected `python -m app.main` output:
```
The result is ready: {"tool_call_id":"call_1","status":"success","output":{"result":12},"error":null}
```

## Testing

All tests use `tests/mock_model_client.py`'s `MockModelClient` — a
scripted queue of `ModelResponse` objects, no API key or network
access required. Coverage includes:

- Tool registration, duplicate-registration rejection, unregistration,
  lookup of unknown tools (`test_tool_registry.py`).
- JSON Schema generation for every supported type, required/optional
  handling, `additionalProperties` (`test_schema_generator.py`).
- Argument validation: valid args, missing required, invalid types,
  unexpected args with/without `additionalProperties`
  (`test_argument_validator.py`).
- Dispatch: success, unknown tool, validation failure, multiple calls
  with `tool_call_id` preserved in order (`test_tool_dispatcher.py`).
- Execution: success, exception containment, multiple sequential calls
  (`test_tool_executor.py`).
- Result normalization for both outcomes (`test_result_handler.py`).
- End-to-end agent loop: final response without tools, single and
  multiple tool calls, tool exceptions, unknown tool names, max
  iterations, and message-history ordering (`test_agent_loop.py`).
- Message history behavior, including the JSON-serialized tool result
  content (`test_message_history.py`).

## Explicitly out of scope for this phase

Coding-specific tools (file editing, shell execution, repository
indexing), vector databases, multi-agent systems, planning engines,
memory systems, and web search. These are later phases, once this
foundation is in place.
