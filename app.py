"""
app.py
------
Streamlit frontend for the Data-Intensive Systems assignment.

Features:
  - View records from SQL, NoSQL, or both (combined/deduplicated)
  - Keyword search across text columns
  - Edit a record by ID with Eager or Lazy replication
  - Replication log at the bottom of the page
"""

import time
import sqlite3
import threading
from datetime import datetime

import pandas as pd
import streamlit as st
from tinydb import TinyDB, Query

SQL_FILE   = "sql_database.db"
NOSQL_FILE = "nosql_database.json"

st.set_page_config(page_title="Sales Database Viewer", layout="wide")
st.title("Sales Database Viewer")

# ---- session state defaults ----------------------------------------------
if "replication_log" not in st.session_state:
    st.session_state.replication_log = []

# ---- helper: add a line to the log ----------------------------------------
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.replication_log.append(f"[{ts}] {msg}")

# ---- database helpers ----------------------------------------------------
def get_sql_connection():
    return sqlite3.connect(SQL_FILE)

def get_nosql_table():
    db = TinyDB(NOSQL_FILE)
    return db, db.table("sales")

def fetch_sql_all():
    conn = get_sql_connection()
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    return df

def fetch_nosql_all():
    db, table = get_nosql_table()
    records = table.all()
    db.close()
    if records:
        df = pd.DataFrame(records)
        # tinydb adds a doc_id; drop it if it got included as a column
        if "doc_id" in df.columns:
            df = df.drop(columns=["doc_id"])
        return df
    return pd.DataFrame()

def search_df(df, keyword):
    # search across all text columns (and the id column)
    if not keyword:
        return df
    keyword = keyword.lower()
    mask = df.apply(
        lambda col: col.astype(str).str.lower().str.contains(keyword, na=False)
    ).any(axis=1)
    return df[mask]

def get_sql_record(record_id):
    conn = get_sql_connection()
    df = pd.read_sql_query(
        "SELECT * FROM sales WHERE id = ?", conn, params=(record_id,)
    )
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

def get_nosql_record(record_id):
    db, table = get_nosql_table()
    Q = Query()
    results = table.search(Q.id == record_id)
    db.close()
    return results[0] if results else None

