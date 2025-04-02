import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import csv
import re

def scrape_twitch_earnings(max_clicks = 50, file_path = 'data/twitch_earnings.csv'):
    """
    A function to scrape information from the twitch earnings leaderboard 
    (https://twitch.pages.dev/). By default the leaderboard only displays the 
    top 100 twitch earners. Clicking on the "More..." button at the button at 
    the page displays an addtional 100 earners (200 total). Increasing the 
    max_clicks argument will increase the number of streamer data returned, 
    but will take longer to run.
    
    Args:
    max_clicks: The number of times to click the "More..." button -> int
    file_path: Path of csv file to save -> str
    
    Return:
    A csv file saved to file_path with the following columns:
        'ranking': ranking of twitch streamer,
        'name': streamer or channel name,
        'earnings_usd': earnings in US dollars
    
    """
    # Set up Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the page
        url = "https://twitch.pages.dev/"
        driver.get(url)
        
        # Give the page time to load
        time.sleep(2)
        
        # Counter to keep track of how many times we've clicked "More..."
        click_count = 0
        # max_clicks = 50  # Safety limit to prevent infinite loops
        
        while click_count < max_clicks:
            try:
                # Find the "More..." button
                more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'More...')]"))
                )
                
                # Click the button
                # more_button.click()
                driver.execute_script("arguments[0].click();", more_button)
                click_count += 1
                print(f"Clicked 'More...' button ({click_count} times)")
                
                # Wait for the new content to load
                time.sleep(2)
                
            except TimeoutException:
                # If we can't find the button, we've likely reached the end
                print("No more 'More...' button found. All content loaded.")
                break
            except Exception as e:
                print(f"Error clicking 'More...' button: {e}")
                break
        
        print(f"Finished loading content after {click_count} clicks")
        
        # Now that all content is loaded, get the page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all streamer elements
        # Based on inspection of the elements, select the divs that contain the streamer earning info 
        streamer_elements = soup.select('div.flex.flex-row.items-center.font-mono')
        
        print(f"Found {len(streamer_elements)} streamers on the page")
        
        # Prepare a list to store the data
        streamers_data = []
        
        # Extract data for each streamer
        for element in streamer_elements:
            try:
                # Find the streamer name from the anchor tag
                streamer_name_element = element.select_one('a')
                if not streamer_name_element:
                    continue
                    
                streamer_name = streamer_name_element.text.strip()
                streamer_url = streamer_name_element['href']
                
                # Extract earnings amount from the last span in the div
                spans = element.select('span')
                if spans and len(spans) >= 3:
                    earnings_text = spans[-1].text.strip()
                else:
                    earnings_text = ""
                
                # Clean up the earnings amount (remove non-numeric characters)
                earnings = re.sub(r'[^0-9.]', '', earnings_text)
                
                # Get ranking from the first span
                if spans and len(spans) >= 1:
                    ranking_text = spans[0].text.strip()
                    ranking = re.sub(r'[^0-9]', '', ranking_text)
                else:
                    ranking = ""
                
                # Add data to our list
                streamers_data.append({
                    'ranking': ranking,
                    'name': streamer_name,
                    'earnings_usd': earnings
                })
                
            except Exception as e:
                print(f"Error processing a streamer: {e}")
        
        print(f"Successfully collected data for {len(streamers_data)} streamers")
        
        # Save the data to a CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ranking', 'name', 'earnings_usd']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for data in streamers_data:
                writer.writerow(data)
        
        print(f"Data saved to {file_path}")
        return streamers_data
        
    finally:
        # close the driver
        driver.quit()

if __name__ == "__main__":
    scrape_twitch_earnings()