import subprocess
from pathlib import Path

from .. import config, contexts, logger
from . import accumulator, file_io, llm_api

def run_auto_workflow(test_script_path: Path, max_iterations: int):
    cfg = config.load_config()
    if not all(cfg.values()):
        print("🚨 API configuration is incomplete. Please run 'agentbee config set --help'.")
        return

    project_root = accumulator.get_project_root()
    
    print("--- 🐝 Starting Auto-Fix Workflow ---")
    
    file_paths = accumulator.get_file_paths(project_root, path_option=None)
    initial_code = file_io.accumulate_code(file_paths, scrub_comments=False)
    
    if not initial_code.strip():
        print("No code found to process. Exiting.")
        return

    test_script_content = test_script_path.read_text()

    current_user_prompt = initial_code
    error_output = ""

    for i in range(max_iterations):
        iteration = i + 1
        print(f"\n--- 🔄 Iteration {iteration}/{max_iterations} ---")

        if iteration == 1:
            system_prompt = contexts.AUTO_CONTEXT_INITIAL
        else:
            system_prompt = contexts.AUTO_CONTEXT_RETRY.format(
                test_script_content=test_script_content,
                test_output=error_output
            )
        
        patch_content = llm_api.call_llm(
            system_prompt=system_prompt,
            user_prompt=current_user_prompt,
            config=cfg,
        )
        logger.log_output(current_user_prompt, patch_content)

        if not patch_content or not "--- a/" in patch_content:
             print("⚠️ LLM did not return a valid patch. Skipping iteration.")
             error_output = "LLM did not return a valid patch."
             continue

        patch_result = file_io.apply_patch(patch_content, project_root)
        if patch_result.returncode != 0:
            print("🚨 Failed to apply the patch:")
            print(patch_result.stderr)
            error_output = f"The generated patch could not be applied:\n{patch_result.stderr}"
            continue

        print(f"🔬 Running verification script: {test_script_path}")
        test_result = subprocess.run(
            [test_script_path.as_posix()],
            shell=True, capture_output=True, text=True, cwd=project_root
        )

        if test_result.returncode == 0:
            print("\n--- ✅ SUCCESS! ---")
            print("Verification test passed. The patch has been successfully applied.")
            logger.log_output("Final state", f"SUCCESS on iteration {iteration}.\nPatch applied:\n{patch_content}")
            return
        else:
            print(f"--- ❌ TEST FAILED (Iteration {iteration}) ---")
            error_output = f"STDOUT:\n{test_result.stdout}\n\nSTDERR:\n{test_result.stderr}"
            print(error_output)
            file_io.revert_patch(project_root)
            current_user_prompt = error_output

    print(f"\n--- 🛑 FAILED ---")
    print(f"Could not fix the code within the {max_iterations} iteration limit.")