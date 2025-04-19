from . import templates as T
import json

def _schema_from_summary(summary: dict) -> dict:
    """
    Convert the data summary into the JSON structure expected by the LLM.
    """
    return {
        "n_rows": summary["rows"],
        "columns": summary["columns"],
        "dtypes": summary["dtypes"],
        "numeric_cols": summary["numeric_cols"],
        "head": summary["head"],  # First 5 rows for reference
    }

def build_code_prompt(
    question: str, 
    summary: dict, 
    memory: str = ""
) -> list[dict]:
    """
    Create a prompt for generating code based on the provided question, summary, and memory.
    """
    schema = _schema_from_summary(summary)  
    code_msg = ""
    if memory:
        code_msg += ( "Here is the conversation/code history you must take into account:\n"
                    f"{memory}\n\n"
        )
    code_msg += (
        "You are given the following DataFrame summary (as JSON):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"**Task:** {question}\n\n"
        "Write Python code now."
    )

    return [
        {"role": "system", "content": T.SYSTEM_CODE},
        {"role": "user",   "content": code_msg},
    ]

def build_debug_prompt(
    question: str,
    summary: dict,
    error: str,
    previous_code: str,
    memory: str = ""
) -> list[dict]:
    """
    Create a debug prompt using the error message, question, summary, and memory context.
    """
    schema = _schema_from_summary(summary)
    debug_msg = ""
    if memory:
        debug_msg += ("Conversation/code history:\n" + memory + "\n\n")
    debug_msg += (
        "Here is the code that just failed:\n"
        f"```python\n{previous_code}\n```\n\n"
        "The traceback was:\n"
        f"{error}\n\n"
        "You are given the following DataFrame summary (as JSON):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"**Task (retry):** {question}\n\n"
        "Fix the code and reply with **ONLY executable Python**.\n"
        "**If the traceback shows a missing‑package or NameError for an undefined "
        "module/alias, prepend the appropriate `import …` statement(s) at the very top "
        "of your code.**"
    )

    return [
        {"role": "system", "content": T.SYSTEM_CODE},
        {"role": "user",   "content": debug_msg},
    ]

def build_answer_prompt(
    question: str,
    summary: dict,
    code: str,
    output: str,
    history_blob: str = "",
) -> list[dict]:
    """
    Construct a full-context prompt for answering the given question.
    """
    schema = _schema_from_summary(summary)
    parts = []
    if history_blob:
        parts.append("Conversation context:\n" + history_blob)

    parts.append(
        "You are given the following DataFrame summary (as JSON):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        + T.ANSWER_TEMPLATE.format(question=question, code=code, output=output)
    )

    return [
        {"role": "system", "content": "You are an assistant who explains data insights clearly."},
        {"role": "user",   "content": "\n\n".join(parts)},
    ]

def build_sql_prompt(question: str, summary: dict, memory="") -> list[dict]:
    schema = _schema_from_summary(summary)
    msg = (
        (f"Conversation context:\n{memory}\n\n" if memory else "") +
        "Table schema (JSON):\n" + json.dumps(schema, indent=2) +
        f"\n\n**Task:** {question}\n\nWrite SQL now."
    )
    return [{"role": "system", "content": T.SYSTEM_SQL},
            {"role": "user", "content": msg}]

def build_sql_debug_prompt(question, summary, error, prev_sql, memory="") -> list[dict]:
    schema = _schema_from_summary(summary)
    msg = (
        (f"History:\n{memory}\n\n" if memory else "") +
        "The previous SQL was:\n```\n" + prev_sql + "\n```\n\n"
        "Error:\n" + error + "\n\n" +
        "Schema:\n" + json.dumps(schema, indent=2) +
        f"\n\n**Task (retry):** {question}\n\nFix the SQL and return ONLY SQL."
    )
    return [{"role": "system", "content": T.SYSTEM_SQL},
            {"role": "user", "content": msg}]
