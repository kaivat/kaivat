import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin, urlparse
import logging
import re

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

BASE_URL_ITB = "https://intheblack.cpaaustralia.com.au"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def find_rss_in_html(url):
    """Fetches a URL and looks for RSS feed links in its HTML."""
    rss_links = []
    try:
        logging.info(f"Fetching HTML from {url} to find RSS links...")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Common RSS link types
        link_tags = soup.find_all('link', attrs={'rel': 'alternate', 'type': re.compile(r'application/(rss|atom)\+xml')})
        for tag in link_tags:
            href = tag.get('href')
            if href:
                # Ensure the URL is absolute
                full_url = urljoin(url, href)
                rss_links.append(full_url)
                logging.info(f"Found potential RSS feed link in HTML of {url}: {full_url}")
        
        if not rss_links:
            logging.info(f"No specific RSS <link> tags found in HTML of {url}.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching HTML from {url}: {e}")
    except Exception as e:
        logging.error(f"Error parsing HTML for {url}: {e}")
    return rss_links

def test_rss_feed(feed_url):
    """Tests if a given RSS feed URL is valid and contains entries."""
    logging.info(f"Testing RSS feed: {feed_url}")
    try:
        # Using a timeout for feedparser.parse by handling it within requests.get
        # feedparser itself doesn't have a direct timeout, so we fetch content first
        response = requests.get(feed_url, headers=HEADERS, timeout=20) # Increased timeout for feeds
        response.raise_for_status()
        
        # Check content type if possible, though some feeds might not set it perfectly
        # content_type = response.headers.get('Content-Type', '').lower()
        # if not ('xml' in content_type or 'rss' in content_type or 'atom' in content_type or 'application/octet-stream' in content_type): # octet-stream sometimes used
        #     logging.warning(f"Feed {feed_url} has an unexpected Content-Type: {content_type}. Proceeding with parsing attempt.")

        feed = feedparser.parse(response.content) # Parse the fetched content
        
        if feed.bozo:
            logging.warning(f"Feed {feed_url} may be ill-formed. Bozo reason: {feed.bozo_exception}")
        
        if feed.entries and len(feed.entries) > 0:
            logging.info(f"SUCCESS: RSS feed {feed_url} is valid and contains {len(feed.entries)} entries.")
            for i, entry in enumerate(feed.entries[:3]): # Log first few for verification
                logging.info(f"  Entry {i+1}: Title: {entry.title}, Link: {entry.link}")
            return True
        elif feed.entries is not None and len(feed.entries) == 0:
             logging.warning(f"RSS feed {feed_url} is valid but contains 0 entries.")
             return False
        else:
            logging.error(f"FAILURE: RSS feed {feed_url} did not parse correctly or has no entries. Status in feed obj: {feed.get('status', 'N/A')}. Debug message: {feed.get('debug_message', 'N/A')}")
            return False
            
    except requests.exceptions.RequestException as e: # Catch requests errors (timeout, HTTP error for feed URL itself)
        logging.error(f"FAILURE: RequestException while fetching content for RSS feed {feed_url}: {e}")
        return False
    except Exception as e: # Catch other errors (e.g. during feedparser.parse if content is totally invalid)
        logging.error(f"FAILURE: Exception while testing RSS feed {feed_url}: {e}")
        return False

