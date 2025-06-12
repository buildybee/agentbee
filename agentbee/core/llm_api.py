from openai import OpenAI
from typing import Dict
import json

def call_llm(
    system_prompt: str,
    user_prompt: str,
    config: Dict[str, str]
) -> str:
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

        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=messages,
            response_format={"type": "json_object"},
        )
        
        response_content = response.choices[0].message.content
        print("LLM response:\n {}".format(response_content))
        
        # Validate JSON structure
        parsed = json.loads(response_content)
        if not isinstance(parsed, (list, dict)):
            raise ValueError("Response is not a JSON array or object")
        
        return response_content

    except json.JSONDecodeError as e:
        print(f"🚨 JSON Error: {e}\nAttempting to fix response...")
        # Basic JSON repair attempt
        fixed = response_content.replace('\\"', '"').replace('\n', '\\n')
        return json.dumps([{"file_path": "response.json", "code": fixed}])
    except Exception as e:
        print(f"🚨 API Error: {e}")
        raise