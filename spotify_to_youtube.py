from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytube import YouTube
import time
import os
import logging
import re
from urllib.parse import urlparse, urlunparse, parse_qs
import yt_dlp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your ChromeDriver executable
chrome_driver_path = "C:\Program Files\Google\Chrome Dev\Application\chromedriver.exe"  # Replace with the actual path to your ChromeDriver

# Set up Chrome options
chrome_options = Options()
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe"  # Replace with your Chrome binary path

# Set up the Chrome WebDriver
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)

def initialize_driver():
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    return driver

def scrape_spotify_songs():
    try:
        driver.get('https://accounts.spotify.com/en/login')
        time.sleep(2)
        
        logger.info("Navigating to Spotify login page")
        
        driver.find_element(By.ID, 'login-username').send_keys('#')  # Replace with your username
        driver.find_element(By.ID, 'login-password').send_keys('#')  # Replace with your password
        driver.find_element(By.ID, 'login-button').click()
        
        logger.info("Logging in")
        
        time.sleep(10)  
        
        # Navigate to your liked songs or a specific playlist
        driver.get('https://open.spotify.com/collection/tracks')
        logger.info("Navigating to your liked songs")
        time.sleep(40)
        
        # Extract song titles and artists
        songs = []
        song_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="tracklist-row"]')
        
        logger.info(f"Found {len(song_elements)} song elements")
        
        for song_element in song_elements:
            try:
                #Title Extract
                title_element = song_element.find_element(By.CSS_SELECTOR, '.encore-text.encore-text-body-medium.encore-internal-color-text-base.btE2c3IKaOXZ4VNAb8WQ.standalone-ellipsis-one-line')
                title = title_element.text
                logger.info(f"Extracted title: {title}")

              #Artist Extract
                artist_elements = song_element.find_elements(By.CSS_SELECTOR, 'span.encore-text.encore-text-body-small.encore-internal-color-text-subdued.UudGCx16EmBkuFPllvss.standalone-ellipsis-one-line a')
                artists = [artist.text for artist in artist_elements]
                artist = ', '.join(artists)  
                logger.info(f"Extracted artist(s): {artist}")

               
                songs.append(f"{title} by {artist}")
            except Exception as e:
                logger.error(f"Error extracting song details: {e}")

        logger.info(f"Scraped {len(songs)} songs")
        return songs
    except Exception as e:
        logger.error(f"An error occurred during Spotify scraping: {e}")
    finally:
        driver.quit()

def search_youtube(songs):
    youtube_urls = []
    driver = initialize_driver() 
    
    for song in songs:
        try:
            query = song + " official audio"
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            
            driver.get(search_url)
            
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a#video-title'))
            )
            

            video_element = driver.find_element(By.CSS_SELECTOR, 'a#video-title')
            if video_element:
                youtube_url = video_element.get_attribute('href')
                
                if youtube_url.startswith("https://www.youtube.comhttps://"):
                    youtube_url = youtube_url.replace("https://www.youtube.comhttps://", "https://")
                
                youtube_urls.append(youtube_url)
                logger.info(f"Found YouTube URL for {song}: {youtube_url}")
            else:
                logger.warning(f"No video found for {song}")
                
        except Exception as e:
            logger.error(f"Error searching YouTube for {song}: {e}")
            time.sleep(5)
            continue
 
    driver.quit()  
    logger.info(f"Found {len(youtube_urls)} YouTube URLs")
    return youtube_urls


def clean_youtube_url(youtube_url):
    # Parse the URL into components
    parsed_url = urlparse(youtube_url)
    
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get('v', [None])[0]
    

    if not video_id:
        match = re.search(r'([0-9A-Za-z_-]{11})', parsed_url.path)
        if match:
            video_id = match.group(1)
    

    if video_id:
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
    else:

        clean_url = youtube_url
    
    return clean_url


#Download the MP3 Format...
def download_mp3(youtube_urls):
    output_directory = r"C:\Users\Asim Peerzada\Music"
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for url in youtube_urls:
        try:
            logger.info(f"Processing URL: {url}")
            
            clean_url = clean_youtube_url(url)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([clean_url])
                logger.info(f"Downloaded: {clean_url}")
        
        except Exception as e:
            logger.error(f"An error occurred while downloading {url}: {e}")

    logger.info("Download complete!")



if __name__ == "__main__":
    songs = scrape_spotify_songs()
    if songs:
        youtube_urls = search_youtube(songs)
        if youtube_urls:
            download_mp3(youtube_urls)