def find_and_test_rss_feeds():
    """Main function to find and test RSS feeds for INTHEBLACK."""
    found_and_working_rss = []
    tested_urls = set() # Keep track of URLs tested to avoid redundancy

    # 1. Check main page HTML for RSS links
    main_page_rss_links = find_rss_in_html(BASE_URL_ITB)
    for link in main_page_rss_links:
        if link not in tested_urls:
            if test_rss_feed(link):
                found_and_working_rss.append(link)
            tested_urls.add(link)

    # 2. Try common feed URL patterns on the base URL
    common_patterns = ['/feed', '/rss', '/atom.xml', '/feed/', '/rss/', '/atom.xml/'] # Added variations
    for pattern in common_patterns:
        potential_feed_url = urljoin(BASE_URL_ITB, pattern)
        if potential_feed_url not in tested_urls:
            if test_rss_feed(potential_feed_url):
                found_and_working_rss.append(potential_feed_url)
            tested_urls.add(potential_feed_url)
    
    # 3. Identify potential category pages and test their feeds
    guessed_categories = [
        "tax", "taxation", "business", "finance", "policy", "regulation", 
        "insights", "articles", "news", "leadership", "strategy", "careers", "technology", "management"
    ] 
    
    try:
        logging.info(f"Fetching {BASE_URL_ITB} to look for category links for RSS testing...")
        response = requests.get(BASE_URL_ITB, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        candidate_paths = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            parsed_href = urlparse(href)
            
            # Check if it's a path on the same domain
            is_same_domain_path = (parsed_href.netloc == "" or parsed_href.netloc == urlparse(BASE_URL_ITB).netloc)
            
            if is_same_domain_path and parsed_href.path:
                path_segments = [seg for seg in parsed_href.path.split('/') if seg]
                # Looking for paths like /slug or /category/slug or /topic/slug
                if len(path_segments) == 1: # e.g. /tax
                    segment = path_segments[0]
                    if segment and len(segment) > 3 and not re.match(r'.*\.(aspx|jpg|png|pdf|gif|js|css)$', segment, re.IGNORECASE):
                        candidate_paths.add(segment)
                elif len(path_segments) == 2 and path_segments[0] in ['category', 'topic', 'section', 'issue', 'type', 'area']: # e.g. /category/tax
                    segment = path_segments[1]
                    if segment and len(segment) > 3 and not re.match(r'.*\.(aspx|jpg|png|pdf|gif|js|css)$', segment, re.IGNORECASE):
                         candidate_paths.add(f"{path_segments[0]}/{segment}")
        
        logging.info(f"Found {len(candidate_paths)} potential category paths from homepage: {candidate_paths if candidate_paths else 'None'}")
        guessed_categories.extend(list(candidate_paths))
        guessed_categories = list(set(guessed_categories)) # Make unique

    except requests.exceptions.RequestException as e:
        logging.warning(f"Could not fetch homepage to find category links: {e}")

    for category_slug in guessed_categories:
        # Test feed for path like /category/tax/feed or just /tax/feed
        # Ensure category_slug itself doesn't end with /feed or /rss already
        if category_slug.endswith(('/feed', '/rss', '/feed/', '/rss/')):
            potential_feed_url = urljoin(BASE_URL_ITB, category_slug)
        else:
            potential_feed_url = urljoin(BASE_URL_ITB, f"{category_slug.strip('/')}/feed/")
        
        if potential_feed_url not in tested_urls:
             if test_rss_feed(potential_feed_url):
                found_and_working_rss.append(potential_feed_url)
             tested_urls.add(potential_feed_url)

    if found_and_working_rss:
        logging.info(f"Found the following working RSS feeds for INTHEBLACK: {list(set(found_and_working_rss))}") # Deduplicate
    else:
        logging.warning("No working RSS feeds found after extensive checking for INTHEBLACK.")
    
    return list(set(found_and_working_rss))


def scrape_itb_articles(target_url):
    logging.info(f"Attempting to scrape articles from: {target_url}")
    articles_found = []
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        possible_article_elements = []
        # Updated selectors based on re-inspection of INTHEBLACK homepage (May 2024)
        # 1. Main featured articles often in elements with data-testid attributes
        possible_article_elements.extend(soup.find_all('article', attrs={'data-testid': re.compile(r'article-preview', re.IGNORECASE)}))
        # 2. Teaser blocks for other articles
        possible_article_elements.extend(soup.find_all('div', class_=re.compile(r'teaser--(?!ad)', re.IGNORECASE))) # Exclude 'teaser--ad'
        # 3. Generic article tags as a fallback
        if not possible_article_elements:
            possible_article_elements.extend(soup.find_all('article'))

        logging.info(f"Found {len(possible_article_elements)} potential article elements using combined selectors on {target_url}.")
        processed_urls = set()

        for item in possible_article_elements:
            headline_text = None
            article_url = None

            link_tag = item.find('a', href=True)
            if not link_tag: 
                continue 
            
            # Ensure URL is absolute and clean
            raw_url = link_tag['href']
            if not raw_url or raw_url.startswith("javascript:") or raw_url == "#":
                continue
            article_url = urljoin(BASE_URL_ITB, raw_url.strip())

            if article_url in processed_urls: # Avoid processing the same URL twice
                continue

            # Try to find headline within specific title classes or general heading tags
            headline_tag = item.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'(title|headline|heading|preview__title|teaser__title)', re.IGNORECASE))
            if not headline_tag: # If no specific class, find first h1-h5 inside the item
                headline_tag = item.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            
            if headline_tag:
                headline_text = ' '.join(headline_tag.get_text(strip=True, separator=' ').split()) # Cleaned text
            elif link_tag.has_attr('title') and len(link_tag['title'].strip()) > 10:
                 headline_text = link_tag['title'].strip()
            elif link_tag.get_text(strip=True) and len(link_tag.get_text(strip=True)) > 20 : # Use link's own text if it's substantial
                 headline_text = ' '.join(link_tag.get_text(strip=True, separator=' ').split())

            if headline_text and article_url and len(headline_text) > 5: # Basic sanity check
                articles_found.append({'headline': headline_text, 'url': article_url})
                processed_urls.add(article_url)
                logging.info(f"  Extracted: '{headline_text}' - {article_url}")
            
            if len(articles_found) >= 7: # Aim for a decent number if available
                break
        
        if articles_found:
            logging.info(f"Successfully scraped {len(articles_found)} distinct articles from {target_url}.")
        else:
            logging.warning(f"No articles scraped from {target_url} with current selectors. Site structure might have changed or page has no articles in expected format.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {target_url}: {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during scraping of {target_url}: {e}")
        
    return articles_found[:5] # Return up to 5 as per original goal


