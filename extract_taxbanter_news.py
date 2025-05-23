import requests
from bs4 import BeautifulSoup
import feedparser
import re
from urllib.parse import urljoin

def get_taxbanter_news_rss():
    """
    Attempts to find and parse an RSS feed from TaxBanter.
    Returns a list of dictionaries with 'headline' and 'url'.
    """
    # TaxBanter is a WordPress site, so /feed is common.
    # Also check other common paths.
    base_url = "https://taxbanter.com.au"
    rss_urls_to_try = [
        f"{base_url}/feed/",
        f"{base_url}/rss/",
        f"{base_url}/atom.xml",
        f"{base_url}/blog/feed/" # If they have a /blog path
    ]
    
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # First, try to find an RSS link tag on the main page or a blog page
    # Common blog page URLs
    pages_to_check_for_rss_link = [base_url, f"{base_url}/blog/", f"{base_url}/insights/"]
    found_rss_link_in_html = False

    for page_url in pages_to_check_for_rss_link:
        if found_rss_link_in_html:
            break
        try:
            print(f"Checking for RSS link tag on: {page_url}")
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for <link type="application/rss+xml" ...> or similar
            rss_link_tag = soup.find('link', type=lambda x: x and ('rss' in x.lower() or 'atom' in x.lower()))
            if rss_link_tag and rss_link_tag.get('href'):
                discovered_rss_url = urljoin(base_url, rss_link_tag['href'])
                print(f"Discovered RSS feed URL via HTML link tag: {discovered_rss_url}")
                # Add this to the list of URLs to try, and prioritize it
                if discovered_rss_url not in rss_urls_to_try:
                    rss_urls_to_try.insert(0, discovered_rss_url)
                found_rss_link_in_html = True # Stop checking other pages
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch {page_url} to check for RSS link: {e}")
        except Exception as e:
            print(f"Error parsing {page_url} for RSS link: {e}")


    for rss_url in rss_urls_to_try:
        try:
            print(f"Attempting to fetch RSS feed from: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if not ('xml' in content_type or 'rss' in content_type or 'atom' in content_type):
                print(f"URL {rss_url} does not appear to be an RSS feed. Content-Type: {content_type}. Skipping.")
                continue

            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"Warning: Feed from {rss_url} may be ill-formed. Bozo bit set with reason: {feed.bozo_exception}")

            if not feed.entries:
                print(f"No entries found in the RSS feed from {rss_url}.")
                # print(f"Raw response content for debugging {rss_url}:")
                # print(response.text[:1000]) # Print first 1000 chars
                continue

            for entry in feed.entries[:10]: # Get top 10 items
                headline = entry.title
                url = entry.link
                news_items.append({'headline': headline, 'url': url})
            
            if news_items:
                print(f"Successfully parsed RSS feed from {rss_url} with {len(news_items)} items.")
                return news_items # Successfully got items

        except requests.exceptions.RequestException as e:
            print(f"Error fetching RSS feed {rss_url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during RSS processing for {rss_url}: {e}")
    
    if not news_items:
         print("Could not fetch or parse any of the attempted/discovered RSS feed URLs.")
    return news_items

