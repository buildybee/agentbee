import os
import typer
from pathlib import Path
from typing_extensions import Annotated

from . import config, contexts, logger
from .core import accumulator, file_io, llm_api, runner

app = typer.Typer(help="🐝 AgentBee: An AI-powered code assistant.")

# --- Shared Options ---
FreshOption = Annotated[bool, typer.Option("--fresh", help="Start with a fresh log file, deleting the old one.")]
NoScrubOption = Annotated[bool, typer.Option("--no-scrub", help="Include comments in the accumulated code.")]
PathOption = Annotated[Path, typer.Option("--path", help="Scan a specific relative path instead of using 'git ls-files'.")]


@app.callback()
def main_callback():
    """Manage global state and configurations."""
    pass

@app.command()
def accumulate(
    path: PathOption = None,
    no_scrub: NoScrubOption = False,
    fresh: FreshOption = False
):
    """Gathers code from files and saves it to a log without calling an API."""
    logger.setup_logging(fresh)
    try:
        project_root = accumulator.get_project_root()
        file_paths = accumulator.get_file_paths(project_root, path)
        accumulated_code = file_io.accumulate_code(file_paths, scrub_comments=not no_scrub)
        logger.log_output(accumulated_code)
        print(f"\n✅ Accumulated code from {len(file_paths)} files logged to {logger.LOG_FILE_PATH}")
    except Exception as e:
        print(f"🚨 Operation failed: {e}")
        logger.log_output("", error_message=str(e))

@app.command()
def assist(
    instructions: Annotated[str, typer.Argument(help="Your specific instructions for the AI assistant.")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Directory to save generated files.")] = Path(".beecode.d"),
    path: PathOption = None,
    no_scrub: NoScrubOption = False,
    fresh: FreshOption = False  # Changed from FreshFlag to FreshOption
):
    """Assist with code generation or modification using AI."""
    logger.setup_logging(fresh)
    api_response = None
    accumulated_code = ""
    error_message_for_log = None
    
    try:
        cfg = config.load_config()
        if not all(cfg.values()):
            print("🚨 API configuration is incomplete. Please run 'agentbee config set --help'.")
            return

        project_root = accumulator.get_project_root()
        file_paths = accumulator.get_file_paths(project_root, path)
        accumulated_code = file_io.accumulate_code(file_paths, scrub_comments=not no_scrub)

        if not accumulated_code.strip():
            print("No code accumulated. Exiting.")
            return

        system_prompt = f"{contexts.ASSIST_CONTEXT}\n\n--- CURRENT CODE CONTEXT ---\n{accumulated_code}"
        user_prompt = instructions

        print("\n🤖 Sending request to LLM API...")
        api_response = llm_api.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config=cfg
        )

        file_io.apply_code_changes(api_response, output)

    except Exception as e:
        error_message_for_log = str(e)
        print(f"🚨 Operation failed: {e}")
    finally:
        logger.log_output(accumulated_code, response_data=api_response, error_message=error_message_for_log)

@app.command()
def auto(
    test_script: Annotated[Path, typer.Option("--test", help="Path to the shell script for verification.")],
    max_iterations: Annotated[int, typer.Option("--max-iterations", help="Maximum number of attempts.")] = 5,
    fresh: FreshOption = False
):
    """Automatically fix code using a test script as verification."""
    logger.setup_logging(fresh)
    if not test_script.exists():
        print(f"🚨 Error: Test script not found at '{test_script}'")
        return

    try:
        runner.run_auto_workflow(
            test_script_path=test_script,
            max_iterations=max_iterations,
        )
    except Exception as e:
        print(f"🚨 A critical error occurred in the auto workflow: {e}")
        logger.log_output("", error_message=f"Auto workflow failed: {e}")

@app.command("show")
def show_config():
    """Displays the current configuration."""
    cfg = config.load_config()
    if not cfg or not any(cfg.values()):
        print(f"No configuration found. Please run 'agentbee config set'.")
        print(f"(Expected at: {config.get_config_path()})")
    else:
        print(f"Current configuration from {config.get_config_path()}:")
        if cfg.get('llm_api_key'):
            key = cfg['llm_api_key']
            cfg['llm_api_key'] = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "********"
        
        for key, value in cfg.items():
            print(f"  - {key}: {value}")

if __name__ == "__main__":
    app()