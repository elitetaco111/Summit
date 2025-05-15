import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# Load the links from the CSV file
links_df = pd.read_csv('links.csv')
links = links_df['links'].tolist()

# Prepare the output data
output_data = []

# Iterate through each link
for link in links:
    time.sleep(random.uniform(5, 15))  # Random delay between requests
    print(f"Processing link: {link}")
    try:
        # Send a GET request to the link
        response = requests.get(link)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all color blocks
        color_blocks = soup.find_all('div', class_='colorblock')

        for block in color_blocks:
            raw_text = block.decode_contents()  # Get the inner HTML
            # Split the text by <br> markers and clean up the data
            columns = [line.strip() for line in raw_text.split('<br>') if line.strip()]
            if len(columns) >= 5:
                color = columns[0].replace("Hex Color:", "").strip()
                pantone = columns[1].replace("PANTONE:", "").strip()
                rgb = columns[2].replace("RGB:", "").strip()
                cmyk = columns[3].replace("CMYK:", "").strip()
                matching_paint = columns[4].strip()
                output_data.append([link, color, pantone, rgb, cmyk, matching_paint])
    except Exception as e:
        print(f"Error processing link {link}: {e}")

# Save the output data to a CSV file
output_df = pd.DataFrame(output_data, columns=['Link', 'Color', 'Pantone', 'RGB', 'CMYK', 'Matching Paint'])
output_df.to_csv('output.csv', index=False)

print("Scraping complete. Data saved to output.csv.")