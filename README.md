# Australian Taxation Weekly Newsletter Generator

## Description

This project automates the generation of a weekly HTML newsletter featuring the latest Australian taxation news. It currently fetches articles from TaxBanter's public RSS feed and formats them into a clean, dated HTML file using a predefined template.

## Features

-   Fetches the latest news articles from TaxBanter's RSS feed.
-   Uses a customizable HTML template (`newsletter_template.html`) for the newsletter layout.
-   Generates a new HTML newsletter file with the current date in its filename (e.g., `tax_newsletter_YYYY-MM-DD.html`).
-   Includes basic styling for readability in the generated newsletter.
-   The news fetching and newsletter generation logic is contained within `generate_newsletter.py`.

## Prerequisites/Dependencies

-   **Python 3.x**
-   **Python Libraries:**
    -   `requests`: For making HTTP requests to fetch news feeds.
    -   `feedparser`: For parsing RSS/Atom feeds.
    -   `BeautifulSoup4`: (Though not heavily used by the final `generate_newsletter.py` if RSS is consistently available, it was part of the development scripts and good to have for potential scraping tasks).

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
4.  **Output:** The script will generate an HTML file named `tax_newsletter_YYYY-MM-DD.html` (where `YYYY-MM-DD` is the current date) in the same directory. Open this file in a web browser to view the newsletter.

## File Structure

-   `generate_newsletter.py`: The main Python script that fetches news and generates the HTML newsletter.
-   `newsletter_template.html`: The HTML template file used to structure the newsletter.
-   `extract_ato_news.py`: (Development script) Attempts to extract news from the Australian Taxation Office (ATO) website. *Note: This script faced challenges due to website access restrictions.*
-   `extract_itb_news.py`: (Development script) Attempts to extract news from CPA Australia's INTHEBLACK publication. *Note: This script had limited success due to RSS unavailability and website structure.*
-   `extract_taxbanter_news.py`: (Development script) Successfully extracts news from TaxBanter. The core logic for TaxBanter was integrated into `generate_newsletter.py`.
-   `README.md`: This file, providing information about the project.

## Customization

-   **Changing News Sources:**
    -   To change the news source or add more sources, you would need to modify the `fetch_taxbanter_news()` function (or add new similar functions) within `generate_newsletter.py`. This would involve updating the RSS feed URL and potentially adjusting parsing logic if the new source has a different feed structure or requires web scraping.
-   **Editing the Newsletter Layout:**
    -   The appearance of the newsletter can be changed by editing `newsletter_template.html`. You can modify the CSS within the `<style>` tags or change the HTML structure. Ensure that the placeholders (`{{NEWSLETTER_TITLE}}`, `<!-- {{ARTICLES_LIST_START}} -->...<!-- {{ARTICLES_LIST_END}} -->`, `{{CURRENT_YEAR}}`) are kept intact if you want the script to populate them correctly.

## Troubleshooting

-   **No Articles Fetched / Script Errors:**
    -   **Internet Connection:** Ensure you have an active internet connection.
    -   **RSS Feed Changes:** The TaxBanter RSS feed URL (`https://taxbanter.com.au/feed/`) might change, or the feed structure could be altered. This would require updating the URL or parsing logic in `generate_newsletter.py`.
    -   **Website Blocking/Security:** If attempting to adapt the script for websites that are not TaxBanter (especially those requiring scraping, like the ATO site attempts), you might encounter `403 Forbidden` errors or other blocks due to anti-scraping measures.
    -   **Library Issues:** Ensure all prerequisite libraries are correctly installed.
-   **Template Not Found:**
    -   The script will report an error if `newsletter_template.html` is not in the same directory. Ensure the file is present.
-   **Outdated Content:**
    -   If the newsletter shows old articles, it might be an issue with the source's RSS feed not being updated or a caching issue (though the script itself doesn't implement aggressive caching).

---
This README provides a basic overview. For more advanced modifications, a deeper understanding of Python, HTML, and web scraping/feed parsing might be necessary.
