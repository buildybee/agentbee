# agentbee/core/llm_api.py

from openai import OpenAI
from typing import Dict

def call_llm(
    system_prompt: str,
    user_prompt: str,
    config: Dict[str, str]
) -> str:
    """
    Calls the specified LLM with the given prompts and configuration.

    Args:
        system_prompt: The system-level instructions for the AI.
        user_prompt: The user-provided prompt, typically containing the code.
        config: A dictionary with 'llm_api_key', 'llm_base_url', and 'llm_model'.
    """
    try:
        client = OpenAI(
            api_key=config['llm_api_key'],
            base_url=config['llm_base_url']
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        print(f"🤖 Calling model '{config['llm_model']}'...")

        # SIMPLIFIED: Removed the response_format parameter from the call.
        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=messages
        )
        
        response_content = response.choices[0].message.content
        return response_content

    except Exception as e:
        print(f"🚨 An error occurred during the LLM API call: {e}")
        raise