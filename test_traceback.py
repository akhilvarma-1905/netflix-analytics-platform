import sqlite3
import sys

sys.path.append('.')

from pages.insights import generate_neural_response

conn = sqlite3.connect('netflix.db')

queries = [
    "hi",
    "top 10 movies",
    "movies directed by Christopher Nolan",
    "starring Will Smith",
    "cast of Breaking Bad",
    "how many movies are from Canada",
    "top 10 errors"
]

with open('scratch_out.txt', 'w', encoding='utf-8') as f:
    for q in queries:
        f.write(f"\n--- Testing Query: '{q}' ---\n")
        res = generate_neural_response(conn, q)
        f.write("Response:\n")
        f.write(res)
        f.write("\n")

print("All queries completed successfully. Written outputs to scratch_out.txt.")
