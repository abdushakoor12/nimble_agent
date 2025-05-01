# Nimble Agent

A LangChain, CLI based AI coding assistant and library aimed at fixing common issues that exist in other AI agents. You can run it at the terminal, call it from your app, or run it in the cloud. 

The agent introduces the concept of "acceptance criteria". This tells the agent how to check if the task has succeeded. Acceptance criteria should be objective, such as something that can be actually tested in a unit test or UI test. The agent should loop until the criteria is met. This ensures that the agent doesn't just create random code and then stop. 

The long term aim is to implement multi-agent support so as to fix issues like code deletion that is so rampant in other agents. It appears at this point that agents will always hallucinate, make mistakes and go beyond what is asked of them. A reviewer agent will revert obvious mistakes made by the original agent and attempt to steer the agent back on the right track.

## Development Environment Setup

**Add your OpenAI API Key by creating a `.env` file in the root directory**
```
OPENAI_API_KEY=your_key_here
```

This project uses VS Code Dev Containers to ensure a consistent development environment. **This is the required way to develop for this project.**

### Prerequisites




1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install [Visual Studio Code](https://code.visualstudio.com/)
3. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VS Code

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/nimble_agent.git
   cd nimble_agent
   ```

2. Start Docker Desktop

3. Open the project in VS Code:
   ```bash
   code .
   ```

4. Start the Dev Container:
   - When prompted "Folder contains a Dev Container configuration file. Reopen folder to develop in a container", click "Reopen in Container"
   - Or press `Cmd + Shift + P` (Mac) / `Ctrl + Shift + P` (Windows/Linux), type "Dev Containers: Reopen in Container"

VS Code will automatically:
- Build the container with Python 3.12 and Flutter
- Install all project dependencies
- Run setup.sh to configure the development environment
- Configure development tools and extensions

### Environment Variables

Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_key_here
```

### Development Tools Included

The dev container comes pre-configured with:
- Python 3.11
- Flutter (stable channel)
- Code formatting (Black, dart format)
- Linting (Ruff, Flutter lint)
- Type checking (Pyright)
- Auto-formatting on save
- Import sorting
- Debugging support
- IntelliCode AI assistance

### Development Workflow

#### Running Tests and Checks

The project includes a comprehensive CI script that runs all necessary checks. To test your changes, run:

```bash
./scripts/ci.sh
```

This script will:
- Run all tests with pytest
- Check code formatting with Black
- Run linting with Ruff
- Verify type checking with Pyright
- Check test coverage requirements
- Generate coverage reports

#### Common Commands

Inside the dev container:
```bash
# Run tests
pytest

# Format code
black .

# Run linting
ruff check .

# Run all checks
./scripts/ci.sh
```

### Troubleshooting

If you encounter issues:
1. Ensure Docker Desktop is running
2. Rebuild the container:
   - `Cmd/Ctrl + Shift + P`
   - Type "Dev Containers: Rebuild Container"
3. Verify Flutter installation:
   ```bash
   flutter doctor
   ```

### Stopping the Dev Container

1. Press `Cmd + Shift + P` (Mac) / `Ctrl + Shift + P` (Windows/Linux)
2. Type "Dev Containers: Reopen Folder Locally"
3. Press Enter