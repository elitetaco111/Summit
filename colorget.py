import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_colorblocks_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        colorblocks = soup.find_all('div', class_='colorblock')
        # Split each colorblock's text by whitespace/newline if needed
        return [cb.get_text(separator='|', strip=True).split('|') for cb in colorblocks]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    with open('links.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    rows = []
    max_cols = 0

    for url in urls:
        colorblocks = get_colorblocks_from_url(url)
        for block in colorblocks:
            row = [url] + block
            rows.append(row)
            if len(row) > max_cols:
                max_cols = len(row)

    # Pad rows so all have the same number of columns
    for row in rows:
        row.extend([''] * (max_cols - len(row)))

    # First column is 'url', others are unnamed
    columns = ['url'] + [''] * (max_cols - 1)
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv('colorblocks.csv', index=False, header=False)
    print("Saved colorblocks.csv")

if __name__ == "__main__":
    main()