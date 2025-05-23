import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin, urlparse
import logging
import re
from datetime import datetime # For handling dates if found

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

BASE_URL_CAANZ = "https://www.charteredaccountantsanz.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# --- RSS Feed Functions (similar to previous script) ---
def find_rss_links_in_html(page_url, base_url_for_relative_links):
    """Fetches a URL and looks for RSS feed links in its HTML."""
    rss_links = []
    try:
        logging.info(f"Fetching HTML from {page_url} to find RSS links...")
        response = requests.get(page_url, headers=HEADERS, timeout=20) # Increased timeout
        response.raise_for_status()
        # Check if we were redirected to an error page or different domain
        if response.url != page_url and urlparse(response.url).netloc != urlparse(base_url_for_relative_links).netloc:
            logging.warning(f"Redirected from {page_url} to {response.url}. This might indicate an issue.")
            # Potentially stop if it's a generic error page, though difficult to determine universally
        
        soup = BeautifulSoup(response.content, 'html.parser')
        link_tags = soup.find_all('link', attrs={'rel': 'alternate', 'type': re.compile(r'application/(rss|atom)\+xml', re.IGNORECASE)})
        for tag in link_tags:
            href = tag.get('href')
            if href:
                full_url = urljoin(base_url_for_relative_links, href) # Use base_url for consistency with relative links
                rss_links.append(full_url)
                logging.info(f"Found potential RSS feed link in HTML of {page_url}: {full_url}")
        
        if not rss_links:
            logging.info(f"No specific RSS <link> tags found in HTML of {page_url}.")

    except requests.exceptions.HTTPError as e:
        # Handle 403 specifically, as CAANZ site previously blocked
        if e.response.status_code == 403:
            logging.error(f"Access Denied (403 Forbidden) when fetching {page_url}. Site may be blocking automated access.")
        else:
            logging.error(f"HTTP error fetching HTML from {page_url}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error fetching HTML from {page_url}: {e}")
    except Exception as e:
        logging.error(f"Error parsing HTML for {page_url}: {e}")
    return rss_links

