import json, textwrap
from .data_analyzer import file_handler, executor
from .reporter import answerer
from .prompts import builder
from .code_generator import llm_wrapper
from .utils.guard import looks_suspicious

MAX_RETRY = 3

def run_session(csv_path: str):
    _, summary = file_handler.load_csv(csv_path)  # df no longer needed on host
    history = []

    while True:
        question = input("\n📝 Ask a data question (or 'exit'): ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        error = None
        for attempt in range(1, MAX_RETRY + 1):
            msgs = builder.build_code_prompt(question, summary, error)
            code = llm_wrapper.chat(msgs)

            if looks_suspicious(code):
                error = "Code tries to build its own DataFrame or read the CSV."
                print("🚫  Guard rejected generated code – asking LLM to fix it.")
                continue 

            print(f"\nGenerated code (attempt {attempt}):\n{code}\n{'-'*40}")
            stdout, ret_obj, plots, error = executor.try_run(code, csv_path)

            if not error:
                # Short preview of structured output, if any
                if ret_obj is not None:
                    preview = json.dumps(ret_obj, ensure_ascii=False, indent=2)[:300]
                    print(f"🗂️  output_data preview:\n{textwrap.indent(preview, '   ')}")
                if plots:
                    print(f"🖼️  Plots saved: {plots}")

                # For the LLM’s narrative we pass stdout + ret_obj (stringified)
                combined_output = stdout
                if ret_obj is not None:
                    combined_output += "\n\noutput_data = " + json.dumps(ret_obj, ensure_ascii=False)

                nl_answer = answerer.answer(question, combined_output)
                print(f"🗨️  {nl_answer}")
                history.append((question, code, combined_output))
                break
            else:
                print(f"⚠️  Error:\n{textwrap.indent(error, '   ')}")
        else:
            print("❌ Failed after retries.")

if __name__ == "__main__":
    csv = input("Path to CSV: ").strip()
    run_session(csv)
