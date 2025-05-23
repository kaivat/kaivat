import requests
from bs4 import BeautifulSoup
import feedparser
import re

def get_itb_news_rss():
    """
    Attempts to find and parse an RSS feed from INTHEBLACK.
    Returns a list of dictionaries with 'headline' and 'url'.
    """
    # Common RSS feed paths for INTHEBLACK (educated guesses)
    # e.g., /rss, /feed, /atom.xml
    # A quick search suggests INTHEBLACK might have a feed.
    # Common pattern: domain/feed or domain/rss
    rss_urls_to_try = [
        "https://intheblack.cpaaustralia.com.au/feed/",
        "https://intheblack.cpaaustralia.com.au/rss/",
        "https://intheblack.cpaaustralia.com.au/atom.xml"
    ]
    
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for rss_url in rss_urls_to_try:
        try:
            print(f"Attempting to fetch RSS feed from: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=15)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Check if the content type suggests it's actually an RSS/XML feed
            content_type = response.headers.get('Content-Type', '').lower()
            if not ('xml' in content_type or 'rss' in content_type or 'atom' in content_type):
                print(f"URL {rss_url} does not appear to be an RSS feed. Content-Type: {content_type}")
                # Try to see if it's an HTML page pointing to an RSS feed
                soup = BeautifulSoup(response.content, 'html.parser')
                rss_link_tag = soup.find('link', type=lambda x: x and 'rss' in x.lower()) or \
                               soup.find('link', type=lambda x: x and 'atom' in x.lower())
                if rss_link_tag and rss_link_tag.get('href'):
                    new_rss_url = rss_link_tag['href']
                    print(f"Found potential RSS link in HTML: {new_rss_url}")
                    # Make sure it's an absolute URL
                    if not new_rss_url.startswith('http'):
                        from urllib.parse import urljoin
                        new_rss_url = urljoin(rss_url, new_rss_url)
                    
                    print(f"Retrying with discovered RSS URL: {new_rss_url}")
                    response = requests.get(new_rss_url, headers=headers, timeout=15)
                    response.raise_for_status()
                else:
                    print(f"No RSS link tag found in HTML of {rss_url} either.")
                    continue # Try next guessed RSS URL

            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"Warning: Feed from {rss_url} may be ill-formed. Bozo bit set with reason: {feed.bozo_exception}")

            if not feed.entries:
                print(f"No entries found in the RSS feed from {rss_url}. The structure might have changed or the URL is incorrect.")
                # print(f"Raw response content for debugging {rss_url}:")
                # print(response.text[:1000])
                continue # Try next guessed RSS URL

            for entry in feed.entries[:10]: # Get top 10 items
                headline = entry.title
                url = entry.link
                
                # Basic filter for relevance - could be improved with more keywords
                keywords = ['tax', 'regulation', 'business', 'ato', 'government', 'policy', 'law', 'compliance', 'finance', 'economy']
                is_relevant = any(keyword in headline.lower() for keyword in keywords)
                
                # Also check summary/content if available
                if not is_relevant and hasattr(entry, 'summary'):
                    is_relevant = any(keyword in entry.summary.lower() for keyword in keywords)
                
                # For this task, let's take latest articles even if not strictly tax/regulation first
                # and then note if filtering was possible.
                # For now, let's just take all of them and mention filtering strategy.
                news_items.append({'headline': headline, 'url': url})
            
            if news_items:
                print(f"Successfully parsed RSS feed from {rss_url} with {len(news_items)} items.")
                return news_items # Successfully got items

        except requests.exceptions.RequestException as e:
            print(f"Error fetching RSS feed {rss_url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during RSS processing for {rss_url}: {e}")
    
    if not news_items:
         print("Could not fetch or parse any of the attempted RSS feed URLs.")
    return news_items

