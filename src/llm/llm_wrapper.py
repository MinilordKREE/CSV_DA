from typing import List
from .. import config
import re
from .prompts import builder
import openai

if config.MODEL_BACKEND == "openai":
    openai.api_key = config.OPENAI_API_KEY
else:  # huggingface
    # However, this is not implemented in this demo
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    _tokenizer = AutoTokenizer.from_pretrained(config.DEFAULT_HF_MODEL, token=config.HF_ACCESS_TOKEN)
    _model     = AutoModelForCausalLM.from_pretrained(config.DEFAULT_HF_MODEL, token=config.HF_ACCESS_TOKEN, device_map="auto")
    _pipe      = pipeline("text-generation", model=_model, tokenizer=_tokenizer)


# code is easily extracted due to the consistent formatting of the gpt output
FENCE = re.compile(r"```(?:python|sql)?\\s*([\\s\\S]*?)```", re.I)


def chat(messages: List[dict]) -> str:
    """
    Send a list of message dictionaries to the LLM backend and return the response content.
    """
    if config.MODEL_BACKEND == "openai":
        resp = openai.ChatCompletion.create(
            model=config.DEFAULT_OPENAI_MODEL,
            messages=messages,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_LLM_TOKENS,
        )
        return code_catch(resp["choices"][0]["message"]["content"])
    else:
        # Huggingface model handling is not implemented in this demo
        pass 

def code_catch(llm_out: str) -> str:
    """
    Extract code from markdown-style fenced blocks or strip stray backticks.
    """
    m = FENCE.search(llm_out)
    if m:
        return m.group(1).strip()
    return llm_out.replace("```", "").strip()

def answer(
    question: str,
    summary: dict,
    code: str,
    output: str,
    history_blob: str = "",
) -> str:
    """
    Generate a natural-language answer from the LLM using the provided context.
    """
    msgs = builder.build_answer_prompt(question, summary, code, output, history_blob)
    return chat(msgs)