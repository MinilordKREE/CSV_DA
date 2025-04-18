import textwrap
from .data_analyzer import file_handler, executor
from .code_generator import llm_wrapper
from .reporter import answerer
from .prompts import builder

MAX_RETRY = 3

def run_session(csv_path: str):
    df, summary = file_handler.load_csv(csv_path)
    history = []  # (question, code, output) triples

    while True:
        question = input("\n📝 Ask a data question (or 'exit'): ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        error = None
        for attempt in range(1, MAX_RETRY+1):
            msgs = builder.build_code_prompt(question, summary, error)
            code = llm_wrapper.chat(msgs)

            print(f"\nGenerated code (attempt {attempt}):\n{code}\n{'-'*40}")
            output, error = executor.try_run(code, df)

            if not error:
                print(f"✅ Output:\n{textwrap.indent(output, '   ')}")
                nl_answer = answerer.answer(question, output)
                print(f"🗨️  {nl_answer}")
                history.append((question, code, output))
                break
            else:
                print(f"⚠️  Error:\n{textwrap.indent(error, '   ')}")
        else:
            print("❌ Failed after retries.")

if __name__ == "__main__":
    csv = input("Path to CSV: ").strip()
    run_session(csv)
