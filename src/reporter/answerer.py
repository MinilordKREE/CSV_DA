from ..prompts import builder
from ..code_generator import llm_wrapper

def answer(question: str, raw_output: str) -> str:
    msgs = builder.build_answer_prompt(question, raw_output)
    return llm_wrapper.chat(msgs)