def get_taxbanter_news_scraping():
    """
    Attempts to scrape news from TaxBanter website.
    This is a fallback if RSS fails.
    """
    # TaxBanter has an "Insights" or "Blog" section typically.
    # Based on quick browse, https://taxbanter.com.au/insights/ seems to be their blog/articles page.
    url_to_scrape = "https://taxbanter.com.au/insights/"
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Attempting to scrape: {url_to_scrape}")
        response = requests.get(url_to_scrape, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # TaxBanter website structure:
        # Articles are often in <article> tags or <div class="post-item"> or similar.
        # Example observed structure:
        # <article id="post-..." class="... post ...">
        #   <header class="entry-header">
        #       <h2 class="entry-title"><a href="..." rel="bookmark">TITLE</a></h2>
        #   </header>
        #   <div class="entry-summary">...</div>
        # </article>
        # Or sometimes:
        # <div class="elementor-post"> <a class="elementor-post__thumbnail__link" href="..."> <h3 class="elementor-post__title"> <a href="..."> TITLE </a></h3></div>
        
        # Try a few common selectors for WordPress sites / Elementor
        possible_articles = soup.find_all('article', class_=re.compile(r'\bpost\b|\barticle\b'))
        
        if not possible_articles: # If specific article tags not found, try more general Elementor post containers
            possible_articles = soup.find_all('div', class_=re.compile(r'elementor-post|elementor-grid-item|post-item'))

        if not possible_articles: # Fallback to any <article> tag
            possible_articles = soup.find_all('article')

        for item in possible_articles[:15]: # Process up to 15 potential items found
            headline_text = None
            href = None

            # Try to find headline within h2/h3 with class 'entry-title' or 'elementor-post__title'
            headline_tag_h2_entry = item.find(['h2', 'h3'], class_=re.compile(r'entry-title|elementor-post__title'))
            if headline_tag_h2_entry:
                link_tag_inside_h = headline_tag_h2_entry.find('a', href=True)
                if link_tag_inside_h:
                    headline_text = link_tag_inside_h.get_text(strip=True)
                    href = link_tag_inside_h['href']
                else: # Title might not be a link itself, link might be elsewhere
                    headline_text = headline_tag_h2_entry.get_text(strip=True)
            
            # If headline still not found, try any <a> tag with a decent text length inside common heading tags
            if not headline_text:
                heading_tags = item.find(['h2','h3','h4'])
                if heading_tags:
                    link_tag_generic = heading_tags.find('a', href=True)
                    if link_tag_generic and len(link_tag_generic.get_text(strip=True)) > 10 : # Basic check for meaningful text
                        headline_text = link_tag_generic.get_text(strip=True)
                        href = link_tag_generic['href']

            # Fallback: find the first <a> tag with an href in the item as a last resort if no headline structure matched
            if not href:
                link_tag_fallback = item.find('a', href=True)
                if link_tag_fallback:
                    # Try to get a sensible headline from the link text or a nearby heading
                    potential_headline = link_tag_fallback.get_text(strip=True)
                    if len(potential_headline) > 20: # If link text is long enough
                        headline_text = potential_headline
                        href = link_tag_fallback['href']
                    # Could also try to find any h tag near this link if link text is poor

            if headline_text and href:
                # Ensure URL is absolute
                href = urljoin(url_to_scrape, href)
                
                # Avoid duplicates by URL
                if not any(d['url'] == href for d in news_items) and len(headline_text) > 5: # Basic sanity check for headline
                    news_items.append({'headline': headline_text, 'url': href})
                    if len(news_items) >= 10:
                        break 
            
            if len(news_items) >= 10:
                break
        
        if news_items:
            print(f"Found {len(news_items)} items via scraping {url_to_scrape}")
        else:
            print(f"Scraping did not yield structured results from {url_to_scrape} with current selectors.")
            # print("Raw HTML snippet for debugging (first 2000 chars):")
            # print(soup.prettify()[:2000])

    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url_to_scrape}: {e}")
        if "403" in str(e):
            print("Received a 403 Forbidden error. Direct scraping is likely blocked.")
    except Exception as e:
        print(f"An unexpected error occurred during scraping {url_to_scrape}: {e}")
        
    return news_items


if __name__ == "__main__":
    print("Attempting to fetch TaxBanter news...\n")
    
    # Prioritize RSS feed
    taxbanter_news = get_taxbanter_news_rss()
    
    if not taxbanter_news:
        print("\nRSS feed fetch failed or returned no items for TaxBanter. Attempting direct scraping (less reliable)...")
        taxbanter_news = get_taxbanter_news_scraping()

    if taxbanter_news:
        print("\n--- Latest TaxBanter Articles ---")
        for item in taxbanter_news:
            print(f"Headline: {item['headline']}")
            print(f"URL: {item['url']}\n")
        if len(taxbanter_news) < 5:
            print(f"Note: Fewer than 5 articles found. This could be due to limited recent content or scraping limitations.")
    else:
        print("\n--- No TaxBanter news items found ---")
        print("This could be due to several reasons:")
        print("- Network issues or blocked requests.")
        print("- Changes in the TaxBanter website structure, RSS feed URLs, or selectors used for scraping.")
        print("- Anti-scraping measures by the website.")
        print("- The RSS feed URLs attempted might be incorrect or no longer active.")
        print("- If scraping was attempted, the HTML selectors might not match the current site structure, or the site requires JavaScript for full content rendering.")
        print("\nConsiderations for improvement:")
        print("- Manually verify the current RSS feed URL for TaxBanter (e.g. in page source).")
        print("- For scraping: Use browser developer tools to inspect the 'Insights' page and refine HTML selectors for articles, headlines, and links.")

    print("Script finished.")
