from typing import List
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel,Field, RootModel



class CodeOutput(BaseModel):
    file_path: str = Field(description="The full path to the file where the code should be saved.")
    code_content: str = Field(
        description="The complete source code. It MUST be a single, JSON-safe string. All special characters, including quotes, backslashes, and newlines, must be properly escaped (e.g., \\n for newlines, \\\" for double quotes)."
    )

class CodeOutputRootList(RootModel[List[CodeOutput]]):
    """A list of code outputs that can be the root of a JSON document."""
    pass

def get_scripts_list_parser():
    """Returns a PydanticOutputParser configured for a direct list of scripts."""
    return PydanticOutputParser(pydantic_object=CodeOutputRootList)