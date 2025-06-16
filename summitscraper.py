import os
import pandas as pd
import requests

CSV_FILE = "DROPSHIP IMAGE REQUEST.csv" #csv file with the data
IMG_URL_TEMPLATE = "https://img.rallyhouse.com/assets/images/products/{}.jpg" #rh media link template
ROOT_DIR = "images"  #root folder

def safe_folder_name(name):
    # Remove or replace characters that are invalid in Windows folder names
    return "".join(c for c in name if c not in r'<>:"/\|?*').strip()

def main():
    #Read in the csv file
    df = pd.read_csv(CSV_FILE, dtype=str, encoding="latin1")
    for _, row in df.iterrows():
        #grab important info from the csv
        style_number = str(row["Style Number"])
        part_number = safe_folder_name(str(row["Wholesale Part Number"]))
        color = safe_folder_name(str(row["Wholesale Color"]))

        #create the img url and folder struct
        img_url = IMG_URL_TEMPLATE.format(style_number)
        folder_path = os.path.join(ROOT_DIR, part_number, color)
        os.makedirs(folder_path, exist_ok=True)
        img_path = os.path.join(folder_path, f"{style_number}.jpg")

        #download the image with a good request (200)
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(resp.content)
                print(f"Downloaded {img_path}")
            else:
                print(f"Image not found for {style_number} (HTTP {resp.status_code})")
        except Exception as e:
            print(f"Error downloading {img_url}: {e}")

if __name__ == "__main__":
    main()