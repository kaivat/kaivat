import requests
# from bs4 import BeautifulSoup # Not strictly needed if only using RSS from TaxBanter, commented out
import feedparser
import re
from urllib.parse import urljoin
from datetime import datetime
import os
import logging

# --- Logging Configuration ---
# Configure logging to output to console.
# In a more complex app, this might log to a file.
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- News Fetching Logic (adapted from extract_taxbanter_news.py) ---
def fetch_taxbanter_news():
    """
    Fetches the latest news articles from TaxBanter's RSS feed.
    Returns a list of dictionaries, each with 'headline' and 'url'.
    """
    logging.info("Attempting to fetch TaxBanter news...")
    base_url = "https://taxbanter.com.au"
    rss_url = f"{base_url}/feed/" 
    
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        logging.debug(f"Requesting RSS feed from: {rss_url}")
        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
        logging.debug(f"Successfully fetched RSS feed from {rss_url}. Status: {response.status_code}")

        content_type = response.headers.get('Content-Type', '').lower()
        if not ('xml' in content_type or 'rss' in content_type or 'atom' in content_type):
            logging.error(f"URL {rss_url} does not appear to be an RSS feed. Content-Type: {content_type}.")
            return news_items 

        feed = feedparser.parse(response.content)

        if feed.bozo:
            # feed.bozo_exception often contains useful info about parsing errors
            logging.warning(f"Feed from {rss_url} may be ill-formed. Bozo bit set with reason: {feed.bozo_exception}")

        if not feed.entries:
            logging.warning(f"No entries found in the RSS feed from {rss_url}. The feed might be empty or structure changed.")
            return news_items

        for entry in feed.entries[:10]: # Get top 10 items
            headline = entry.get('title', 'N/A Headline') # Use .get for safer access
            url = entry.get('link', '#')
            news_items.append({'headline': headline, 'url': url})
        
        logging.info(f"Successfully parsed RSS feed. Found {len(news_items)} articles.")
        
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching RSS feed {rss_url}: {http_err} - Status code: {http_err.response.status_code}")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred while fetching RSS feed {rss_url}: {conn_err}. Check network connection.")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred while fetching RSS feed {rss_url}: {timeout_err}.")
    except requests.exceptions.RequestException as req_err: # Catch any other requests error
        logging.error(f"An error occurred during requests to {rss_url}: {req_err}")
    except Exception as e:
        # Catching other potential errors during feed parsing or processing
        logging.exception(f"An unexpected error occurred during RSS processing for {rss_url}: {e}")
    
    return news_items

# --- Newsletter Generation Logic ---
def generate_newsletter():
    logging.info("Starting newsletter generation process...")
    template_path = "newsletter_template.html"
    
    # 1. Read HTML Template
    logging.info(f"Reading HTML template from '{template_path}'...")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        logging.info("Successfully read HTML template.")
    except FileNotFoundError:
        logging.error(f"Critical Error: Template file '{template_path}' not found. Cannot generate newsletter.")
        return None
    except IOError as e: # Catch other IO errors like permission issues
        logging.exception(f"Critical Error: Could not read template file '{template_path}': {e}")
        return None
    except Exception as e:
        logging.exception(f"Critical Error: An unexpected error occurred while reading template file '{template_path}': {e}")
        return None

    # 2. Fetch News Articles
    articles = fetch_taxbanter_news()

    if not articles:
        logging.warning("No articles fetched. Newsletter will be generated with a 'no articles' message.")
        # Proceed to generate with empty articles list, or handle as error

    # 3. Populate the Template
    logging.info("Populating template with fetched data...")
    try:
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        current_year_str = datetime.now().strftime("%Y")

        newsletter_title = f"Australian Taxation Weekly News - {current_date_str}"
        populated_content = template_content.replace("{{NEWSLETTER_TITLE}}", newsletter_title)
        populated_content = populated_content.replace("{{CURRENT_YEAR}}", current_year_str)

        populated_content = re.sub(r"<!-- {{OPTIONAL_INTRO_TEXT_START}} -->.*?<!-- {{OPTIONAL_INTRO_TEXT_END}} -->", 
                                   "", populated_content, flags=re.DOTALL)

        articles_html = ""
        if articles:
            for article in articles:
                headline = article.get('headline', 'No Headline').replace('<', '&lt;').replace('>', '&gt;')
                url = article.get('url', '#').replace('"', '&quot;')
                articles_html += f'<div class="article">\n'
                articles_html += f'    <h3><a href="{url}">{headline}</a></h3>\n'
                articles_html += f'</div>\n'
        else:
            articles_html = "<p>No articles available for this edition.</p>"

        populated_content = re.sub(r"<!-- {{ARTICLES_LIST_START}} -->.*?<!-- {{ARTICLES_LIST_END}} -->",
                                   articles_html, populated_content, flags=re.DOTALL)
        logging.info("Template populated successfully.")
    except Exception as e:
        logging.exception("An error occurred during template population:")
        return None


    # 4. Save the Output
    output_filename = f"tax_newsletter_{current_date_str}.html"
    logging.info(f"Attempting to write newsletter to '{output_filename}'...")
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(populated_content)
        logging.info(f"Newsletter generated successfully: {output_filename}")
        return output_filename
    except IOError as e:
        logging.exception(f"Error writing output file '{output_filename}': {e}")
        return None
    except Exception as e:
        logging.exception(f"An unexpected error occurred while writing output file '{output_filename}': {e}")
        return None

if __name__ == "__main__":
    logging.info("Newsletter generation script started.")
    
    if not os.path.exists("newsletter_template.html"):
        logging.critical("newsletter_template.html not found. This is required to generate the newsletter. Exiting.")
    else:
        generated_file = generate_newsletter()
        if generated_file:
            logging.info(f"Script finished successfully. Newsletter: {generated_file}")
        else:
            logging.error("Newsletter generation failed. See logs above for details.")
    logging.info("Newsletter generation script finished.")
