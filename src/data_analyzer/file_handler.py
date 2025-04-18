import pandas as pd
from pathlib import Path

def load_csv(path: str):
    p = Path(path).expanduser().resolve()
    if not p.exists() or p.suffix.lower() != ".csv":
        raise FileNotFoundError(f"{p} is not a valid CSV")
    df = pd.read_csv(p)
    summary = {
        "columns": df.columns.tolist(),
        "rows": len(df),
        "head": df.head(5).to_dict(orient="records")
    }
    return df, summary