def test_rss_feed(feed_url):
    """Tests if a given RSS feed URL is valid and contains entries."""
    logging.info(f"Testing RSS feed: {feed_url}")
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if feed.bozo:
            logging.warning(f"Feed {feed_url} may be ill-formed. Bozo reason: {feed.bozo_exception}")
        
        if feed.entries and len(feed.entries) > 0:
            logging.info(f"SUCCESS: RSS feed {feed_url} is valid and contains {len(feed.entries)} entries.")
            for i, entry in enumerate(feed.entries[:2]): # Log first few for verification
                logging.info(f"  Entry {i+1}: Title: {entry.title}, Link: {entry.link}")
            return True
        elif feed.entries is not None and len(feed.entries) == 0:
             logging.warning(f"RSS feed {feed_url} is valid but contains 0 entries.")
             return False
        else:
            logging.error(f"FAILURE: RSS feed {feed_url} did not parse correctly or has no entries. Status: {feed.get('status', 'N/A')}. Debug: {feed.get('debug_message', 'N/A')}")
            return False
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logging.error(f"Access Denied (403 Forbidden) when fetching RSS feed {feed_url}.")
        else:
            logging.error(f"FAILURE: HTTP error while fetching content for RSS feed {feed_url}: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"FAILURE: RequestException while fetching content for RSS feed {feed_url}: {e}")
        return False
    except Exception as e:
        logging.error(f"FAILURE: Exception while testing RSS feed {feed_url}: {e}")
        return False

def discover_site_sections(base_url):
    """Attempts to discover key site sections from the homepage."""
    logging.info(f"Discovering site sections from {base_url}...")
    section_urls = {} # Store as 'Section Name': 'URL'
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Keywords for sections we are interested in
        # Making this more targeted: "News", "Media", "Insights", "Technical Resources", "Taxation", "Policy", "Advocacy"
        keywords = ['news', 'media', 'insights', 'technical', 'tax', 'policy', 'advocacy', 'regulation', 'resource', 'update']
        
        nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'(nav|menu|navigation|sitemap)', re.I))
        if not nav_elements: # If no specific nav elements, search all links but be more careful
            nav_elements = [soup] # Search the whole document

        candidate_links = {}
        for nav_area in nav_elements:
            for link in nav_area.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                link_href = link['href']

                if any(keyword in link_text.lower() for keyword in keywords) or \
                   any(keyword in link_href.lower() for keyword in keywords):
                    
                    # Basic filtering for valid-looking URLs
                    if link_href.startswith(('http://', 'https://', '/')) and \
                       not link_href.startswith(('#', 'javascript:', 'mailto:')) and \
                       not re.search(r'\.(pdf|docx|jpg|png|zip)$', link_href, re.I):
                        
                        full_url = urljoin(base_url, link_href)
                        # Add to candidates, prioritizing shorter, more descriptive text if URL is same
                        if full_url not in candidate_links or len(link_text) < len(candidate_links[full_url]):
                             if len(link_text) > 3 and len(link_text) < 50 : # Reasonable text length
                                candidate_links[full_url] = link_text

        # Refine: if multiple links point to same URL with different text, choose one.
        # For now, the overwrite logic in candidate_links helps.
        # Convert to section_urls format
        for url, text in candidate_links.items():
            parsed_url = urlparse(url)
            if parsed_url.netloc == urlparse(base_url).netloc: # Ensure it's on the same domain
                 # Use a simple name or the link text
                simple_name = text if text else parsed_url.path.strip('/').replace('/', '-')
                if simple_name not in section_urls.values(): # Avoid duplicate names if possible
                    section_urls[simple_name if simple_name else url] = url

        if section_urls:
            logging.info(f"Discovered potential sections: {section_urls}")
        else:
            logging.warning(f"No key sections automatically discovered from {base_url} based on keywords.")
        
        # Manually add known or suspected key sections if auto-discovery is weak
        manual_sections = {
            "CAANZ News": urljoin(base_url, "/news-and-analysis/news"),
            "CAANZ Media Releases": urljoin(base_url, "/news-and-analysis/media-releases"),
            "CAANZ Insights (Acquity)": urljoin(base_url, "/news-and-analysis/acquity-insights"), # Acuity is their magazine
            "CAANZ Policy & Advocacy": urljoin(base_url, "/policy-and-advocacy") # General policy page
        }
        for name, url_val in manual_sections.items():
            if url_val not in section_urls.values(): # Add if URL not already present from discovery
                 section_urls[name] = url_val
        logging.info(f"Added/updated manual sections. Current sections to check: {section_urls}")


    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching homepage for section discovery {base_url}: {e}")
    except Exception as e:
        logging.error(f"Error parsing homepage for section discovery {base_url}: {e}")
    
    return section_urls

def comprehensive_rss_search(base_url, discovered_sections):
    """Conducts a comprehensive RSS feed search."""
    working_rss_feeds = []
    tested_urls = set()

    # 1. Check main page HTML
    main_page_rss = find_rss_links_in_html(base_url, base_url)
    for feed_url in main_page_rss:
        if feed_url not in tested_urls:
            if test_rss_feed(feed_url):
                working_rss_feeds.append(feed_url)
            tested_urls.add(feed_url)

    # 2. Check key section pages HTML for RSS links
    for section_name, section_url in discovered_sections.items():
        logging.info(f"Checking section '{section_name}' at {section_url} for RSS links in its HTML.")
        section_rss_links = find_rss_links_in_html(section_url, base_url)
        for feed_url in section_rss_links:
            if feed_url not in tested_urls:
                if test_rss_feed(feed_url):
                    working_rss_feeds.append(feed_url)
                tested_urls.add(feed_url)
    
    # 3. Try common feed patterns on base URL and section URLs
    common_patterns = ['/feed', '/rss', '/atom.xml', '/feed/', '/rss/', '/atom.xml/']
    urls_to_pattern_test = [base_url] + list(discovered_sections.values())
    
    for page_url_to_test in urls_to_pattern_test:
        for pattern in common_patterns:
            potential_feed_url = urljoin(page_url_to_test, pattern)
            normalized_url_to_test = potential_feed_url.rstrip('/') 
            if normalized_url_to_test not in tested_urls and potential_feed_url not in tested_urls:
                if test_rss_feed(potential_feed_url):
                    working_rss_feeds.append(potential_feed_url)
                tested_urls.add(potential_feed_url)
                tested_urls.add(normalized_url_to_test)

    unique_working_feeds = list(set(working_rss_feeds))
    if unique_working_feeds:
        logging.info(f"Found working RSS feeds: {unique_working_feeds}")
    else:
        logging.warning("No working RSS feeds found after comprehensive search.")
    return unique_working_feeds

