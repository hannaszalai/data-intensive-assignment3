"""
init_db.py
----------
Reads sales_data.csv, splits it into three equal parts, and loads:
  - Part 1 (rows 0..99)   -> SQL only
  - Part 2 (rows 100..199)-> NoSQL only
  - Part 3 (rows 200..299)-> Both SQL and NoSQL  (replicated data)
"""

import sqlite3
import os
import pandas as pd
from tinydb import TinyDB

CSV_FILE   = "sales_data.csv"
SQL_FILE   = "sql_database.db"
NOSQL_FILE = "nosql_database.json"

# ---- load the csv --------------------------------------------------------
df = pd.read_csv(CSV_FILE)

if "id" not in df.columns:
    df.insert(0, "id", range(1, len(df) + 1))

df = df.fillna("")

total = len(df)
third = total // 3

part1 = df.iloc[:third].reset_index(drop=True)        # SQL only
part2 = df.iloc[third:2*third].reset_index(drop=True)  # NoSQL only
part3 = df.iloc[2*third:].reset_index(drop=True)       # Both

# ---- reset / clear old databases ----------------------------------------
if os.path.exists(SQL_FILE):
    os.remove(SQL_FILE)
if os.path.exists(NOSQL_FILE):
    os.remove(NOSQL_FILE)

# ---- set up sqlite -------------------------------------------------------
conn = sqlite3.connect(SQL_FILE)
cur  = conn.cursor()

def sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "REAL"
    return "TEXT"

col_defs = ", ".join(
    f'"{col}" {sql_type(df[col].dtype)}' for col in df.columns
)
cur.execute(f"CREATE TABLE IF NOT EXISTS sales ({col_defs})")
conn.commit()

def insert_sql(rows_df):
    cols = ", ".join(f'"{c}"' for c in rows_df.columns)
    placeholders = ", ".join("?" for _ in rows_df.columns)
    for _, row in rows_df.iterrows():
        cur.execute(
            f"INSERT INTO sales ({cols}) VALUES ({placeholders})",
            tuple(row)
        )
    conn.commit()

# insert part 1 and part 3 into sql
insert_sql(part1)
insert_sql(part3)

conn.close()

# ---- set up tinydb -------------------------------------------------------
db = TinyDB(NOSQL_FILE)
table = db.table("sales")

def insert_nosql(rows_df):
    for _, row in rows_df.iterrows():
        table.insert(row.to_dict())

# insert part 2 and part 3 into nosql
insert_nosql(part2)
insert_nosql(part3)

db.close()

# ---- summary -------------------------------------------------------------
print("Database initialisation complete.")
print(f"  CSV rows total : {total}")
print(f"  SQL only       : {len(part1)} rows  (ids {part1['id'].min()} - {part1['id'].max()})")
print(f"  NoSQL only     : {len(part2)} rows  (ids {part2['id'].min()} - {part2['id'].max()})")
print(f"  Both (replicated): {len(part3)} rows  (ids {part3['id'].min()} - {part3['id'].max()})")
print(f"  SQL total rows : {len(part1) + len(part3)}")
print(f"  NoSQL total rows: {len(part2) + len(part3)}")

