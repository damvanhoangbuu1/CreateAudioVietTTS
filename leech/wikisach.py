import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

def get_chapter_content(soup):
    content_body_tag = soup.find(id="bookContentBody")
    if content_body_tag:
        for tag in content_body_tag.find_all(['a', 'div']):
            if tag.name == 'a' or tag.name == 'div':
                    tag.extract()
    return "\n\n\n".join(content_body_tag.stripped_strings)

def get_book_name(soup):
    title_tag = soup.find_all('h2')
    return title_tag[0].text

def get_html_volume_list(book_link):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Chạy ẩn danh không hiển thị giao diện
    chrome_options.add_argument('--no-sandbox')  # Chế độ chạy không cần sandbox
    chrome_options.add_argument('--disable-dev-shm-usage')  # Tắt sử dụng bộ nhớ chia sẻ

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(book_link)
    page_html = ""
    try:
        # Wait for the content inside the div with class 'volume-list' to load
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'volume-list'))
        )

        # Once the content is loaded, get the HTML of the entire page
        page_html = driver.page_source
    finally:
        # Close the browser window
        driver.quit()
        return page_html

def get_all_chapter(book_link, start, lenght):
    soup = BeautifulSoup(get_html_volume_list(book_link), "html.parser")

    book_name = get_book_name(soup)
    urlbase = get_base_url(book_link)

    chapter_tags = soup.find_all('li', class_='chapter-name')
    chapters = []
    for index, chapter_tag in enumerate(chapter_tags):
        if index < start or index > start + lenght:
            continue

        link_tag = chapter_tag.find('a')

        if link_tag is None:
            continue
        
        chapter = {
            'link': urlbase + link_tag['href'],
            'title': chapter_tag.find('a').text,
            'track': index,
            'album': book_name
        }
        chapters.append(chapter)
    return chapters

def get_base_url(full_url):
    parsed_url = urlparse(full_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url
