# agentbee/core/file_io.py
import json
import subprocess
from pathlib import Path
from typing import List

# --- Constants for single-line comment scrubbing ---
COMMENT_PATTERNS = {
    '.py': ['#'], '.sh': ['#'], '.js': ['//'], '.ts': ['//'], '.java': ['//'], '.c': ['//'], 
    '.cpp': ['//'], '.h': ['//'], '.hpp': ['//'], '.go': ['//'], '.rs': ['//'], '.swift': ['//'],
    '.kt': ['//'], '.php': ['//', '#'], '.rb': ['#'], '.pl': ['#'], '.lua': ['--'], '.sql': ['--']
}

# --- NEW: Constants for multi-line comment scrubbing ---
MULTI_LINE_COMMENT_DELIMITERS = {
    # C-style, Java, JS, TS, Go, C#, Swift, etc.
    '.c': ('/*', '*/'), '.cpp': ('/*', '*/'), '.h': ('/*', '*/'), '.hpp': ('/*', '*/'),
    '.java': ('/*', '*/'), '.js': ('/*', '*/'), '.ts': ('/*', '*/'), '.go': ('/*', '*/'),
    '.cs': ('/*', '*/'), '.swift': ('/*', '*/'), '.php': ('/*', '*/'), '.rs': ('/*', '*/'),
    '.sql': ('/*', '*/'),
    # Python docstrings (treated as comments for scrubbing)
    '.py': [('"""', '"""'), ("'''", "'''")]
}


def accumulate_code(file_paths: List[Path], scrub_comments: bool) -> str:
    """Reads a list of files and accumulates their content into a single string."""
    code_accumulation = []
    print(f"📚 Accumulating code from {len(file_paths)} file(s)...")
    if scrub_comments:
        print("Scrubbing single-line and multi-line comments from code.")
    else:
        print("Including comments as per --no-scrub flag.")

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                code_accumulation.append(f"\n--- FILE: {file_path.as_posix()} ---\n")
                
                if scrub_comments:
                    file_ext = file_path.suffix.lower()
                    
                    # --- NEW: Multi-line comment scrubbing logic ---
                    ml_delims = MULTI_LINE_COMMENT_DELIMITERS.get(file_ext)
                    if ml_delims:
                        # Handle cases like Python with multiple delimiter types
                        delimiter_pairs = ml_delims if isinstance(ml_delims, list) else [ml_delims]
                        for start_delim, end_delim in delimiter_pairs:
                            while True:
                                start_index = content.find(start_delim)
                                if start_index == -1:
                                    break
                                end_index = content.find(end_delim, start_index + len(start_delim))
                                if end_index == -1:
                                    # Unclosed comment, stop processing this file to be safe
                                    break 
                                content = content[:start_index] + content[end_index + len(end_delim):]

                    # --- Existing single-line comment scrubbing logic ---
                    sl_markers = COMMENT_PATTERNS.get(file_ext, [])
                    if not sl_markers:
                        code_accumulation.append(content)
                        continue

                    lines = content.split('\n')
                    uncommented_lines = []
                    for line in lines:
                        stripped_line = line.strip()
                        # Check if the stripped line starts with any of the single-line comment markers
                        if any(stripped_line.startswith(marker) for marker in sl_markers):
                            continue
                        uncommented_lines.append(line)
                    code_accumulation.append("\n".join(uncommented_lines))

                else:
                    # If not scrubbing, append the original content
                    code_accumulation.append(content)
        except Exception as e:
            print(f"⚠️ Warning: Could not read file {file_path}: {e}")

    return "".join(code_accumulation)


def apply_code_changes(json_response_str: str, output_dir: Path):
    """Parses JSON and writes files to the output directory."""
    print(f"\n⚡ Applying code changes to directory: {output_dir}")
    try:
        files_to_create = json.loads(json_response_str)
        if not isinstance(files_to_create, list):
            raise ValueError("JSON response is not a list of files.")

        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for file_data in files_to_create:
            if "file_path" not in file_data or "code" not in file_data:
                print(f"⚠️ Warning: Skipping an entry due to missing 'file_path' or 'code': {file_data}")
                continue

            relative_path = Path(file_data["file_path"])
            code_content = file_data["code"]
            
            destination_path = (output_dir / relative_path).resolve()
            if output_dir.resolve() not in destination_path.parents:
                print(f"🚨 Security Error: Path '{relative_path}' attempts to write outside of output directory '{output_dir}'. Skipping.")
                continue

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            destination_path.write_text(code_content, encoding='utf-8')
            print(f"   ✅ Wrote: {destination_path}")
            count += 1
        print(f"\n--- Finished: Successfully created {count} file(s). ---")

    except json.JSONDecodeError:
        print("🚨 Error: Failed to decode JSON from the LLM response.")
        print("Raw response received:", json_response_str)
    except Exception as e:
        print(f"🚨 An unexpected error occurred during file creation: {e}")


def apply_patch(patch_content: str, root: Path) -> subprocess.CompletedProcess:
    """Applies a git patch to the repository, ignoring whitespace issues."""
    print("Applying patch...")
    return subprocess.run(
        ['git', 'apply', '--ignore-whitespace'],
        input=patch_content, text=True, cwd=root,
        capture_output=True
    )


def revert_patch(root: Path):
    """Reverts all uncommitted changes in the working directory."""
    print("⚠️ Reverting changes...")
    subprocess.run(['git', 'checkout', '--', '.'], cwd=root, check=True)