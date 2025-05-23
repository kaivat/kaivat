import requests
from bs4 import BeautifulSoup
import feedparser
import re

def get_ato_news_rss():
    """
    Attempts to find and parse an RSS feed from the ATO website.
    Returns a list of dictionaries with 'headline' and 'url'.
    """
    # Common RSS feed paths/names for ATO (these are educated guesses)
    # The ATO has historically had media releases available via RSS.
    # A common pattern is to look for "Media releases"
    # Let's try a known historical pattern for ATO RSS feeds.
    # The new website might use a different structure or API.
    # A general search reveals that the ATO does provide RSS feeds.
    # One such URL is for media releases:
    rss_url_media_releases = "https://www.ato.gov.au/Media-centre/RSS-feed---Media-releases/"
    
    # Another potential one for more general news/updates if media releases isn't enough
    # For now, focusing on Media Releases as it's a common official channel.

    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Attempting to fetch RSS feed from: {rss_url_media_releases}")
        # It's good practice to set a timeout for requests
        response = requests.get(rss_url_media_releases, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors

        feed = feedparser.parse(response.content)

        if feed.bozo:
            print(f"Warning: Feed may be ill-formed. Bozo bit set with reason: {feed.bozo_exception}")

        if not feed.entries:
            print("No entries found in the RSS feed. The structure might have changed or the URL is incorrect.")
            # Try to print some raw response content if parsing fails to help diagnose
            # print("Raw response content for debugging RSS feed:")
            # print(response.text[:1000]) # Print first 1000 chars
            return news_items # Return empty list

        for entry in feed.entries[:10]: # Get top 10 items
            headline = entry.title
            url = entry.link
            news_items.append({'headline': headline, 'url': url})
        
        if not news_items:
            print("Successfully parsed RSS feed, but it contained no entries.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        # Fallback to trying to find RSS link on a media page if direct guess fails
        # This is complex as it requires another request and parsing.
        # For now, we'll rely on the direct RSS URL guess.
        print("Could not fetch or parse the primary RSS feed URL.")
    except Exception as e:
        print(f"An unexpected error occurred during RSS processing: {e}")

    return news_items

def get_ato_news_scraping():
    """
    Attempts to scrape news from the ATO website.
    This is a fallback and more likely to break or be blocked.
    """
    # Try common pages where news/updates might be listed.
    # The ATO website structure can be complex and change.
    # Let's target the general "Media Centre" as a starting point.
    urls_to_try = [
        "https://www.ato.gov.au/media-centre/",
        "https://www.ato.gov.au/media-centre/media-releases/",
        "https://www.ato.gov.au/About-ATO/ATO-newsroom/" # Another common pattern for news
    ]
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for url_to_scrape in urls_to_try:
        try:
            print(f"Attempting to scrape: {url_to_scrape}")
            response = requests.get(url_to_scrape, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # ATO website structure specific selectors - these will need updating if the site changes.
            # This is highly dependent on the current ATO website structure.
            # Common patterns: look for <h2> or <h3> tags with <a> inside, or list items.
            # Example: articles = soup.find_all('div', class_='news-item-class') # Fictional class
            
            # Let's try a more generic search for links within main content areas
            # This is a very broad search and might pick up non-news items.
            # ATO's structure uses complex class names, often dynamically generated.
            # A quick inspection of ATO media releases (e.g., via browser dev tools)
            # might show list items (<li>) with links (<a>) and headlines (often in the link text or a span).

            # Example structure seen on some ATO pages:
            # <div class="ato-dynamic-list"><ul><li><a href="..."><h4>Headline</h4>...</a></li></ul></div>
            # Or table rows <tr><td><a href="..">Headline</a></td>...</tr>
            
            # Looking for list items with links seems like a reasonable generic start
            # This is a guess and likely needs refinement after inspecting the actual page structure if accessible.
            possible_articles = soup.find_all('li') 
            if not possible_articles: # If no <li>, maybe tables?
                possible_articles = soup.find_all('tr')

            for item in possible_articles:
                link_tag = item.find('a', href=True)
                if link_tag:
                    headline_text = ""
                    # Try to find a heading tag within the link or its parent
                    h_tag = link_tag.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if h_tag:
                        headline_text = h_tag.get_text(strip=True)
                    else: # Otherwise, use the link text itself, clean it up
                        headline_text = link_tag.get_text(strip=True)
                    
                    # Basic filter for relevance - very crude
                    if len(headline_text) > 20 and ("news" in headline_text.lower() or "release" in headline_text.lower() or "update" in headline_text.lower() or "speech" in headline_text.lower() or "alert" in headline_text.lower()):
                        href = link_tag['href']
                        # Ensure URL is absolute
                        if not href.startswith('http'):
                            href = "https://www.ato.gov.au" + href if href.startswith('/') else "https://www.ato.gov.au/" + href
                        
                        # Avoid duplicates by URL
                        if not any(d['url'] == href for d in news_items):
                            news_items.append({'headline': headline_text, 'url': href})
                            if len(news_items) >= 10:
                                break # Stop if we have enough
            
            if news_items:
                print(f"Found {len(news_items)} items via scraping {url_to_scrape}")
                return news_items # Return if we found something

        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url_to_scrape}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during scraping {url_to_scrape}: {e}")
        
        if news_items: # Should not be strictly necessary here, but good for clarity
            break

    if not news_items:
        print("Scraping did not yield any results or failed for all attempted URLs.")
    return news_items


if __name__ == "__main__":
    print("Attempting to fetch ATO news...\n")
    
    # Prioritize RSS feed as it's more reliable
    ato_news = get_ato_news_rss()
    
    if not ato_news:
        print("\nRSS feed fetch failed or returned no items. Attempting direct scraping (less reliable)...")
        # Note: Scraping ATO.gov.au is challenging due to its dynamic nature and security.
        # The selectors used in get_ato_news_scraping() are very generic and may not work.
        # This is included as a fallback as per requirements but has a low chance of success without specific, up-to-date selectors.
        ato_news = get_ato_news_scraping()

    if ato_news:
        print("\n--- Latest ATO News/Updates ---")
        for item in ato_news:
            print(f"Headline: {item['headline']}")
            print(f"URL: {item['url']}\n")
    else:
        print("\n--- No ATO news items found ---")
        print("This could be due to several reasons:")
        print("- Network issues or blocked requests (check User-Agent, IP reputation).")
        print("- Changes in the ATO website structure or RSS feed URLs.")
        print("- Anti-scraping measures by the ATO website.")
        print("- The RSS feed URL used might be outdated or incorrect.")
        print("- If scraping was attempted, the HTML selectors are likely not matching the current site structure.")
        print("\nConsiderations for improvement:")
        print("- Manually verify the current RSS feed URL for ATO media releases.")
        print("- For scraping: Use browser developer tools to inspect the media/news pages and identify reliable HTML tags/classes for headlines and links.")
        print("- Implement more robust error handling and logging.")

    print("Script finished.")
