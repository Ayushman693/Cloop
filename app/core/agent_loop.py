"""The agent's execution loop: model call -> tool dispatch -> repeat."""

from __future__ import annotations

from app.context.message_history import MessageHistory
from app.core.config import AgentConfig
from app.core.exceptions import MaxIterationsExceededError
from app.llm.base import ModelClient
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import ToolRegistry


class AgentLoop:
    """Owns a single run's lifecycle: calling the model, dispatching any
    tool calls it requests, and feeding results back until the model
    produces a final response or the iteration limit is reached.

    The loop depends only on the `ModelClient`, `ToolRegistry` (for
    schemas), and `ToolDispatcher` (for execution) interfaces, injected
    via the constructor — it has no knowledge of which provider or
    which concrete tools are in use.
    """

    def __init__(
        self,
        model_client: ModelClient,
        tool_registry: ToolRegistry,
        tool_dispatcher: ToolDispatcher,
        config: AgentConfig | None = None,
        history: MessageHistory | None = None,
    ) -> None:
        self._model_client = model_client
        self._tool_registry = tool_registry
        self._tool_dispatcher = tool_dispatcher
        self._config = config or AgentConfig()
        self._history = history or MessageHistory()

    @property
    def history(self) -> MessageHistory:
        return self._history

    def run(self, user_input: str) -> str:
        """Run the loop to completion for a single user turn.

        Returns:
            The model's final textual response.

        Raises:
            MaxIterationsExceededError: if `config.max_iterations` turns
                pass without the model returning a final response.
        """
        self._history.add_user(user_input)

        for _ in range(self._config.max_iterations):
            response = self._model_client.generate(
                messages=self._history.get_messages(),
                tools=self._tool_registry.list_definitions(),
            )

            if not response.tool_calls:
                self._history.add_assistant(content=response.content)
                return response.content or ""

            self._history.add_assistant(
                content=response.content, tool_calls=response.tool_calls
            )
            results = self._tool_dispatcher.dispatch_all(response.tool_calls)
            for result in results:
                self._history.add_tool_result(result)

        raise MaxIterationsExceededError(
            f"Agent loop did not reach a final response within "
            f"{self._config.max_iterations} iterations."
        )
