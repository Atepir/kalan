import sys
from neo4j import GraphDatabase

URIS = [
    "bolt://127.0.0.1:7687",
    "neo4j://127.0.0.1:7687",
    "bolt+s://127.0.0.1:7687",
    "neo4j+s://127.0.0.1:7687",
    "bolt+ssc://127.0.0.1:7687",
    "neo4j+ssc://127.0.0.1:7687",
]

for uri in URIS:
    try:
        print(f"Trying {uri}...")
        driver = GraphDatabase.driver(uri, auth=("neo4j", "dev_password"))
        driver.verify_connectivity()
        print(f"SUCCESS: connected using {uri}")
        driver.close()
    except Exception as e:
        print(f"FAIL: {uri} -> {type(e).__name__}: {e}")

print("Done.")