# --- Scraping Functions ---
def scrape_caanz_articles(target_url):
    logging.info(f"Attempting to scrape articles from: {target_url}")
    articles_found = []
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        if "login" in response.url.lower() or "error" in response.url.lower():
            if response.url != target_url : 
                logging.warning(f"Redirected from {target_url} to {response.url}. This might be a login/error page. Scraping may fail.")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_containers = soup.find_all('div', class_='listResults__item')
        if not article_containers:
             article_containers = soup.find_all('li', class_='list-group-item')
             if not article_containers:
                 article_containers = soup.find_all('div', class_='sfPublicWrapper')


        logging.info(f"Found {len(article_containers)} potential article containers on {target_url}.")
        processed_urls = set()

        for item in article_containers:
            headline_text = None
            article_url = None
            date_text = None

            link_tag = item.find('a', href=True)
            if not link_tag:
                continue
            
            raw_url = link_tag['href']
            if not raw_url or raw_url.startswith("javascript:") or raw_url == "#":
                continue
            article_url = urljoin(BASE_URL_CAANZ, raw_url.strip())

            if article_url in processed_urls:
                continue

            title_tag = item.find(['h3', 'h4'], class_=re.compile(r'(title|heading|listResults__item-title)', re.I))
            if title_tag:
                headline_text = ' '.join(title_tag.get_text(strip=True, separator=' ').split())
            elif link_tag.get_text(strip=True) and len(link_tag.get_text(strip=True)) > 10:
                headline_text = ' '.join(link_tag.get_text(strip=True, separator=' ').split())
            
            date_tag = item.find(['p', 'span', 'div', 'time'], class_=re.compile(r'(date|meta|publicationdate|listResults__item-meta)', re.I))
            if date_tag:
                date_text = date_tag.get_text(strip=True)

            if headline_text and article_url:
                keywords_relevance = ['tax', 'regulation', 'policy', 'ato', 'government', 'federal budget', 'superannuation', 'sgc', 'gst', 'compliance', 'law', 'reform', 'audit', 'ethics', 'financial reporting']
                is_relevant = any(keyword in headline_text.lower() for keyword in keywords_relevance)
                
                if is_relevant:
                    articles_found.append({
                        'headline': headline_text, 
                        'url': article_url,
                        'date': date_text if date_text else "N/A"
                    })
                    processed_urls.add(article_url)
                    logging.info(f"  Extracted Relevant: '{headline_text}' (Date: {date_text}) - {article_url}")
                else:
                    logging.debug(f"  Skipped (not relevant): '{headline_text}' (Date: {date_text}) - {article_url}")

            if len(articles_found) >= 7: 
                break
        
        if articles_found:
            logging.info(f"Successfully scraped {len(articles_found)} relevant articles from {target_url}.")
        else:
            logging.warning(f"No relevant articles scraped from {target_url} with current selectors or relevance filter.")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
             logging.error(f"Access Denied (403 Forbidden) when scraping {target_url}.")
        else:
            logging.error(f"Error scraping {target_url}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {target_url}: {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during scraping of {target_url}: {e}")
        
    return articles_found[:5]


