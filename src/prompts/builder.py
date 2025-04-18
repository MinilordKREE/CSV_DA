from . import templates as T
import json

def build_code_prompt(question: str, summary: dict, error: str | None = None):
    schema = {
        "n_rows": summary["rows"],
        "columns": summary["columns"],
        "dtypes": summary["dtypes"],
        "numeric_cols": summary["numeric_cols"],
        "head": summary["head"],          # first 5 rows so the LLM “sees” examples
    }

    user_msg = (
        "You are given the following DataFrame summary (as JSON):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"**Task:** {question}\n\n"
        "Write Python code now."
    )
    if error:
        user_msg += T.DEBUG_SUFFIX.format(error=error)

    return [
        {"role": "system", "content": T.SYSTEM_CODE},
        {"role": "user",   "content": user_msg},
    ]

def build_answer_prompt(question: str, output: str):
    return [
        {"role": "system", "content": "You are an assistant who explains data insights clearly."},
        {"role": "user",   "content": T.ANSWER_TEMPLATE.format(question=question, output=output)},
    ]
