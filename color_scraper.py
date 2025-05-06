import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Base URL of the website
BASE_URL = "https://usteamcolors.com/"

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
    Scrape the main page to get links to all team pages.
    """
    response = requests.get(BASE_URL, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    team_links = []

    # Find all team links
    for link in soup.select('a[href*="-team-colors"]'):
        team_links.append(link['href'])
    
    return team_links

def scrape_team_colors(team_url):
    """
    Scrape color information from a team page and save it into a pandas DataFrame.
    """
    response = requests.get(team_url, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to find the team name
    team_name_element = soup.find('h1', class_='title')
    if not team_name_element:
        print(f"Could not find team name on page: {team_url}")
        return pd.DataFrame()  # Return an empty DataFrame if team name is not found

    team_name = team_name_element.text.strip()

    # Create a DataFrame to store the colors for this team
    team_colors_df = pd.DataFrame(columns=['Team', 'Color Name', 'Hex', 'RGB', 'CMYK', 'Pantone'])

    # Find the div containing the color table (ID ends with '-color-codes')
    color_div = soup.find('div', id=lambda x: x and x.endswith('-color-codes'))
    if not color_div:
        print(f"Could not find color table for {team_name} at {team_url}")
        return team_colors_df  # Return an empty DataFrame if no color table is found

    # Iterate through each table within the color div
    color_tables = color_div.find_all('table')
    for table in color_tables:
        color_data = {}  # Create a new dictionary for each table

        # Extract the color name from the <th> element in the first <tr>
        first_row = table.find('tbody').find('tr')
        if first_row:
            color_name_element = first_row.find('th').find('span')
            if color_name_element:
                color_data["Color Name"] = color_name_element.text.strip()

        # Extract other color details from the <td> elements in the rows
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:  # Ensure there are three <td> elements (label, value)
                label = cells[0].text.strip().replace(":", "")  # Remove the colon from the label
                value = cells[1].text.strip()  # The value (e.g., "#002244")
                color_data[label] = value

        # Ensure the required fields are present before appending
        if "Color Name" in color_data and "Hex color" in color_data:
            # Append the color data as a new row in the DataFrame
            team_colors_df = pd.concat(
                [
                    team_colors_df,
                    pd.DataFrame([{
                        'Team': team_name,
                        'Color Name': color_data.get("Color Name", ""),
                        'Hex': color_data.get("Hex color", ""),
                        'RGB': color_data.get("RGB", ""),
                        'CMYK': color_data.get("CMYK", ""),
                        'Pantone': color_data.get("Pantone", ""),
                    }])
                ],
                ignore_index=True
            )

    return team_colors_df

def main():
    print("Scraping team links...")
    team_links = get_team_links()
    print(f"Found {len(team_links)} team links.")

    # Create an empty DataFrame to store all team colors
    all_colors_df = pd.DataFrame(columns=['Team', 'Color Name', 'Hex', 'RGB', 'CMYK', 'Pantone'])
    i = 0
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