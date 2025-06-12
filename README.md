# AgentBee: AI-Powered Code Assistant

AgentBee is an AI-powered code assistant designed to help you analyze, understand, and modify your code more efficiently. It leverages large language models (LLMs) to provide intelligent suggestions, automate code modifications, and streamline your development workflow.

## Features

*   **Code Accumulation:** Gathers code from your project, either using `git ls-files` or a specified path, preparing it for analysis by the LLM.
*   **AI Assistance:** Provides a command-line interface to send code snippets and instructions to the LLM, receiving back suggested code changes.
*   **Automated Code Modification:** Applies suggested changes to your codebase automatically.
*   **Test-Driven Workflow:** Integrates with your existing test scripts to verify the correctness of changes.
*   **Configuration:** Easily configure API keys, base URLs, and models used by the LLM.
*   **Logging:** Keeps a detailed log of all interactions and changes made, enabling easy review and debugging.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/buildybee/agentbee.git
cd agentbee
```

### 2. Installation

It is highly recommended to use a virtual environment. Then, install the dependencies using pip:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows
pip install -e .
```

### 3. Configuration

Before using AgentBee, you need to configure your API credentials. Run the following command and provide the requested information:

```bash
agentbee config-set
```

You'll be prompted to enter your LLM API key, base URL, and model name.  AgentBee stores this configuration in `~/.agentbee/config.ini`.

### 4. Usage

#### Accumulate Code

To accumulate code from your project, run:

```bash
agentbee accumulate
```

This will gather all files tracked by git (or a specified path via `--path`) and log them to `.bee.log`.

#### Assist with Code Modifications

To get assistance with a specific task, use the `assist` command:

```bash
agentbee assist "Refactor the user authentication module to use JWTs."
```

This will send your instructions and the accumulated code to the LLM, and save the changes to the `.beecode.d` directory.

#### Automated Workflow(WIP)

To run an automated workflow with a test script, use the `auto` command:

```bash
agentbee auto --test tests/integration_test.sh --max-iterations 3
```

This will run the specified test script, and if it fails, it will use the LLM to attempt to fix the code and re-run the test script, up to the specified number of iterations.

#### View Configuration

To view the current configuration, use the `show` command:

```bash
agentbee show
```

### Options

*   `--fresh`: Start with a fresh log file, deleting the old one.
*   `--no-scrub`: Include comments in the accumulated code.
*   `--path`: Scan a specific relative path instead of using `git ls-files`.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to discuss potential improvements.

## License

This project is licensed under the [MIT License](LICENSE).
