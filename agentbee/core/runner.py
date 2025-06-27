import subprocess
from pathlib import Path
from langchain_core.runnables import RunnableLambda
from pathlib import Path

from .. import config, logger
from . import accumulator, file_io, llm_api, parser
from typing import List,Dict

def accumulate(runnable_input: dict):
    path = runnable_input.get("path",None)
    no_scrub = runnable_input.get("no_scrub", False)
    project_root = accumulator.get_project_root()
    file_paths = accumulator.get_file_paths(project_root, path)
    accumulated_code = file_io.accumulate_code(file_paths, scrub_comments=not no_scrub)
    print(f"\n✅ Accumulated code from {len(file_paths)} files")
    return(accumulated_code)

def format_for_prompt(accumulated_code, instructions, format_instructions):
    """Transform accumulated code and instructions into prompt format"""
    return {
        "code_content": accumulated_code,
        "query": instructions,
        "format_instructions": format_instructions
    }

def log_model_output(model_response: str) -> str:
    """A utility to print the model's raw output for debugging."""
    print(f"\n🤖 Model Output:")
    print("=" * 50)
    print(model_response)
    print("=" * 50)
    return model_response

def clean_markdown_json(model_response: str) -> str:
    """
    Safely clean JSON from markdown code blocks and extract scripts array.
    This function avoids using regex to prevent corrupting the inner code.
    """
    import json
    
    # Copy the response to avoid modifying the original
    cleaned_response = model_response.strip()
    
    # Safely remove the prefix and suffix
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[len("```json"):].strip()
    elif cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[len("```"):].strip()
        
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-len("```")].strip()
        
    # Now that the outer markdown is stripped, we can process the JSON
    try:
        parsed = json.loads(cleaned_response)
        if isinstance(parsed, dict) and 'scripts' in parsed:
            return json.dumps(parsed['scripts'])
        else:
            return cleaned_response
    except json.JSONDecodeError:
        return cleaned_response

def save_script(parsed_response):
    """
    Save parsed scripts to files, ensuring paths are correctly resolved
    relative to the project root.
    """
    project_root = accumulator.get_project_root()
    
    for script in parsed_response.root:
        model_path = Path(script.file_path)
        
        # Determine the correct relative path
        if model_path.is_absolute():
            # If the path from the model is absolute, make it relative to the project root
            try:
                relative_path = model_path.relative_to(project_root)
            except ValueError:
                # Fallback for absolute paths outside the project, use only the name
                relative_path = model_path.name
        else:
            # If the path is already relative, use it as is
            relative_path = model_path

        # The save function constructs the full path inside .beecode.d
        file_io.save_code_to_beecode(
            Path(relative_path),
            script.code_content
        )
    return parsed_response