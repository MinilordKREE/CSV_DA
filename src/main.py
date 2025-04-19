import json, textwrap, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .analysis import file_handler
from .analysis.sandbox import sandbox_runner
from .llm.prompts import builder
from .llm import llm_wrapper
from .history import json_history as jh

# Constants
# Maximum number of retries for code generation
MAX_RETRY = 3
session_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def run_session(csv_path: str):
    # Load the CSV and generate a summary for the data
    _, summary = file_handler.load_csv(csv_path)


    # Create the directory for storing chat history if it doesn't exist
    chat_history_dir = Path("src/history/chat_history")
    chat_history_dir.mkdir(parents=True, exist_ok=True)

    # Logger for the chat history
    h = hashlib.md5(str(csv_path).encode()).hexdigest()[:8]
    hist_path = chat_history_dir / f"hist_{h}_{session_tag}.json"
    hist = jh.JSONHistory(hist_path)
    hist_logger = jh.make_logger(name_suffix=session_tag, level=jh.logging.DEBUG)
    jh.logger = hist_logger

    TAIL_N = 5 # Number of recent entries for context

    # Main loop to accept user questions and interact with the system
    while True:
        question = input("\n📝 Ask a data question (or 'exit'): ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        error = None
        # Construct a memory blob containing recent Q&A pairs 
        # and code/excution information for context
        memory_blob = "\n\n".join(
            f"Q: {r['question']}\n"
            f"Code: {r['code']}\n"
            f"Key output: {r['output']}\n"
            f"Explanation: {r['explain']}"
            for r in hist.tail(TAIL_N)
        )

        # Main loop to accept user questions and interact with the system
        last_code = ""
        for attempt in range(1, MAX_RETRY + 1):
            # Generate code using the LLM
            if attempt == 1 or error is None:
                msgs = builder.build_code_prompt(question, summary, memory_blob)
            else:
                msgs = builder.build_debug_prompt(
                    question, summary, error, last_code, memory_blob
                )
            code = llm_wrapper.chat(msgs)
            last_code = code 


            print(f"\nGenerated code (attempt {attempt}):\n{code}\n{'-'*40}")
            # Run the generated code in a sandbox environment
            # and capture the output
            stdout, ret_obj, plots, error = sandbox_runner.try_run(code, csv_path)

            output_preview = (
                json.dumps(ret_obj, ensure_ascii=False) if ret_obj else ""
            )
            plots_preview = ", ".join(Path(p).name for p in plots) if plots else ""

            if not error:
                if output_preview:
                    print(f"🗂️  output_data preview:\n{textwrap.indent(output_preview, '   ')}")
                if plots:
                    print(f"🖼️  Plots saved: {plots}")

                combined_output = stdout
                if ret_obj is not None:
                    combined_output += "\n\noutput_data = " + json.dumps(ret_obj, ensure_ascii=False)


                # Generate a natural language answer of the query based on the code and output
                # history/and data information
                nl_answer = llm_wrapper.answer(
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
                print(f"Error:\n{textwrap.indent(error, '   ')}")
        else:
            print("Failed after retries.")

if __name__ == "__main__":
    csv = input("Path to CSV: ").strip()
    run_session(csv)
