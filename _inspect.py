"""Quick column name check - print ALL keys from raw items."""
import os, requests, json

with open('.streamlit/secrets.toml') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split(' = ', 1)
            os.environ[k.strip()] = v.strip().strip('"')

token = os.environ['MONDAY_API_TOKEN']
headers = {"Authorization": token, "Content-Type": "application/json", "API-Version": "2024-01"}

# Get 1 item from Work Orders with full column details
q = '''{ boards(ids: [5030095751]) { columns { id title type } items_page(limit: 1) { items { name column_values { id column { title } text value } } } } }'''
r = requests.post("https://api.monday.com/v2", json={"query": q}, headers=headers, timeout=30)
data = r.json()

board = data["data"]["boards"][0]
print("=== BOARD COLUMNS (schema) ===")
for col in board["columns"]:
    print(f"  id={col['id']}  title={col['title']!r}  type={col['type']}")

print("\n=== FIRST ITEM (raw column_values) ===")
item = board["items_page"]["items"][0]
print(f"  name: {item['name']}")
for cv in item["column_values"]:
    col_title = cv.get("column", {}).get("title", "?")
    print(f"  [{cv['id']}] {col_title!r}: text={cv['text']!r}")

# Same for Deals
print("\n\n=== DEALS BOARD COLUMNS ===")
q2 = '''{ boards(ids: [5030095779]) { columns { id title type } items_page(limit: 1) { items { name column_values { id column { title } text value } } } } }'''
r2 = requests.post("https://api.monday.com/v2", json={"query": q2}, headers=headers, timeout=30)
data2 = r2.json()
board2 = data2["data"]["boards"][0]
for col in board2["columns"]:
    print(f"  id={col['id']}  title={col['title']!r}  type={col['type']}")

print("\n=== FIRST DEAL ITEM ===")
item2 = board2["items_page"]["items"][0]
print(f"  name: {item2['name']}")
for cv in item2["column_values"]:
    col_title = cv.get("column", {}).get("title", "?")
    print(f"  [{cv['id']}] {col_title!r}: text={cv['text']!r}")
