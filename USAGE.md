# Using the `html_to_pdf.py` Script on Windows

This guide explains how to use the `html_to_pdf.py` script to convert HTML files to PDF format on a Windows system.

## Prerequisites

1.  **Python Installation:** Ensure you have Python installed on your Windows machine. You can download it from [python.org](https://www.python.org/downloads/). During installation, it's recommended to check the box that says "Add Python to PATH".

2.  **Install `xhtml2pdf` Library:** If you haven't already installed the necessary Python library, open Command Prompt (search for `cmd` in the Start Menu) and run the following command:
    ```bash
    pip install xhtml2pdf
    ```
    This command downloads and installs the `xhtml2pdf` library and its dependencies, which are required by the script.

## Running the Script

To use the `html_to_pdf.py` script, you will run it from the Command Prompt.

### Command Structure

The basic command to run the script is:

```bash
python html_to_pdf.py <input_html_file> <output_pdf_file>
```

### Arguments

*   `<input_html_file>`: This is the path to the HTML file you want to convert.
    *   Replace this with the actual name of your HTML file (e.g., `my_document.html`).
    *   If the HTML file is not in the same directory as the `html_to_pdf.py` script, you will need to provide its full path (e.g., `C:\Users\YourName\Documents\my_document.html`).
*   `<output_pdf_file>`: This is the desired name and path for the generated PDF file.
    *   Replace this with the name you want for your output PDF file (e.g., `converted_document.pdf`).
    *   If you only provide a name, the PDF will be saved in the current directory.
    *   You can also specify a full path to save it elsewhere (e.g., `C:\Users\YourName\Documents\converted_document.pdf`).

### Example

Let's say you have an HTML file named `my_newsletter.html` and you want to convert it to a PDF named `newsletter_output.pdf`.

1.  **Navigate to the Script's Directory (Recommended):**
    *   Open Command Prompt.
    *   Use the `cd` (change directory) command to navigate to the folder where you saved the `html_to_pdf.py` script. For example, if it's in `C:\Scripts`, you would type:
        ```bash
        cd C:\Scripts
        ```
    *   If your `my_newsletter.html` file is also in `C:\Scripts`, you can then run:
        ```bash
        python html_to_pdf.py my_newsletter.html newsletter_output.pdf
        ```

2.  **Using Full Paths (If files are in different locations):**
    *   If `html_to_pdf.py` is in `C:\Scripts`, `my_newsletter.html` is in `C:\Users\YourName\Documents`, and you want the PDF in `C:\Users\YourName\Desktop`, you would run:
        ```bash
        python C:\Scripts\html_to_pdf.py C:\Users\YourName\Documents\my_newsletter.html C:\Users\YourName\Desktop\newsletter_output.pdf
        ```
    *   Alternatively, from any directory in Command Prompt:
        ```bash
        python path\to\html_to_pdf.py path\to\input.html path\to\output.pdf
        ```

### Successful Conversion

If the conversion is successful, the script will print a message like:
`Successfully converted 'input_html_file' to 'output_pdf_file'`

If there are errors (e.g., input file not found, issues with HTML content), the script will print an error message.

## Testing with `sample.html`

A file named `sample.html` is included alongside the `html_to_pdf.py` script. This allows you to quickly test the script's functionality.

**Content of `sample.html`:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML</title>
    <style>
        body { font-family: sans-serif; }
        h1 { color: navy; }
    </style>
</head>
<body>
    <h1>Test Document</h1>
    <p>This is a sample HTML file for testing the conversion to PDF.</p>
</body>
</html>
```

**To convert `sample.html`:**

1.  Ensure `sample.html` and `html_to_pdf.py` are in the same directory.
2.  Open Command Prompt and navigate to this directory.
3.  Run the following command:
    ```bash
    python html_to_pdf.py sample.html sample.pdf
    ```
4.  **Expected Output:** This will create a new file named `sample.pdf` in the same directory. When you open `sample.pdf`, you should see the heading "Test Document" (likely in navy color) and the paragraph "This is a sample HTML file for testing the conversion to PDF." rendered, similar to how it would appear in a web browser.

## Notes

*   Ensure that the input HTML file is well-formed. Complex or malformed HTML/CSS might not convert perfectly.
*   The script uses UTF-8 encoding to read the HTML file.
*   If you encounter issues with image rendering or complex graphics, and you only installed `xhtml2pdf` without `pycairo`, you might consider installing the `pycairo` extra as mentioned in the `HTML_to_PDF_Libraries_Windows.md` guide, though this can sometimes have its own installation challenges on Windows. For most standard newsletters, the basic `xhtml2pdf` installation should suffice.