def update_sql(record_id, updates: dict):
    conn = get_sql_connection()
    cur  = conn.cursor()
    set_clause = ", ".join(f'"{k}" = ?' for k in updates)
    values     = list(updates.values()) + [record_id]
    cur.execute(f"UPDATE sales SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def update_nosql(record_id, updates: dict):
    db, table = get_nosql_table()
    Q = Query()
    table.update(updates, Q.id == record_id)
    db.close()

def insert_sql_record(record: dict):
    conn = get_sql_connection()
    cur  = conn.cursor()
    cols  = ", ".join(f'"{k}"' for k in record)
    placeholders = ", ".join("?" for _ in record)
    cur.execute(f"INSERT INTO sales ({cols}) VALUES ({placeholders})", list(record.values()))
    conn.commit()
    conn.close()

def insert_nosql_record(record: dict):
    db, table = get_nosql_table()
    table.insert(record)
    db.close()

def record_exists_sql(record_id):
    conn = get_sql_connection()
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM sales WHERE id = ? LIMIT 1", (record_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def record_exists_nosql(record_id):
    db, table = get_nosql_table()
    Q = Query()
    results = table.search(Q.id == record_id)
    db.close()
    return len(results) > 0

# ---- sidebar controls ----------------------------------------------------
st.sidebar.header("View Options")
view_mode = st.sidebar.selectbox(
    "Select database view",
    ["All Databases (Combined View)", "SQL Database Only", "NoSQL Database Only"]
)
keyword = st.sidebar.text_input("Search keyword", placeholder="e.g. New York or T20001001")

st.sidebar.markdown("---")
st.sidebar.header("Replication Settings")
replication_mode = st.sidebar.radio(
    "Replication protocol",
    ["Eager (Synchronous) Replication", "Lazy (Asynchronous) Replication"]
)

# ---- main table display --------------------------------------------------
st.subheader(view_mode)

if view_mode == "SQL Database Only":
    df_sql = fetch_sql_all()
    df_show = search_df(df_sql, keyword)
    st.write(f"Showing {len(df_show)} records from SQLite.")
    st.dataframe(df_show, use_container_width=True)

elif view_mode == "NoSQL Database Only":
    df_nosql = fetch_nosql_all()
    df_show  = search_df(df_nosql, keyword)
    st.write(f"Showing {len(df_show)} records from TinyDB.")
    st.dataframe(df_show, use_container_width=True)

else:
    # combined view: merge and deduplicate by id
    df_sql   = fetch_sql_all()
    df_nosql = fetch_nosql_all()

    if df_sql.empty and df_nosql.empty:
        st.warning("Both databases are empty. Run init_db.py first.")
        st.stop()

    # tag each with its source
    df_sql["Source"]   = "SQL"
    df_nosql["Source"] = "NoSQL"

    # find ids that appear in both so we can mark them
    sql_ids   = set(df_sql["id"].astype(str))
    nosql_ids = set(df_nosql["id"].astype(str))
    both_ids  = sql_ids & nosql_ids

    # keep all sql rows; for nosql, only add rows not already in sql
    nosql_only = df_nosql[~df_nosql["id"].astype(str).isin(sql_ids)].copy()
    combined   = pd.concat([df_sql, nosql_only], ignore_index=True)

    # update source label for replicated records
    combined.loc[combined["id"].astype(str).isin(both_ids), "Source"] = "Both (Replicated)"

    combined = search_df(combined, keyword)
    st.write(f"Showing {len(combined)} unique records (SQL + NoSQL merged, duplicates removed).")
    st.dataframe(combined, use_container_width=True)

# ---- edit / update section -----------------------------------------------
st.markdown("---")
st.subheader("Edit a Record")

record_id_input = st.number_input("Enter Record ID to edit", min_value=1, step=1, value=1)
load_btn        = st.button("Load Record")

if load_btn:
    in_sql   = record_exists_sql(record_id_input)
    in_nosql = record_exists_nosql(record_id_input)

    if not in_sql and not in_nosql:
        st.error(f"Record ID {record_id_input} not found in either database.")
    else:
        # load the record data for the form (prefer SQL, fall back to NoSQL)
        rec = get_sql_record(record_id_input) if in_sql else get_nosql_record(record_id_input)
        st.session_state["editing_record"]   = rec
        st.session_state["editing_id"]       = record_id_input
        st.session_state["editing_in_sql"]   = in_sql
        st.session_state["editing_in_nosql"] = in_nosql

if "editing_record" in st.session_state:
    rec     = st.session_state["editing_record"]
    rec_id  = st.session_state["editing_id"]
    in_sql  = st.session_state["editing_in_sql"]
    in_nosql= st.session_state["editing_in_nosql"]

    location_label = "SQL only" if (in_sql and not in_nosql) else \
                     "NoSQL only" if (in_nosql and not in_sql) else \
                     "Both (Replicated)"
    st.write(f"Editing ID **{rec_id}** — currently stored in: **{location_label}**")

    # let the user edit a few key fields (keep the form short for the demo)
    with st.form("edit_form"):
        new_name     = st.text_input("Customer Name",     value=str(rec.get("Customer_Name", "")))
        new_qty      = st.number_input("Quantity",        value=int(rec.get("Quantity", 1)), min_value=1)
        new_status   = st.selectbox(
            "Order Status",
            ["Completed", "Pending", "Cancelled", "Returned"],
            index=["Completed", "Pending", "Cancelled", "Returned"].index(
                str(rec.get("Order_Status", "Completed"))
            ) if str(rec.get("Order_Status", "Completed")) in ["Completed", "Pending", "Cancelled", "Returned"] else 0
        )
        new_rating   = st.slider("Customer Rating", 1.0, 5.0,
                                 float(rec.get("Customer_Rating", 3.0)), step=0.1)

        # option to replicate a single-database record to the other db
        replicate_across = False
        if in_sql and not in_nosql:
            replicate_across = st.checkbox("Also replicate this record to NoSQL database")
        elif in_nosql and not in_sql:
            replicate_across = st.checkbox("Also replicate this record to SQL database")

        save_btn = st.form_submit_button("Save Changes")

    if save_btn:
        updates = {
            "Customer_Name": new_name,
            "Quantity":      new_qty,
            "Order_Status":  new_status,
            "Customer_Rating": new_rating,
        }

        if in_sql and in_nosql:
            # -- replicated record: apply the chosen replication protocol --
            if replication_mode == "Eager (Synchronous) Replication":
                update_sql(rec_id, updates)
                update_nosql(rec_id, updates)
                log(f"Updated ID {rec_id} in SQL -> Eagerly replicated to NoSQL (synchronous)")
                st.success(f"Record {rec_id} updated in both SQL and NoSQL (Eager replication).")

            else:
                # lazy: update SQL first, show success, then update NoSQL after a delay
                update_sql(rec_id, updates)
                log(f"Updated ID {rec_id} in SQL (primary) [Lazy replication - NoSQL pending...]")
                st.success(f"Record {rec_id} updated in SQL (primary). Propagating to NoSQL replica...")

                # background thread simulates async propagation
                def lazy_replicate(rid, upd):
                    time.sleep(2)
                    update_nosql(rid, upd)
                    log(f"Lazy replication complete: ID {rid} propagated to NoSQL replica.")

                t = threading.Thread(target=lazy_replicate, args=(rec_id, updates), daemon=True)
                t.start()
                st.info("NoSQL replica will be updated in the background (simulated 2s delay).")

        elif in_sql and not in_nosql:
            # SQL-only record
            update_sql(rec_id, updates)
            log(f"Updated ID {rec_id} in SQL only.")
            if replicate_across:
                full_rec = get_sql_record(rec_id)
                insert_nosql_record(full_rec)
                log(f"Replicated ID {rec_id} from SQL to NoSQL (user-initiated).")
                st.success(f"Record {rec_id} updated in SQL and replicated to NoSQL.")
            else:
                st.success(f"Record {rec_id} updated in SQL.")

        else:
            # NoSQL-only record
            update_nosql(rec_id, updates)
            log(f"Updated ID {rec_id} in NoSQL only.")
            if replicate_across:
                full_rec = get_nosql_record(rec_id)
                insert_sql_record(full_rec)
                log(f"Replicated ID {rec_id} from NoSQL to SQL (user-initiated).")
                st.success(f"Record {rec_id} updated in NoSQL and replicated to SQL.")
            else:
                st.success(f"Record {rec_id} updated in NoSQL.")

        # clear editing state so the form resets
        for key in ["editing_record", "editing_id", "editing_in_sql", "editing_in_nosql"]:
            st.session_state.pop(key, None)

# ---- replication log section ---------------------------------------------
st.markdown("---")
st.subheader("Replication Log")

if st.session_state.replication_log:
    log_text = "\n".join(reversed(st.session_state.replication_log))
    st.text_area("Log (newest first)", value=log_text, height=180)
    if st.button("Clear log"):
        st.session_state.replication_log = []
        st.rerun()
else:
    st.write("No replication activity yet.")

