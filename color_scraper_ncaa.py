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
    Scrape the NCAA Division 1 page to get links to all conferences,
    and then scrape each conference page to get links to all team pages.
    """
    ncaa_url = "https://usteamcolors.com/ncaa-division-2/"
    response = requests.get(ncaa_url, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Add a random delay after loading the NCAA Division 1 page
    delay = random.uniform(2, 5)
    print(f"Delaying for {delay:.2f} seconds after loading NCAA Division 2 page...")
    time.sleep(delay)

    # Find all conference links on the NCAA Division 1 page
    conference_links = []
    for link in soup.select('a[href*="-conference"]'):
        conference_links.append(link['href'])

    print(f"Found {len(conference_links)} conference links.")

    # For each conference, find all team links
    team_links = []
    for conference_url in conference_links:
        print(f"Scraping conference: {conference_url}")
        response = requests.get(conference_url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Add a random delay after loading each conference page
        delay = random.uniform(2, 5)
        print(f"Delaying for {delay:.2f} seconds after loading conference page...")
        time.sleep(delay)

        # Find the <div> with class "us-teams"
        us_teams_section = soup.find('div', class_='us-teams')
        if not us_teams_section:
            print(f"Could not find the 'us-teams' section for conference: {conference_url}")
            continue

        # Find the <ul> inside the "us-teams" section
        team_list = us_teams_section.find('ul')
        if not team_list:
            print(f"Could not find the team list in 'us-teams' for conference: {conference_url}")
            continue

        # Iterate through each <li> in the <ul> and extract the href from <a class="card-image">
        conference_team_links = []
        for li in team_list.find_all('li', class_='card'):
            link = li.find('a', class_='card-image')
            if link and 'href' in link.attrs:
                conference_team_links.append(link['href'])

        # Add the conference's team links to the main list
        team_links.extend(conference_team_links)

        # Print the number of links found for this conference
        print(f"Found {len(conference_team_links)} team links in {conference_url}.")

    print(f"Found a total of {len(team_links)} team links across all conferences.")
    return team_links


def scrape_team_colors(team_url):
    """
    Scrape color information from a team page and save it into a pandas DataFrame.
    """
    response = requests.get(team_url, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Add a random delay after loading each team page
    delay = random.uniform(2, 4)
    print(f"Delaying for {delay:.2f} seconds after loading team page...")
    time.sleep(delay)

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
            if len(cells) == 2:  # Ensure there are two <td> elements (label, value)
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
    for team_url in team_links:
        print(f"Scraping colors from {team_url}...")
        team_colors_df = scrape_team_colors(team_url)

        # Append the scraped colors to the main DataFrame
        all_colors_df = pd.concat([all_colors_df, team_colors_df], ignore_index=True)

        # Add a random delay between 5 and 10 seconds
        delay = random.uniform(5, 10)
        print(f"Delaying for {delay:.2f} seconds before the next team page...")
        time.sleep(delay)

    print(f"Scraped colors for {len(all_colors_df)} entries.")

    # Save the DataFrame to a CSV file
    all_colors_df.to_csv('ncaa_d2_team_colors.csv', index=False, encoding='utf-8')
    print("Data saved to ncaa_d2_team_colors.csv.")

if __name__ == "__main__":
    main()