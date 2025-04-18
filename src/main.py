import json, textwrap, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .data_analyzer import file_handler, executor
from .reporter import answerer
from .prompts import builder
from .code_generator import llm_wrapper
from .utils import json_history as jh

MAX_RETRY = 3
session_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def run_session(csv_path: str):
    _, summary = file_handler.load_csv(csv_path)  # df no longer needed on host
    # -------- persistent history file per CSV --------
    h = hashlib.md5(str(csv_path).encode()).hexdigest()[:8]
    hist_path = Path("src/chat_history") / f"hist_{h}_{session_tag}.json"
    hist = jh.JSONHistory(hist_path)
    hist_logger = jh.make_logger(name_suffix=session_tag, level=jh.logging.DEBUG)

    jh.logger = hist_logger
    TAIL_N = 5

    while True:
        question = input("\n📝 Ask a data question (or 'exit'): ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        error = None
        # build memory blob
        memory_blob = "\n\n".join(
            f"Q: {r['question']}\n"
            f"Code: {r['code']}\n"
            f"Key output: {r['output']}\n"
            f"Explanation: {r['explain']}"
            for r in hist.tail(TAIL_N)
        )

        for attempt in range(1, MAX_RETRY + 1):
            msgs = builder.build_code_prompt(question, summary, memory_blob)
            if attempt == 1 or error is None:
                code = llm_wrapper.chat(msgs)
            else:
                dbg_msgs = builder.build_debug_prompt(
                    question, summary, error, memory_blob
                )
                code = llm_wrapper.chat(dbg_msgs)
            hist.log_prompt(msgs[-1]["content"])
            hist.log_response(code)

            print(f"\nGenerated code (attempt {attempt}):\n{code}\n{'-'*40}")
            stdout, ret_obj, plots, error = executor.try_run(code, csv_path)

            # always pre‑compute preview strings (empty if N/A)
            output_preview = (
                json.dumps(ret_obj, ensure_ascii=False) if ret_obj else ""
            )
            plots_preview = ", ".join(Path(p).name for p in plots) if plots else ""

            if not error:
                if output_preview:
                    print(f"🗂️  output_data preview:\n{textwrap.indent(output_preview, '   ')}")
                if plots:
                    print(f"🖼️  Plots saved: {plots}")

                # For the LLM’s narrative we pass stdout + ret_obj (stringified)
                combined_output = stdout
                if ret_obj is not None:
                    combined_output += "\n\noutput_data = " + json.dumps(ret_obj, ensure_ascii=False)

                nl_answer = answerer.answer(
                    question=question,
                    summary=summary,
                    code=code,              
                    output=combined_output,
                    history_blob=memory_blob,  
                )
                hist.log_response(nl_answer)
                print(f"🗨️  {nl_answer}")
                hist.append(
                     dict(
                         question=question,
                         code=code,
                         stdout=stdout,
                         output=output_preview,
                         plots=plots_preview,
                         explain=nl_answer,
                     )
                 )
                break
            else:
                print(f"⚠️  Error:\n{textwrap.indent(error, '   ')}")
        else:
            print("❌ Failed after retries.")

if __name__ == "__main__":
    csv = input("Path to CSV: ").strip()
    run_session(csv)