def get_itb_news_scraping():
    """
    Attempts to scrape news from INTHEBLACK website.
    This is a fallback and more likely to break or be blocked.
    """
    url_to_scrape = "https://intheblack.cpaaustralia.com.au/"
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Attempting to scrape: {url_to_scrape}")
        response = requests.get(url_to_scrape, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # INTHEBLACK website structure specific selectors - these will need updating if the site changes.
        # Common patterns: look for <article>, <div> with class like "article-card", "post-summary" etc.
        # Headlines are often in <h2>, <h3> inside these containers.
        # Example: articles = soup.find_all('article', class_='article-listing-item')
        
        # A quick look at INTHEBLACK (via browser) shows articles often in <article> tags
        # or divs with classes like 'content-block', 'article-preview', 'teaser'.
        # Let's try finding <article> tags first.
        
        # Common structure observed:
        # <article class="article-archive-item ...">
        #   <a href="...">
        #     <div class="article-archive-item__image-wrapper">...</div>
        #     <div class="article-archive-item__content">
        #       <h3 class="article-archive-item__title">TITLE HERE</h3>
        #       <div class="article-archive-item__summary">...</div>
        #     </div>
        #   </a>
        # </article>
        
        # Or for featured items, it might be different.
        # Let's try a few selectors.
        # Selector 1: Based on observed archive pages
        possible_articles = soup.find_all('article', class_=re.compile(r'article-archive-item'))
        
        # Selector 2: More generic, looking for common teaser/card patterns
        if not possible_articles:
            possible_articles = soup.find_all('div', class_=re.compile(r'(teaser|card|content-block|article-preview|post-item)'))

        # Selector 3: Fallback to generic <article> tags
        if not possible_articles:
            possible_articles = soup.find_all('article')

        for item in possible_articles[:15]: # Check first 15 potential items
            link_tag = item.find('a', href=True)
            headline_tag = item.find(['h2', 'h3', 'h4'], class_=re.compile(r'(title|headline)'))
            
            if not headline_tag and link_tag: # If no specific title class, try finding h tag inside link
                 headline_tag = link_tag.find(['h2', 'h3', 'h4'])

            if link_tag and headline_tag:
                headline_text = headline_tag.get_text(strip=True)
                href = link_tag['href']
                
                # Ensure URL is absolute
                if not href.startswith('http'):
                    from urllib.parse import urljoin
                    href = urljoin(url_to_scrape, href)
                
                # Basic filter for relevance (can be expanded)
                keywords = ['tax', 'regulation', 'business', 'ato', 'government', 'policy', 'law', 'compliance', 'finance', 'economy']
                is_relevant = any(keyword in headline_text.lower() for keyword in keywords)
                
                # For this task, we'll take the latest articles.
                # If filtering, uncomment: if is_relevant:
                if headline_text and href:
                    # Avoid duplicates by URL
                    if not any(d['url'] == href for d in news_items):
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
        # Often INTHEBLACK might block if it detects scraping (e.g. 403 error)
        if "403" in str(e):
            print("Received a 403 Forbidden error. Direct scraping is likely blocked.")
    except Exception as e:
        print(f"An unexpected error occurred during scraping {url_to_scrape}: {e}")
        
    return news_items


if __name__ == "__main__":
    print("Attempting to fetch INTHEBLACK news...\n")
    
    # Prioritize RSS feed
    itb_news = get_itb_news_rss()
    
    if not itb_news:
        print("\nRSS feed fetch failed or returned no items for INTHEBLACK. Attempting direct scraping (less reliable)...")
        itb_news = get_itb_news_scraping()

    if itb_news:
        print("\n--- Latest INTHEBLACK Articles (focused on relevance if possible) ---")
        for item in itb_news:
            print(f"Headline: {item['headline']}")
            print(f"URL: {item['url']}\n")
        if len(itb_news) < 5:
            print(f"Note: Fewer than 5 articles found. This could be due to strict filtering or limited recent relevant content.")
    else:
        print("\n--- No INTHEBLACK news items found ---")
        print("This could be due to several reasons:")
        print("- Network issues or blocked requests (check User-Agent, IP reputation).")
        print("- Changes in the INTHEBLACK website structure, RSS feed URLs, or selectors used for scraping.")
        print("- Anti-scraping measures by the website.")
        print("- The RSS feed URLs attempted might be incorrect or no longer active.")
        print("- If scraping was attempted, the HTML selectors might not match the current site structure, or the site requires JavaScript to render content.")
        print("\nConsiderations for improvement:")
        print("- Manually verify the current RSS feed URL for INTHEBLACK.")
        print("- For scraping: Use browser developer tools to inspect the website and identify reliable HTML tags/classes for articles, headlines, and links. Pay attention to dynamically loaded content.")

    print("Script finished.")
