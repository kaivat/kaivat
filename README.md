# Australian Taxation Weekly Newsletter Generator

## Description

This project automates the generation of a weekly HTML newsletter featuring the latest Australian taxation news. It currently fetches articles from TaxBanter's public RSS feed and formats them into a clean, dated HTML file using a predefined template. The system is designed to be extensible for multiple news sources.

## Features

-   Fetches the latest news articles from currently active sources (TaxBanter).
-   **Designed for Multiple Sources:** The core script (`generate_newsletter.py`) is structured to easily incorporate multiple news fetching functions.
-   **Article De-duplication:** Combines articles from all active sources and removes duplicates based on URL.
-   **Source Attribution:** Displays the source (e.g., "TaxBanter") for each article in the generated newsletter.
-   Uses a customizable HTML template (`newsletter_template.html`) for the newsletter layout.
-   Generates a new HTML newsletter file with the current date in its filename (e.g., `tax_newsletter_YYYY-MM-DD.html`).
-   Includes basic styling for readability and enhanced error logging in the generation script.

## Prerequisites/Dependencies

-   **Python 3.x**
-   **Python Libraries:**
    -   `requests`: For making HTTP requests to fetch news feeds/pages.
    -   `feedparser`: For parsing RSS/Atom feeds.
    -   `BeautifulSoup4`: Used by some exploratory scripts for HTML parsing; good to have if adapting those.

    You can install these libraries using pip:
    ```bash
    pip install requests feedparser beautifulsoup4
    ```

## How to Run

1.  **Ensure Prerequisites:** Make sure Python 3.x and the required libraries are installed.
2.  **Check Template:** Verify that `newsletter_template.html` is present in the same directory as `generate_newsletter.py`.
3.  **Execute the Script:** Open your terminal or command prompt, navigate to the project directory, and run the following command:
    ```bash
    python generate_newsletter.py
    ```
4.  **Output:** The script will generate an HTML file named `tax_newsletter_YYYY-MM-DD.html` (where `YYYY-MM-DD` is the current date) in the same directory. Open this file in a web browser to view the newsletter. Log messages will be printed to the console.

## File Structure

-   `generate_newsletter.py`: The main Python script that fetches news from active sources, de-duplicates articles, and generates the HTML newsletter.
-   `newsletter_template.html`: The HTML template file used to structure the newsletter.
-   `README.md`: This file.
-   **Exploratory & Development Scripts:**
    -   `extract_ato_news.py`: Attempts to extract news from the ATO website. Outcome: Unsuccessful due to website access restrictions (403 errors).
    -   `extract_itb_news.py`: Initial attempt to extract news from CPA Australia's INTHEBLACK. Outcome: Limited success.
    -   `reevaluate_itb_extraction.py`: Further investigation into INTHEBLACK. Outcome: Unsuccessful due to lack of RSS and challenges with dynamic content.
    -   `extract_taxbanter_news.py`: Successfully extracts news from TaxBanter. Core logic now integrated into `generate_newsletter.py`.
    -   `investigate_caanz_extraction.py`: Investigates CA ANZ for news. Outcome: Unsuccessful due to website access restrictions (403 errors).

## Customization

### Editing the Newsletter Layout
The appearance of the newsletter can be changed by editing `newsletter_template.html`. You can modify the CSS within the `<style>` tags or change the HTML structure. Ensure that the placeholders (`{{NEWSLETTER_TITLE}}`, `<!-- {{ARTICLES_LIST_START}} -->...<!-- {{ARTICLES_LIST_END}} -->`, `{{CURRENT_YEAR}}`) are kept intact for the script to populate them correctly.

### Adding New News Sources
The `generate_newsletter.py` script is designed to accommodate multiple news sources. To add a new source:
1.  **Create a Fetcher Function:** Write a new Python function (similar to `fetch_taxbanter_news` within `generate_newsletter.py`).
    -   This function should handle the specific logic (RSS parsing or web scraping) for the new source.
    -   It must return a list of dictionaries. Each dictionary represents an article and should contain at least:
        -   `'headline'`: The article title.
        -   `'url'`: The direct URL to the article.
        -   `'source_name'`: A string identifying the news source (e.g., "NewSource XYZ").
2.  **Register the Fetcher:** Add your new function to the `active_source_fetchers` list within the `generate_newsletter()` function in `generate_newsletter.py`. For example:
    ```python
    active_source_fetchers = [
        fetch_taxbanter_news,
        your_new_fetcher_function,  # Add your function here
    ]
    ```
    The main script will then automatically call your function, collect its articles, handle errors gracefully, and include its findings in the de-duplication and generation process.

## Troubleshooting & Known Issues

-   **No Articles Fetched / Script Errors:**
    -   **Internet Connection:** Ensure an active internet connection.
    -   **RSS Feed Changes (TaxBanter):** The TaxBanter RSS feed URL (`https://taxbanter.com.au/feed/`) or its structure might change, requiring updates in `fetch_taxbanter_news()`.
    -   **Library Issues:** Ensure all prerequisite libraries are correctly installed.
    -   **Logging:** Check the console output for detailed log messages, which can help diagnose issues with specific sources or steps in the generation process.
-   **Template Not Found:**
    -   The script will log a critical error if `newsletter_template.html` is not in the same directory.
-   **Investigated Sources (Currently Not Usable):**
    -   **ATO (Australian Taxation Office):** Attempts to fetch content were blocked (403 Forbidden errors), likely due to anti-scraping measures.
    -   **CPA Australia (INTHEBLACK):** No reliable public RSS feeds were found. The website appears to use dynamic JavaScript rendering, making content extraction difficult with the current tools.
    -   **CA ANZ (Chartered Accountants ANZ):** Attempts to fetch content were consistently blocked (403 Forbidden errors), likely due to anti-scraping measures.
    Due to these technical limitations, these sources are not currently integrated into the newsletter generation.

---
This README provides a comprehensive overview. For more advanced modifications, a deeper understanding of Python, HTML, and web scraping/feed parsing might be necessary.
