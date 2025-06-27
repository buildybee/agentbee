from langchain.prompts import ChatPromptTemplate,PromptTemplate

def get_assist_prompt():
    return  ChatPromptTemplate(
        [
            (
                "system",
                "You are an advanced AI code analysis and writing assistant. \n"
                "You have the a github source code each marked with its file path. \n"
                "User will provide instruction that will require code change like adding a new function, modifying existing function, etc.\n"
                "Output only the list of file path and complete code content in the following schema:\n"
                "{format_instructions} \n"
                "Code content with file path: \n"
                "{code_content} \n"
                "Also try to follow: \n"
                "1. Maximize the use of any exiting functions \n"
            ),
            (
                "human",
                "{query}"
            ),
        ]
    )

def fix_json_prompt():
    return PromptTemplate(
        template="fix the string so that it can parsed safely by any json library\n" 
        "only output the string without any further explanation: \n"
        "String is : {input}",
        input_variables=["input"]
    )