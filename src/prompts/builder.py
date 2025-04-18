from . import templates as T

def build_code_prompt(question: str, summary: dict, error: str | None = None):
    user_msg = (
        f"The dataframe has {summary['rows']} rows and columns {summary['columns']}. "
        f"First rows:\n{summary['head']}\n\n"
        f"Task: {question}\n"
        "Write code now."
    )
    if error:
        user_msg += "\n\n" + T.DEBUG_SUFFIX.format(error=error)


    return [
        {"role": "system", "content": T.SYSTEM_CODE},
        {"role": "user", "content": user_msg}
    ]

def build_answer_prompt(question: str, output: str):
    return [
        {"role": "system", "content": "You are an assistant who explains data insights clearly."},
        {"role": "user", "content": T.ANSWER_TEMPLATE.format(question=question, output=output)}
    ]
