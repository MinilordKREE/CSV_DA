from ..prompts import builder
from ..code_generator import llm_wrapper

def answer(
    question: str,
    summary: dict,
    code: str,
    output: str,
    history_blob: str = "",
) -> str:
    """
    Build the full-context answer prompt and get the LLM's natural-language reply.
    """
    msgs = builder.build_answer_prompt(
        question, summary, code, output, history_blob
    )

    print("### ANSWER PROMPT ####\n", msgs[1]["content"], "\n#####################")

    return llm_wrapper.chat(msgs)