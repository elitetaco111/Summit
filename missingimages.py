import os
import csv

csv_file = "DROPSHIP IMAGE REQUEST.csv"
images_folder = "images"
output_file = "missing.txt"

# 1. Get all base style numbers from CSV
style_numbers = set()
with open(csv_file, newline='', encoding='latin1') as f:
    reader = csv.DictReader(f)
    for row in reader:
        style_num = row["Style Number"].strip()
        base_style_num = style_num.split('-')[0]
        style_numbers.add(base_style_num)

# 2. Get all image filenames (recursively)
image_files = []
for root, dirs, files in os.walk(images_folder):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tif', '.tiff')):
            image_files.append(file)

# 3. Extract base style numbers from image filenames
image_style_numbers = set()
for file in image_files:
    name, _ = os.path.splitext(file)
    base_style_num = name.split('-')[0]
    image_style_numbers.add(base_style_num)

# 4. Find missing style numbers (those in CSV but not in images)
missing = sorted([sn for sn in style_numbers if sn not in image_style_numbers])

# 5. Write missing style numbers to missing.txt
with open(output_file, "w", encoding="utf-8") as f:
    for sn in missing:
        f.write(sn + "\n")

print(f"Done. Missing style numbers written to {output_file}")