
"""
Paste HTML content here
"""
def content():
    return """

"""

from re import search
from requests import get
from time import sleep
from tqdm import tqdm
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from bs4 import BeautifulSoup
from urllib.request import urlretrieve

"""
Attempt download the given URL to the given file. Retrying up to 5 times.
"""
@retry(stop=stop_after_attempt(5),
       wait=wait_fixed(3)+wait_exponential(min=1, max=16))
def retry_download(url, file) -> None:
    urlretrieve(url, file)


soup = BeautifulSoup(content(), 'html.parser')
total = len(soup.find_all('a', class_='episode-lockup'))

episodes = soup.find_all('a', class_='episode-lockup')
for abs_num, ep in tqdm(enumerate(episodes), total=total):
    # Get episode number from aria-label
    episode_number = search(r'Episode (\d+).*', ep['aria-label']).group(1)

    # Skip if the file already exists
    if Path(f'{abs_num+1}-{episode_number}.jpg').exists():
        continue

    # Get url of episode page for next request
    url = 'https://tv.apple.com' + ep['href']
    req = get(url)

    # Parse the image sourced on this webpage
    ep_soup = BeautifulSoup(req.content, 'html.parser')
    ep_imgs = ep_soup.find('source', type='image/jpeg')

    # If the episode has no images, skip
    if ep_imgs is None:
        continue

    # Go through all images, find the best one (largest width)
    best_url, best_width = '', 0
    for image in ep_imgs['srcset'].split(','):
        url, width = image.strip().split(' ')
        if int(width[:-1]) > best_width:
            best_width = int(width[:-1])
            best_url = url

    # Download the image
    retry_download(best_url, f'{abs_num+1}-{episode_number}.jpg')
    sleep(0.0625)
