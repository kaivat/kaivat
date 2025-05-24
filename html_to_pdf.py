# html_to_pdf.py
# Description: Converts an HTML file to a PDF file using xhtml2pdf.
# Usage: python html_to_pdf.py <input_html_path> <output_pdf_path>

import sys
from xhtml2pdf import pisa

def convert_html_to_pdf(source_html_path, output_pdf_path):
    """
    Converts an HTML file to a PDF file.

    Args:
        source_html_path (str): The path to the source HTML file.
        output_pdf_path (str): The path where the generated PDF should be saved.

    Returns:
        bool: True if conversion was successful, False otherwise.
    """
    try:
        # Open the source HTML file for reading
        with open(source_html_path, "r", encoding="utf-8") as source_file:
            source_html = source_file.read()
    except FileNotFoundError:
        print(f"Error: Input HTML file not found at '{source_html_path}'")
        return False
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False

    try:
        # Open the output PDF file for writing in binary mode
        with open(output_pdf_path, "w+b") as result_file:
            # Create the PDF
            # pisa.CreatePDF() returns a pisaContextObject
            # The first argument is the HTML content.
            # The second argument is the output file object.
            pdf_status = pisa.CreatePDF(
                source_html,  # HTML content
                dest=result_file  # File object to write to
            )

        # pisa.CreatePDF returns an object with an 'err' attribute.
        # If 'err' is 0, it means success. Otherwise, it indicates an error.
        if pdf_status.err:
            print(f"Error during PDF conversion: {pdf_status.err}")
            return False
        
        print(f"Successfully converted '{source_html_path}' to '{output_pdf_path}'")
        return True

    except Exception as e:
        print(f"An unexpected error occurred during PDF conversion: {e}")
        return False

if __name__ == "__main__":
    # Check if the correct number of command-line arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python html_to_pdf.py <input_html_path> <output_pdf_path>")
        sys.exit(1)

    # Get the input and output file paths from command-line arguments
    input_html = sys.argv[1]
    output_pdf = sys.argv[2]

    # Perform the conversion
    if not convert_html_to_pdf(input_html, output_pdf):
        sys.exit(1)
    
    sys.exit(0)
