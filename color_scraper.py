import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from lxml import html

# Base URL of the website
BASE_URL = "https://teamcolorcodes.com/ncaa-color-codes/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

def get_team_links():
    """
    Scrape the main page to get links to all team pages using XPath.
    """
    response = requests.get(BASE_URL, headers=get_headers(), timeout=10)
    tree = html.fromstring(response.content)  # Use lxml to parse the HTML content
    team_links = []

    # XPath to locate all <p> blocks below the "Browse By Team" <h4>
    xpath_for_paragraphs = "//div[@class='entry-content']//h4[text()='Browse By Team']/following-sibling::p"

    # Find all <p> blocks
    paragraphs = tree.xpath(xpath_for_paragraphs)
    for paragraph in paragraphs:
        # Extract all <a> tags within each <p> block
        links = paragraph.xpath(".//a[@href]")
        for link in links:
            team_links.append(link.attrib['href'])

    if not team_links:
        print("Could not find any team links using the provided XPath.")
    return team_links

def scrape_team_colors(team_url):
    """
    Scrape color information from a team page and save it into a pandas DataFrame.
    """
    response = requests.get(team_url, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(3)
    # Find all color blocks
    color_blocks = soup.find_all('div', class_='colorblock')
    if not color_blocks:
        print(f"Could not find color blocks on page: {team_url}")
        return pd.DataFrame()  # Return an empty DataFrame if no color blocks are found

    # Create a DataFrame to store the colors for this team
    team_colors_df = pd.DataFrame(columns=['Link', 'Pantone', 'Hex Color', 'RGB', 'CMYK', 'Matching Paint Link'])

    for block in color_blocks:
        # Extract text from the color block and split by <br> tags
        block_text = block.decode_contents().split('<br>')
        block_data = [team_url]  # Start with the team URL as the first column
        for item in block_text:
            # Clean up the text and append it to the row
            block_data.append(BeautifulSoup(item, 'html.parser').text.strip())

        # Ensure the row has the correct number of columns
        while len(block_data) < 6:
            block_data.append("")  # Fill missing columns with empty strings

        # Append the row to the DataFrame
        team_colors_df = pd.concat(
            [team_colors_df, pd.DataFrame([block_data], columns=team_colors_df.columns)],
            ignore_index=True
        )

    return team_colors_df

def main():
    print("Scraping team links...")
    team_links = get_team_links()
    print(f"Found {len(team_links)} team links.")

    # Create an empty DataFrame to store all team colors
    all_colors_df = pd.DataFrame(columns=['Link', 'Pantone', 'Hex Color', 'RGB', 'CMYK', 'Matching Paint Link'])
    for team_url in team_links:
        print(f"Scraping colors from {team_url}...")
        team_colors_df = scrape_team_colors(team_url)

        # Append the scraped colors to the main DataFrame
        all_colors_df = pd.concat([all_colors_df, team_colors_df], ignore_index=True)

        # Add a random delay between 5 and 15 seconds
        time.sleep(random.uniform(5, 15))

    print(f"Scraped colors for {len(all_colors_df)} entries.")

    # Save the DataFrame to a CSV file
    all_colors_df.to_csv('team_colors.csv', index=False, encoding='utf-8')
    print("Data saved to team_colors.csv.")

if __name__ == "__main__":
    main()