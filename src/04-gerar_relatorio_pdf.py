import pandas as pd
import requests
from io import BytesIO
from PIL import Image
from fpdf import FPDF

# Assuming your dataframe is named df
# Load your dataframe here (df = pd.read_csv, pd.read_excel, etc.)

class PDF(FPDF):
    def header(self):
        # Remove the header for all pages
        pass
    
    def first_page_content(self, unique_materials):
        # Add the introductory text on the first page
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, "Para produzir o look, foram encontrados estes materiais:")
        self.ln(10)
        
        # Add the unique materials
        self.set_font('Arial', 'B', 10)
        for material in unique_materials:
            self.cell(0, 10, f"- {material}", ln=True)
        self.ln(15)

    def add_material_section(self, material, data):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Material: {material}', ln=True)
        self.ln(10)
        self.set_font('Arial', '', 10)
        
        for idx, row in data.iterrows():
            self.multi_cell(0, 10, f"Product Link: {row['produto_link']}")
            self.ln(3)
            try:
                # Fetch the image
                response = requests.get(row['subproduct_img_url'])
                image = Image.open(BytesIO(response.content))

                # Save the image temporarily and insert it into the PDF
                image_path = f"temp/temp_image_{idx}.jpg"
                image.save(image_path)
                self.image(image_path, w=50, h=50)
                self.ln(55)
            except Exception as e:
                self.multi_cell(0, 10, "Image could not be loaded.")
                self.ln(5)

# Create a PDF instance
pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# First Page: Add the introductory text and list of unique materials
df = pd.read_csv('src/top_5_por_material.csv')
unique_materials = df['material'].unique()
pdf.first_page_content(unique_materials)

# Add a new page for each material's section

grouped = df.groupby('material')

for material, group in grouped:
    pdf.add_page()
    pdf.add_material_section(material, group.head(5))

# Output the PDF
pdf_output_path = "material_products_report.pdf"
pdf.output(pdf_output_path)

print(f"PDF saved at: {pdf_output_path}")
