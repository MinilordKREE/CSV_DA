from typing import List
from .. import config
import re
from .prompts import builder

if config.MODEL_BACKEND == "openai":
    import openai
#     client = OpenAI(
#     # This is the default and can be omitted
#     api_key=os.environ.get("OPENAI_API_KEY"),
# )
    openai.api_key = config.OPENAI_API_KEY
else:  # huggingface
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    _tokenizer = AutoTokenizer.from_pretrained(config.DEFAULT_HF_MODEL, token=config.HF_ACCESS_TOKEN)
    _model     = AutoModelForCausalLM.from_pretrained(config.DEFAULT_HF_MODEL, token=config.HF_ACCESS_TOKEN, device_map="auto")
    _pipe      = pipeline("text-generation", model=_model, tokenizer=_tokenizer)

# ---------- public helpers ----------
def chat(messages: List[dict]) -> str:
    """
    messages = [{role: "system"|"user"|"assistant", content: str}, ...]
    returns assistant_content
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
        # naive HF chat (single‑shot). Format system/msg → prompt string
        prompt = ""
        for m in messages:
            prompt += f"<|{m['role']}|>{m['content']}\n"
        gen = _pipe(prompt, max_new_tokens=512, do_sample=False)[0]["generated_text"]
        return gen[len(prompt):]  # crude split

FENCE = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.I)

def code_catch(llm_out: str) -> str:
    """
    Remove markdown fences; fall back to stripping stray back‑ticks.
    """
    m = FENCE.search(llm_out)
    if m:
        return m.group(1).strip()
    # fallback if the model didn't use fences at all
    return llm_out.replace("```", "").strip()

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
    return chat(msgs)