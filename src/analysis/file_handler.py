import pandas as pd
from pathlib import Path

def load_csv(path: str):
    """
    Load a CSV file and return its contents along with a summary.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists() or p.suffix.lower() != ".csv":
        raise FileNotFoundError(f"{p} is not a valid CSV")

    df = pd.read_csv(p)

    # Generate a lightweight summary of the data
    dtypes = {c: str(t) for c, t in df.dtypes.items()}
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    summary = {
        "path": str(p),                     
        "columns": df.columns.tolist(),
        "rows": len(df),
        "dtypes": dtypes,
        "numeric_cols": numeric_cols,
        "head": df.head(5).to_dict(orient="records"),
    }
    return df, summary
