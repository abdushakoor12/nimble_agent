"""Constants used throughout the AI coding agent application."""

# Constants for model configuration

DEFAULT_GPT_MODEL = "gpt-4o-mini"  # DO NOT CHANGE!!!
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAXITERATIONS = 10

DEFAULT_COMMAND_TIMEOUT = 20.0

ROOT_RELATIVE_PATH = "/"

# Messages
ERROR_MESSAGE_WORKSPACE_DOT_NOT_EXIST = "Workspace path does not exist"
ERROR_MESSAGE_WORKSPACE_NOT_DIRECTORY = "Workspace path is not a directory"
ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE = "Workspace path is not an absolute path"

ERROR_MESSAGE_TARGET_NOT_DIRECTORY = "Target is not a directory"
ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER = (
    "There is an invalid character in the path"
)
ERROR_MESSAGE_TARGET_DIRECTORY_NOT_EXIST = "Error: Directory does not exist"
ERROR_MESSAGE_NAVIGATE_OUTSIDE_WORKSPACE = "Error: cannot navigate outside workspace"
ERROR_MESSAGE_UNQUALIFIED_PATH = "Error: The directory {target_dir} does exist in {current_dir} but you need to fully qualify the relative path. Try {current_dir}/{target_dir}"
ERROR_MESSAGE_DIRECTORY_CHANGE_FAILED = "Changing directory failed"
