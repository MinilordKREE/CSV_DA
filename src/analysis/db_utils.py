from pathlib import Path
import sqlite3, pandas as pd

def csv_to_sqlite(df: pd.DataFrame, csv_path: str) -> Path:
    """
    Persist the DataFrame as a table called  data  in <csv>.db
    and return the DB path.
    """
    db_path = Path(csv_path).with_suffix(".db")
    con = sqlite3.connect(db_path)
    df.to_sql("data", con, if_exists="replace", index=False)
    con.close()
    return db_path
