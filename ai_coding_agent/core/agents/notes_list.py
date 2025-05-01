"""NotesList is a simple class that allows you to store and retrieve notes."""

from langchain_core.messages import AIMessage


class NotesList:
    """NotesList is a simple class that allows you to store and retrieve notes."""

    inner_map: dict[str, str]
    _messages: list  # type: ignore

    def __init__(self):
        """Initialize an empty NotesList."""
        self.inner_map = {}
        self._messages = []

    def set_item(self, key: str, value: str) -> None:
        """Set a note."""
        self.inner_map[key] = value
        # replace the message if it exists
        for msg in self._messages:
            if msg.content.startswith(key):
                msg.content = f"{key} (note): {value}"
                return
        self._messages.append(AIMessage(content=f"{key} (note): {value}"))

    @property
    def get_messages(self) -> list:  # type: ignore
        """Get all notes."""
        return self._messages
