import requests
# from bs4 import BeautifulSoup # Not strictly needed if only using RSS from TaxBanter, commented out
import feedparser
import re
from urllib.parse import urljoin
from datetime import datetime
import os
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__) # Create a logger for this module

# --- News Fetching Logic ---
def fetch_taxbanter_news():
    """
    Fetches the latest news articles from TaxBanter's RSS feed.
    Returns a list of dictionaries, each with 'headline', 'url', and 'source_name'.
    """
    source_name = "TaxBanter"
    logger.info(f"Attempting to fetch news from {source_name}...")
    base_url = "https://taxbanter.com.au"
    rss_url = f"{base_url}/feed/" 
    
    news_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        logger.debug(f"Requesting RSS feed from: {rss_url} for source {source_name}")
        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status() 
        logger.debug(f"Successfully fetched RSS feed from {rss_url} for {source_name}. Status: {response.status_code}")

        content_type = response.headers.get('Content-Type', '').lower()
        if not ('xml' in content_type or 'rss' in content_type or 'atom' in content_type):
            logger.error(f"URL {rss_url} for {source_name} does not appear to be an RSS feed. Content-Type: {content_type}.")
            return news_items 

        feed = feedparser.parse(response.content)

        if feed.bozo:
            logger.warning(f"Feed from {rss_url} ({source_name}) may be ill-formed. Bozo reason: {feed.bozo_exception}")

        if not feed.entries:
            logger.warning(f"No entries found in the RSS feed from {rss_url} ({source_name}).")
            return news_items

        for entry in feed.entries[:10]: 
            headline = entry.get('title', 'N/A Headline') 
            url = entry.get('link', '#')
            # Add source information
            news_items.append({'headline': headline, 'url': url, 'source_name': source_name})
        
        logger.info(f"Successfully parsed RSS feed for {source_name}. Found {len(news_items)} articles.")
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching RSS feed for {source_name} from {rss_url}: {http_err} - Status code: {http_err.response.status_code}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while fetching RSS feed for {source_name} from {rss_url}: {conn_err}.")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while fetching RSS feed for {source_name} from {rss_url}: {timeout_err}.")
    except requests.exceptions.RequestException as req_err: 
        logger.error(f"An error occurred during requests to {rss_url} for {source_name}: {req_err}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during RSS processing for {source_name} from {rss_url}: {e}")
    
    return news_items

# --- Newsletter Generation Logic ---
def generate_newsletter():
    logger.info("Starting newsletter generation process...")
    template_path = "newsletter_template.html"
    
    # 1. Read HTML Template
    logger.info(f"Reading HTML template from '{template_path}'...")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        logger.info("Successfully read HTML template.")
    except FileNotFoundError:
        logger.error(f"Critical Error: Template file '{template_path}' not found. Cannot generate newsletter.")
        return None
    except IOError as e: 
        logger.exception(f"Critical Error: Could not read template file '{template_path}': {e}")
        return None
    except Exception as e:
        logger.exception(f"Critical Error: An unexpected error occurred while reading template file '{template_path}': {e}")
        return None

    # 2. Fetch News Articles from All Sources
    active_source_fetchers = [
        fetch_taxbanter_news, # Only TaxBanter is active
    ]
    
    all_articles_raw = []
    logger.info(f"Fetching articles from {len(active_source_fetchers)} active source(s)...")
    for fetcher_function in active_source_fetchers:
        source_func_name = fetcher_function.__name__
        try:
            logger.info(f"Calling source: {source_func_name}")
            articles_from_source = fetcher_function()
            if articles_from_source: 
                all_articles_raw.extend(articles_from_source)
                logger.info(f"Received {len(articles_from_source)} articles from {source_func_name}.")
            # No "else: logger.warning..." here, as fetch_fake_source_news raises error before returning anything
        except Exception as e:
            logger.error(f"Error fetching articles from source {source_func_name}: {e}", exc_info=False) 
            logger.info(f"Continuing with next source despite error in {source_func_name}.")


    # 3. De-duplicate Articles
    unique_articles = []
    seen_urls = set()
    if all_articles_raw:
        logger.info(f"Starting de-duplication of {len(all_articles_raw)} raw articles...")
        for article in all_articles_raw:
            article_url = article.get('url')
            if article_url and isinstance(article_url, str):
                if article_url not in seen_urls:
                    unique_articles.append(article)
                    seen_urls.add(article_url)
                else:
                    logger.info(f"Duplicate article found (URL: {article_url}). Skipping.") 
            else:
                logger.warning(f"Article missing URL or URL is not a string, cannot de-duplicate: {article.get('headline', 'N/A')}")
        logger.info(f"Found {len(unique_articles)} unique articles after de-duplication.")
    else:
        logger.info("No raw articles to de-duplicate. This might be due to errors in all sources or no articles from successful sources.")

    if not unique_articles:
        logger.warning("No unique articles found after fetching and de-duplication. Newsletter will have no articles if this is unexpected.")

    # 4. Populate the Template
    logger.info("Populating template with fetched data...")
    try:
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        current_year_str = datetime.now().strftime("%Y")

        newsletter_title = f"Australian Taxation Weekly News - {current_date_str}"
        populated_content = template_content.replace("{{NEWSLETTER_TITLE}}", newsletter_title)
        populated_content = populated_content.replace("{{CURRENT_YEAR}}", current_year_str)

        populated_content = re.sub(r"<!-- {{OPTIONAL_INTRO_TEXT_START}} -->.*?<!-- {{OPTIONAL_INTRO_TEXT_END}} -->", 
                                   "", populated_content, flags=re.DOTALL)

        articles_html = ""
        if unique_articles:
            for article in unique_articles: 
                headline = article.get('headline', 'No Headline').replace('<', '&lt;').replace('>', '&gt;')
                url = article.get('url', '#').replace('"', '&quot;')
                source_name = article.get('source_name', 'N/A Source')
                
                articles_html += f'<div class="article">\n'
                articles_html += f'    <h3><a href="{url}">{headline}</a></h3>\n'
                articles_html += f'    <p class="article-source">Source: {source_name.replace("<", "&lt;").replace(">", "&gt;")}</p>\n' 
                articles_html += f'</div>\n'
        else:
            articles_html = "<p>No articles available for this edition. This could be due to issues with news sources.</p>" # Updated message
            logger.warning("Generating newsletter with 'No articles available' message.")


        populated_content = re.sub(r"<!-- {{ARTICLES_LIST_START}} -->.*?<!-- {{ARTICLES_LIST_END}} -->",
                                   articles_html, populated_content, flags=re.DOTALL)
        logger.info("Template populated successfully.")
    except Exception as e:
        logger.exception("An error occurred during template population:")
        return None

    # 5. Save the Output
    output_filename = f"tax_newsletter_{current_date_str}.html"
    logger.info(f"Attempting to write newsletter to '{output_filename}'...")
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(populated_content)
        logger.info(f"Newsletter generated successfully: {output_filename}")
        return output_filename
    except IOError as e:
        logger.exception(f"Error writing output file '{output_filename}': {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while writing output file '{output_filename}': {e}")
        return None

if __name__ == "__main__":
    logger.info("Newsletter generation script started.")
    
    if not os.path.exists("newsletter_template.html"):
        logger.critical("newsletter_template.html not found. This is required to generate the newsletter. Exiting.")
    else:
        generated_file = generate_newsletter()
        if generated_file:
            logger.info(f"Script finished successfully. Newsletter: {generated_file}")
        else:
            logger.error("Newsletter generation failed. See logs above for details.")
    logger.info("Newsletter generation script finished.")