if __name__ == "__main__":
    logging.info("--- Starting INTHEBLACK Content Extraction Re-evaluation ---")
    
    working_rss_feeds = find_and_test_rss_feeds()
    extracted_articles = []

    if working_rss_feeds:
        logging.info(f"SUCCESS: Found and validated working RSS feeds: {working_rss_feeds}")
        feed_to_use = working_rss_feeds[0] # Pick the first one
        logging.info(f"Attempting to extract articles from RSS feed: {feed_to_use}")
        try:
            feed = feedparser.parse(feed_to_use, agent=HEADERS['User-Agent'], request_headers=HEADERS)
            if feed.entries:
                for entry in feed.entries[:5]: 
                    extracted_articles.append({'headline': entry.title, 'url': entry.link})
                logging.info(f"Extracted {len(extracted_articles)} articles via RSS feed {feed_to_use}.")
            else:
                logging.warning(f"RSS feed {feed_to_use} had no entries. Will attempt scraping if needed.")
        except Exception as e:
            logging.error(f"Error parsing RSS feed {feed_to_use} for article extraction: {e}")
    else:
        logging.warning("No working RSS feeds found. Proceeding to scraping attempt.")

    if not extracted_articles: 
        logging.info("RSS did not yield articles, attempting scraping from main page...")
        articles_from_scraping = scrape_itb_articles(BASE_URL_ITB)
        if articles_from_scraping:
            extracted_articles = articles_from_scraping # Use these if scraping was successful

    logging.info("\n--- Re-evaluation Summary ---")
    if working_rss_feeds:
        print("\nDiscovered and Validated RSS Feeds:")
        for feed_url in working_rss_feeds:
            print(f"- {feed_url}")
    else:
        print("\nNo functional RSS feeds were discovered after extensive search.")

    if extracted_articles:
        print("\nExtracted Articles (up to 5):")
        for i, article in enumerate(extracted_articles):
            print(f"{i+1}. Headline: {article['headline']}")
            print(f"   URL: {article['url']}")
    else:
        print("\nNo articles were successfully extracted (either via RSS or scraping).")

    logging.info("--- INTHEBLACK Content Extraction Re-evaluation Finished ---")
