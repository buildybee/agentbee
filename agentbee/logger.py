# agentbee/logger.py
import os
import json
import datetime
from pathlib import Path
from typing import Optional

# Define the log file path relative to the current working directory
LOG_FILE_PATH = Path.cwd() / ".bee.log"

def setup_logging(fresh: bool):
    """
    Prepares the logging session, deleting the old log if requested.
    """
    if fresh and LOG_FILE_PATH.exists():
        try:
            os.remove(LOG_FILE_PATH)
            print(f"🗑️  Removed old log file at {LOG_FILE_PATH}")
        except OSError as e:
            print(f"🚨 Error removing log file: {e}")

def log_output(
    accumulated_code: str,
    response_data: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Logs the accumulated code, API response, and any errors to the log file.
    """
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"\n--- LOG ENTRY: {timestamp} ---\n")

            if error_message:
                log_file.write(f"--- STATUS: ERROR ---\n")
                log_file.write(f"{error_message}\n")

            log_file.write("\n--- ACCUMULATED CODE ---\n")
            log_file.write(accumulated_code if accumulated_code.strip() else "No code was accumulated.\n")

            log_file.write("\n--- API RESPONSE ---\n")
            if response_data:
                # Try to format if it's a JSON string, otherwise write as is
                try:
                    parsed_json = json.loads(response_data)
                    log_file.write(json.dumps(parsed_json, indent=2))
                except (json.JSONDecodeError, TypeError):
                    log_file.write(response_data)
            else:
                log_file.write("No API response was generated or provided for logging.\n")

            log_file.write("\n--- END OF LOG ENTRY ---\n")
    except Exception as e:
        # Critical error if logging itself fails
        print(f"🚨 CRITICAL: Could not write to log file {LOG_FILE_PATH}: {e}")