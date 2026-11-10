
# Data-Intensive Systems - Assignment 3

## Hanna Szalai

A small Python application that demonstrates how data can be split and replicated across a SQL database (SQLite) and a NoSQL document store (TinyDB), with a Streamlit web interface for browsing, searching, and editing records.

---

## Project Structure

```
data-intensive-assignment3/
├── sales_data.csv           # source dataset (300 rows of sales transactions)
├── generate_data.py         # one-off helper that creates sales_data.csv
├── init_db.py               # splits the CSV and loads it into the two databases
├── app.py                   # Streamlit web application
├── requirements.txt         # Python dependencies
├── sql_database.db          # created by init_db.py (SQLite)
├── nosql_database.json      # created by init_db.py (TinyDB)
└── README.md
```

---

## Databases Used

| Database | Technology | File |
|----------|-----------|------|
| SQL      | SQLite (`sqlite3` stdlib) | `sql_database.db` |
| NoSQL    | TinyDB (`tinydb`) | `nosql_database.json` |

SQLite is a relational database that stores rows in a table with strict column types.  
TinyDB is a lightweight document store where each record is a JSON object

---

## Data Split (1/3 Rule)

The 300-row CSV is divided into three equal parts of 100 rows each:

| Partition | Row IDs | Stored in |
|-----------|---------|-----------|
| Part 1    | 1 – 100   | SQL only |
| Part 2    | 101 – 200 | NoSQL only |
| Part 3    | 201 – 300 | **Both** (replicated data) |

This means:
- SQL holds 200 rows total (Part 1 + Part 3).
- NoSQL holds 200 rows total (Part 2 + Part 3).
- Part 3 is the overlapping replicated set used to demonstrate replication protocols.

---

## Setup & Installation

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate the dataset (only needed once)

```bash
python generate_data.py
```

This creates `sales_data.csv` with 300 realistic sales records.

### 3. Initialise the databases

```bash
python init_db.py
```

This clears any old database files and re-loads them from scratch. Expected output:

```
Database initialisation complete.
  CSV rows total : 300
  SQL only       : 100 rows  (ids 1 - 100)
  NoSQL only     : 100 rows  (ids 101 - 200)
  Both (replicated): 100 rows  (ids 201 - 300)
  SQL total rows : 200
  NoSQL total rows: 200
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

## Application Features

### View Modes (sidebar dropdown)

- **SQL Database Only** – queries only SQLite and shows those records.
- **NoSQL Database Only** – queries only TinyDB and shows those records.
- **All Databases (Combined View)** – merges both sources, deduplicates by record ID, and adds a `Source` column showing `SQL`, `NoSQL`, or `Both (Replicated)`.

### Search

Type any keyword in the sidebar search box to filter records across all text columns (customer name, city, product name, order status, etc.) or by record ID.

### Edit a Record

1. Enter a record ID in the "Edit a Record" section and click **Load Record**.
2. Modify the editable fields in the form.
3. Click **Save Changes**.

If the record exists in only one database, there is an option to also replicate it to the other database (user-initiated replication).

### Replication Protocol

Select the protocol with the radio button in the sidebar:

**Eager (Synchronous) Replication**  
Both SQL and NoSQL are updated in the same operation before the success message is shown. Used for replicated records (IDs 201–300).

**Lazy (Asynchronous) Replication**  
SQL (primary) is updated first and the success message is shown immediately. The NoSQL replica is updated after a simulated 2-second delay in a background thread. A log entry confirms when the replica is done.

### Replication Log

A text area at the bottom of the page records every update with a timestamp and a description of what was replicated and how. The log can be cleared with the **Clear log** button.

---

## Notes

- Re-running `init_db.py` at any time resets both databases to their original state.
- `generate_data.py` only needs to be run once; `sales_data.csv` can be committed to version control.
- TinyDB requires no background server — it reads and writes a plain JSON file.
