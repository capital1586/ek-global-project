import pdfplumber
import csv

def pdf_to_csv(pdf_path, csv_path):
    # Open the PDF file
    with pdfplumber.open(pdf_path) as pdf:
        # Open the CSV file for writing
        with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            
            # Iterate through each page in the PDF
            for page in pdf.pages:
                # Extract text from the page
                text = page.extract_text()
                
                # If text is found, split it into lines and write each line to the CSV
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        writer.writerow([line])  # Write each line as a row in the CSV

# Example usage
pdf_path = '/home/faisal/ekg-global/178 (46).PDF'  # Path to your PDF file
csv_path = '/home/faisal/ekg-global/output.csv'      # Path to save the CSV file
pdf_to_csv(pdf_path, csv_path)

print(f"PDF text has been extracted to {csv_path}")