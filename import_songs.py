import pandas as pd
import mysql.connector

df = pd.read_excel("songs.xlsx")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sumitpatel05",   # apna mysql password
    database="musicify_db"
)

cur = conn.cursor()

for _, row in df.iterrows():

    cur.execute("""
    INSERT INTO songs
    (song_name, singer, file_name, image, category)
    VALUES (%s,%s,%s,%s,%s)
    """, (
        row['song_name'],
        row['singer'],
        row['file_name'],
        row['image'],
        row['category']
    ))

conn.commit()

print("Songs Imported Successfully")

cur.close()
conn.close()