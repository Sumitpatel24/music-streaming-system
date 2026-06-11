import os
import pandas as pd

base_folder = "static/songs"

data = []

for category in os.listdir(base_folder):

    category_path = os.path.join(base_folder, category)

    if os.path.isdir(category_path):

        for file in os.listdir(category_path):

            if file.endswith(".mp3"):

                song_name = file.replace(".mp3", "")
                safe_file = file.encode("ascii", "ignore").decode()
                data.append({
                    "song_name": song_name,
                    "singer": "Unknown",
                    "file_name": file,
                    "image": "default.jpg",
                    "category": category
                })

df = pd.DataFrame(data)

df.to_excel("songs.xlsx", index=False)

print("Excel Created Successfully")
print("Total Songs =", len(data))