if __name__ == "__main__":
    logging.info("--- Starting CA ANZ Content Extraction Investigation ---")
    
    discovered_sections = discover_site_sections(BASE_URL_CAANZ)
    key_scrape_targets = {
        "News": urljoin(BASE_URL_CAANZ, "/news-and-analysis/news"),
        "Media Releases": urljoin(BASE_URL_CAANZ, "/news-and-analysis/media-releases"),
        "Policy Submissions": urljoin(BASE_URL_CAANZ, "/policy-and-advocacy/submissions") 
    }
    # Add key_scrape_targets to discovered_sections for comprehensive RSS check, ensuring no duplicates by URL
    existing_urls = set(s_url for s_url in discovered_sections.values())
    for name, url in key_scrape_targets.items():
        if url not in existing_urls:
            discovered_sections[name] = url
            existing_urls.add(url)
    
    working_rss_feeds = comprehensive_rss_search(BASE_URL_CAANZ, discovered_sections)
    extracted_articles = []

    if working_rss_feeds:
        logging.info(f"SUCCESS: Found and validated working RSS feeds for CA ANZ: {working_rss_feeds}")
        feed_to_use = working_rss_feeds[0] 
        logging.info(f"Attempting to extract articles from RSS feed: {feed_to_use}")
        try:
            response = requests.get(feed_to_use, headers=HEADERS, timeout=20)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            if feed.entries:
                for entry in feed.entries:
                    keywords_relevance = ['tax', 'regulation', 'policy', 'ato', 'government', 'federal budget', 'superannuation', 'sgc', 'gst', 'compliance', 'law', 'reform', 'audit', 'ethics', 'financial reporting']
                    is_relevant = any(keyword in entry.title.lower() for keyword in keywords_relevance)
                    if hasattr(entry, 'summary') and not is_relevant:
                         is_relevant = any(keyword in entry.summary.lower() for keyword in keywords_relevance)

                    if is_relevant:
                        extracted_articles.append({'headline': entry.title, 'url': entry.link, 'date': entry.get('published', entry.get('updated', 'N/A'))})
                        if len(extracted_articles) >= 5:
                            break
                logging.info(f"Extracted {len(extracted_articles)} relevant articles via RSS feed {feed_to_use}.")
            else:
                logging.warning(f"RSS feed {feed_to_use} had no entries.")
        except Exception as e:
            logging.error(f"Error processing RSS feed {feed_to_use} for article extraction: {e}")
    else:
        logging.warning("No working RSS feeds found for CA ANZ. Proceeding to scraping attempt.")

    if len(extracted_articles) < 3: 
        logging.info("RSS did not yield enough relevant articles or failed, attempting scraping...")
        
        all_scraped_articles = []
        for section_name, section_url in key_scrape_targets.items():
            scraped_from_section = scrape_caanz_articles(section_url)
            all_scraped_articles.extend(scraped_from_section)
        
        # Deduplicate based on URL from all scraping targets
        final_scraped_list = []
        seen_urls = set(art['url'] for art in extracted_articles) # Include URLs from RSS to avoid duplication
        for article in all_scraped_articles:
            if article['url'] not in seen_urls:
                final_scraped_list.append(article)
                seen_urls.add(article['url'])
        
        # Add to extracted_articles, ensuring not to exceed 5 total
        for article in final_scraped_list:
            if len(extracted_articles) < 5:
                 extracted_articles.append(article)
            else:
                break


    logging.info("\n--- CA ANZ Extraction Investigation Summary ---")
    if working_rss_feeds:
        print("\nDiscovered and Validated RSS Feeds:")
        for feed_url in working_rss_feeds:
            print(f"- {feed_url}")
    else:
        print("\nNo functional RSS feeds were discovered for CA ANZ.")

    if extracted_articles:
        print("\nExtracted Relevant Articles (up to 5):")
        # Simple sort by date string (descending, assuming YYYY-MM-DD or DD Mon YYYY - this is imperfect)
        # A proper solution would parse dates to datetime objects.
        # For now, we'll just present them as found or rely on source ordering.
        for i, article in enumerate(extracted_articles[:5]): # Ensure only up to 5 are printed
            print(f"{i+1}. Headline: {article['headline']}")
            print(f"   URL: {article['url']}")
            print(f"   Date: {article.get('date', 'N/A')}")
    else:
        print("\nNo relevant articles were successfully extracted (either via RSS or scraping).")

    logging.info("--- CA ANZ Content Extraction Investigation Finished ---")
