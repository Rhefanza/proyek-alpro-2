# pdf_generator.py
from fpdf import FPDF
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'EconoVision - Data Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(analysis_result, output_path):
    """
    Membuat file PDF berdasarkan JSON hasil analisis.
    """
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Judul Model
    model_name = analysis_result.get('chosen_model') or analysis_result.get('model_type') or "Unknown Model"
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Result: {model_name}", 0, 1)
    pdf.ln(5)

    # 2. Tampilkan Insight (Jika ada)
    # Ini mengambil dari 'interpretation' nanti
    if 'interpretation' in analysis_result:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Insight:", 0, 1)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, str(analysis_result.get('interpretation', '-')))
        pdf.ln(10)

    # 3. Tampilkan Tabel Statistik (Summary Text)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Statistical Summary:", 0, 1)
    pdf.set_font("Courier", size=9) # Font monospace agar tabel rapi
    
    summary = ""
    if 'final_model_estimation' in analysis_result:
        summary = analysis_result['final_model_estimation'].get('summary_table', '')
    elif 'model_estimation' in analysis_result:
        summary = analysis_result['model_estimation'].get('summary_table', '')
        
    # Bersihkan karakter aneh jika ada
    clean_summary = summary.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_summary)

    # Simpan
    pdf.output(output_path)
    return output_path