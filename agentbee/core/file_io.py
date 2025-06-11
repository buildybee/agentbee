import json
import re
import subprocess
from pathlib import Path
from typing import List, Union, Dict, Any

COMMENT_PATTERNS = {
    '.py': ['#'], '.sh': ['#'], '.js': ['//'], '.ts': ['//'], '.java': ['//'], '.c': ['//'], 
    '.cpp': ['//'], '.h': ['//'], '.hpp': ['//'], '.go': ['//'], '.rs': ['//'], '.swift': ['//'],
    '.kt': ['//'], '.php': ['//', '#'], '.rb': ['#'], '.pl': ['#'], '.lua': ['--'], '.sql': ['--']
}

MULTI_LINE_COMMENT_DELIMITERS = {
    '.c': ('/*', '*/'), '.cpp': ('/*', '*/'), '.h': ('/*', '*/'), '.hpp': ('/*', '*/'),
    '.java': ('/*', '*/'), '.js': ('/*', '*/'), '.ts': ('/*', '*/'), '.go': ('/*', '*/'),
    '.cs': ('/*', '*/'), '.swift': ('/*', '*/'), '.php': ('/*', '*/'), '.rs': ('/*', '*/'),
    '.sql': ('/*', '*/'),
    '.py': [('"""', '"""'), ("'''", "'''")]
}

def extract_valid_json(response: str) -> Union[Dict, List]:
    """Extracts and validates JSON from LLM response with multiple fallback strategies."""
    try:
        parsed = json.loads(response)
        
        # Normalize to always return a list of file objects
        if isinstance(parsed, dict):
            if 'file_path' in parsed and 'code' in parsed:
                return [parsed]
            return [{
                "file_path": "response.json",
                "code": json.dumps(parsed, indent=2)
            }]
        elif isinstance(parsed, list):
            # Validate each item has required fields
            valid_files = []
            for item in parsed:
                if isinstance(item, dict) and 'file_path' in item and 'code' in item:
                    valid_files.append({
                        "file_path": str(item['file_path']),
                        "code": str(item['code'])
                    })
            return valid_files if valid_files else [{
                "file_path": "invalid_response.json",
                "code": response
            }]
        return [{
            "file_path": "response.txt",
            "code": response
        }]
    
    except json.JSONDecodeError:
        # Try extracting from markdown code block
        code_blocks = re.findall(r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            try:
                return extract_valid_json(code_blocks[0])
            except json.JSONDecodeError:
                pass
        
        # Final fallback
        return [{
            "file_path": "fallback_response.txt",
            "code": response
        }]

def apply_code_changes(json_response_str: str, output_dir: Path) -> List[str]:
    """Safely applies code changes from LLM response."""
    try:
        files_data = extract_valid_json(json_response_str)
        created_files = []

        output_dir.mkdir(parents=True, exist_ok=True)

        for file_data in files_data:
            file_path = file_data.get("file_path", "").strip()
            code_content = file_data.get("code", "")
            
            if not file_path:
                continue

            # Secure path handling
            dest_path = (output_dir / file_path.lstrip('/')).resolve()
            try:
                if not dest_path.is_relative_to(output_dir.resolve()):
                    print(f"🚨 Security: Skipping path outside output dir: {file_path}")
                    continue
            except RuntimeError:
                continue

            # Write file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(code_content, encoding='utf-8')
            created_files.append(str(dest_path))
            print(f"✓ Created: {dest_path}")

        print(f"\n🎉 Successfully created {len(created_files)} files")
        return created_files

    except Exception as e:
        print(f"🚨 Error applying changes: {e}")
        raise
    
def accumulate_code(file_paths: List[Path], scrub_comments: bool) -> str:
    """Accumulates code from multiple files, optionally scrubbing comments."""
    code_accumulation = []
    print(f"📚 Accumulating code from {len(file_paths)} file(s)...")
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                code_accumulation.append(f"\n--- FILE: {file_path.as_posix()} ---\n")
                
                if scrub_comments:
                    file_ext = file_path.suffix.lower()
                    
                    # Handle multi-line comments
                    ml_delims = MULTI_LINE_COMMENT_DELIMITERS.get(file_ext)
                    if ml_delims:
                        delimiter_pairs = ml_delims if isinstance(ml_delims, list) else [ml_delims]
                        for start_delim, end_delim in delimiter_pairs:
                            while True:
                                start_idx = content.find(start_delim)
                                if start_idx == -1:
                                    break
                                end_idx = content.find(end_delim, start_idx + len(start_delim))
                                if end_idx == -1:
                                    break 
                                content = content[:start_idx] + content[end_idx + len(end_delim):]

                    # Handle single-line comments
                    sl_markers = COMMENT_PATTERNS.get(file_ext, [])
                    if sl_markers:
                        lines = content.split('\n')
                        uncommented_lines = []
                        for line in lines:
                            stripped_line = line.strip()
                            if any(stripped_line.startswith(marker) for marker in sl_markers):
                                continue
                            uncommented_lines.append(line)
                        content = "\n".join(uncommented_lines)

                code_accumulation.append(content)
        except Exception as e:
            print(f"⚠️ Warning: Could not read file {file_path}: {e}")

    return "".join(code_accumulation)

def apply_patch(patch_content: str, root: Path) -> subprocess.CompletedProcess:
    """Applies a git patch to the codebase."""
    print("Applying patch...")
    return subprocess.run(
        ['git', 'apply', '--ignore-whitespace'],
        input=patch_content, text=True, cwd=root,
        capture_output=True
    )

def revert_patch(root: Path):
    """Reverts all changes in the git repository."""
    print("⚠️ Reverting changes...")
    subprocess.run(['git', 'checkout', '--', '.'], cwd=root, check=True)
    subprocess.run(['git', 'clean', '-fd'], cwd=root, check=True)