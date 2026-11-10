"""
Quick helper script to generate a realistic sales CSV
matching the data dictionary schema.
Only needed once - run before init_db.py.
"""

import csv
import random
from datetime import date, timedelta, time

random.seed(42)

PRODUCTS = [
    ("P001", "AeroBook 14 Laptop",      "Electronics",    "Laptops",        899.00, 500.00),
    ("P002", "ProDesk Monitor 27",       "Electronics",    "Monitors",       349.00, 180.00),
    ("P003", "MechEdge Keyboard",        "Electronics",    "Peripherals",     89.00,  40.00),
    ("P004", "ErgoGlide Mouse",          "Electronics",    "Peripherals",     49.00,  20.00),
    ("P005", "SoundWave Headphones",     "Electronics",    "Audio",          199.00,  90.00),
    ("P006", "FitTrack Pro Watch",       "Wearables",      "Smartwatches",   299.00, 130.00),
    ("P007", "Office Chair Pro",         "Furniture",      "Chairs",         389.00, 200.00),
    ("P008", "Standing Desk V2",         "Furniture",      "Desks",          599.00, 320.00),
    ("P009", "Whiteboard 120cm",         "Office Supplies","Boards",          79.00,  35.00),
    ("P010", "Notebook Pack x5",         "Office Supplies","Stationery",      14.99,   6.00),
]

STORES = [
    ("NYC-01", "New York Central", "United States", "Northeast",   "New York"),
    ("LAX-01", "LA Westside",      "United States", "West",        "Los Angeles"),
    ("CHI-01", "Chicago Loop",     "United States", "Midwest",     "Chicago"),
    ("LON-01", "London Oxford St", "United Kingdom","South East",  "London"),
    ("HEL-01", "Helsinki Central", "Finland",       "Uusimaa",     "Helsinki"),
]

CHANNELS   = ["Online", "In-Store", "Phone"]
GENDERS    = ["Male", "Female", "Non-binary"]
SEGMENTS   = ["New Customer", "Returning Customer", "Loyal Customer", "VIP"]
PAYMENTS   = ["Credit Card", "Debit Card", "Cash", "PayPal", "Bank Transfer"]
STATUSES   = ["Completed", "Pending", "Cancelled", "Returned"]
SHIPPINGS  = ["Standard", "Express", "Overnight", "Click & Collect"]
RETURN_REASONS = ["Damaged", "Wrong Item", "Changed Mind", "Defective", ""]
PROMOS     = ["SUMMER20", "BLACKFRIDAY25", "WELCOME10", "LOYALTY15", ""]
SALES_REPS = ["Emma Carter", "Liam Park", "Sophia Johnson", "Noah Ali", "Mia Chen", ""]

NAMES_F = ["Emma Carter", "Mia Chen", "Sophia Johnson", "Olivia Brown", "Ava Wilson"]
NAMES_M = ["Liam Park", "Noah Ali", "James Lee", "Lucas Harris", "Mason Clark"]
NAMES_N = ["Jordan Smith", "Alex Taylor", "Sam Morgan"]

start_date = date(2024, 1, 1)

rows = []
for i in range(1, 301):
    tx_id      = f"T{20001000 + i}"
    order_id   = f"O{1001000 + i}"
    cust_id    = f"C{random.randint(1, 150):05d}"
    gender     = random.choice(GENDERS)
    if gender == "Male":
        name = random.choice(NAMES_M)
    elif gender == "Female":
        name = random.choice(NAMES_F)
    else:
        name = random.choice(NAMES_N)
    age        = random.randint(18, 72)
    segment    = random.choice(SEGMENTS)
    order_dt   = start_date + timedelta(days=random.randint(0, 364))
    order_time = time(random.randint(8, 22), random.randint(0, 59), random.randint(0, 59))
    channel    = random.choice(CHANNELS)
    store      = random.choice(STORES)
    prod       = random.choice(PRODUCTS)
    qty        = random.randint(1, 5)
    disc_pct   = random.choice([0, 5, 10, 15, 20, 25])
    unit_price = prod[4]
    cost_unit  = prod[5]
    sales_amt  = round(qty * unit_price * (1 - disc_pct / 100), 2)
    cost_amt   = round(qty * cost_unit, 2)
    profit     = round(sales_amt - cost_amt, 2)
    payment    = random.choice(PAYMENTS)
    status     = random.choices(STATUSES, weights=[70, 10, 10, 10])[0]
    shipping   = random.choice(SHIPPINGS)
    del_days   = random.randint(1, 10)
    ret_flag   = "Yes" if status == "Returned" else random.choices(["Yes", "No"], weights=[5, 95])[0]
    ret_reason = random.choice(RETURN_REASONS[:-1]) if ret_flag == "Yes" else ""
    sales_rep  = random.choice(SALES_REPS)
    promo      = random.choice(PROMOS)
    rating     = round(random.uniform(1, 5), 1)
    inventory  = random.randint(0, 200)
    year       = order_dt.year

    rows.append([
        tx_id, order_id, cust_id, name, age, gender, segment,
        order_dt, order_time, channel,
        store[0], store[1], store[2], store[3], store[4],
        prod[0], prod[1], prod[2], prod[3],
        qty, unit_price, disc_pct, sales_amt, cost_amt, profit,
        payment, status, shipping, del_days,
        ret_flag, ret_reason, sales_rep, promo, rating, inventory, year
    ])

headers = [
    "Transaction_ID", "Order_ID", "Customer_ID", "Customer_Name", "Customer_Age",
    "Customer_Gender", "Customer_Segment", "Order_Date", "Order_Time", "Sales_Channel",
    "Store_ID", "Store_Name", "Country", "Region", "City",
    "Product_ID", "Product_Name", "Product_Category", "Product_Subcategory",
    "Quantity", "Unit_Price", "Discount_Percentage", "Sales_Amount", "Cost_Amount", "Profit",
    "Payment_Method", "Order_Status", "Shipping_Method", "Delivery_Days",
    "Return_Flag", "Return_Reason", "Sales_Representative", "Promotion_Code",
    "Customer_Rating", "Inventory_Level", "Order_Year"
]

with open("sales_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Generated sales_data.csv with {len(rows)} rows.")
