import os
import typer
from pathlib import Path
from typing_extensions import Annotated
from functools import partial
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAI
from langchain_ollama import ChatOllama

from . import config, logger
from .core import accumulator, file_io, llm_api, prompts, runner, parser

app = typer.Typer(help="🐝 AgentBee: An AI-powered code assistant.")

FreshOption = Annotated[bool, typer.Option("--fresh", help="Start with a fresh log file, deleting the old one.")]
NoScrubOption = Annotated[bool, typer.Option("--no-scrub", help="Include comments in the accumulated code.")]
PathOption = Annotated[Path, typer.Option("--path", help="Scan a specific relative path instead of using 'git ls-files'.")]


@app.callback()
def main_callback():
    pass

@app.command()
def accumulate(
    path: PathOption = None,
    no_scrub: NoScrubOption = False,
    fresh: FreshOption = False
):
    runnable = RunnableLambda(runner.accumulate)
    try:
        runnable_input = {"path":path,"no_scrub":no_scrub}
        accumulated_script = runnable.invoke(runnable_input)
        logger.setup_logging(fresh)
        logger.log_output(accumulated_script)
        print(f"\n✅ Saved accumulated code logged to {logger.LOG_FILE_PATH}")
    except Exception as e:
        print(f"🚨 Operation failed: {e}")
        logger.log_output("", error_message=str(e))
    return accumulated_script
    
@app.command()
def assist(
    instructions: Annotated[str, typer.Argument(help="Your specific instructions for the AI assistant.")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Directory to save generated files.")] = Path(".beecode.d"),
    path: PathOption = None,
    no_scrub: NoScrubOption = False,
    fresh: FreshOption = False  # Changed from FreshFlag to FreshOption
):
    
    logger.setup_logging(fresh)
    api_response = None
    accumulated_code = ""
    error_message_for_log = None
    
    try:
        cfg = config.load_config()
        if not all(cfg.values()):
            print("🚨 API configuration is incomplete. Please run 'agentbee config set --help'.")
            return

        # Create the runnable components
        coding_model = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, api_key=llm_api.get_api_key())
        local_model = ChatOllama(model="phi3.5:latest", temperature=0)
        assist_prompt = prompts.get_assist_prompt()
        code_parser = parser.get_scripts_list_parser()        
        fix_json_prompt = prompts.fix_json_prompt()
        code_accumulator = RunnableLambda(runner.accumulate)
        model_logger = RunnableLambda(runner.log_model_output)
        markdown_cleaner = RunnableLambda(runner.clean_markdown_json)
        script_saver = RunnableLambda(runner.save_script)    

        # The main parsing chain that takes the model's raw string output
        code_parser_chain = markdown_cleaner | code_parser
        
        # The fallback "fixer" chain for when the main parser fails
        json_fixer_chain = (
            RunnableLambda(lambda x: print("🔴 Code Parsing failed. Trying to fix with local model..."))
            | RunnableLambda(lambda x: {"input": x})  # Wrap the faulty string for the prompt
             | fix_json_prompt
             | local_model
             | StrOutputParser()
             | markdown_cleaner
             | code_parser
        )
        
        # Create a resilient parser by attaching the fallback
        code_parser_with_fallback = code_parser_chain.with_fallbacks(
            fallbacks=[json_fixer_chain],
        )

        # Create a pre-configured formatter using partial
        data_formatter = RunnableLambda(
            partial(runner.format_for_prompt, 
                   instructions=instructions,
                   format_instructions=code_parser.get_format_instructions())
        )

        # Assemble the full chain
        assist_chain = (
            code_accumulator 
            | data_formatter 
            | assist_prompt 
            | coding_model 
            | model_logger 
            | code_parser_with_fallback # Use the parser with the self-healing fallback
            | script_saver
        )
        
        # Prepare input for the chain
        runnable_input = {
            "path": path,
            "no_scrub": no_scrub,
            "instructions": instructions
        }
        
        # Execute the chain
        api_response = assist_chain.invoke(runnable_input)
        
        print(f"\n✅ Code generation completed and saved")

    except Exception as e:
        error_message_for_log = str(e)
        print(f"🚨 Operation failed: {e}")
    # finally:
    #     logger.log_output(accumulated_code, response_data=api_response, error_message=error_message_for_log)

@app.command()
def auto(
    test_script: Annotated[Path, typer.Option("--test", help="Path to the shell script for verification.")],
    max_iterations: Annotated[int, typer.Option("--max-iterations", help="Maximum number of attempts.")] = 5,
    fresh: FreshOption = False
):
    pass

@app.command("show")
def show_config():
    
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

@app.command()
def config_set(
    api_key: Annotated[str, typer.Option(help="Your LLM API key.")] = "",
    base_url: Annotated[str, typer.Option(help="The base URL of the LLM API.")] = "",
    model: Annotated[str, typer.Option(help="The LLM model to use.")] = "",
):
    """Sets the configuration for AgentBee."""
    # Prompt for missing configurations
    if not api_key:
        api_key = typer.prompt("Please enter your LLM API key")
    if not base_url:
        base_url = typer.prompt("Please enter the LLM API base URL")
    if not model:
        model = typer.prompt("Please enter the LLM model name")

    config.save_config(api_key, base_url, model)

if __name__ == "__main__":
    app()