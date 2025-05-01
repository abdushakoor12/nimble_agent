"""Tool schemas for the dev agent."""

from pydantic import BaseModel, Field

# Documentation: https://python.langchain.com/docs/how_to/custom_tools/#structuredtool


class ExecuteCommandSchema(BaseModel):
    """Schema for execute command tool."""

    command: str = Field(
        description="Command to execute. This executes in the directory within the workspace based on the current directory (current_dir). The current directory defaults to the workspace root."
    )
    timeout: int = Field(
        default=20,
        description="Timeout in seconds for the command to run",
    )


class WriteFileSchema(BaseModel):
    """Schema for write_file tool."""

    filename: str = Field(
        ...,
        description="The name of the file to write in the current directory (current_dir)",
    )
    content: str = Field(
        ...,
        description="Content to write to file. The exact content to write to the file as a string. When content includes line breaks, preserve them exactly. Include all whitespace and not strip any characters.",
    )


class ReadFileSchema(BaseModel):
    """Schema for read_file tool."""

    filename: str = Field(
        ...,
        description="The name of the file to read in the current directory (current_dir).",
    )


class ListDirectoryContentSchema(BaseModel):
    """Schema for list_directory_content tool. Lists files and folders in the current directory (current_dir)."""

    pass


class ChangeDirectorySchema(BaseModel):
    """Change the current working directory of the shell."""

    target_dir: str = Field(
        default="/",
        description="The path of the folder relative to workspace root. It sets the current_dir and must be fully qualified as a relative path. Don't put a / at the start of the path. The target is not relative to the existing current_dir. It is relative to the workspace root. Use / to go back to the root. Don't use .. or other similar symbols. Full relative paths only. Correct: app/src, Incorrect: src (where src is in the app folder inside the workspace.) ",
    )


class WriteNoteSchema(BaseModel):
    """Schema for write_note tool."""

    note_key: str | None = Field(
        default=None,
        description="A key to use for notes. This will put the note_value in the notes dictionary with this key.",
    )
    note_value: str | None = Field(
        default=None,
        description="The value to store in the notes dictionary with the note_key. Give yourself notes but don't be too verbose.",
    )
