# utils.py
"""
Folder untuk fungsionalitas tambahan dan fitur mendatang.
"""

def ocr_image_to_csv(image_file):
    """
    (FITUR MENDATANG)
    Menerima file gambar dan mengekstrak tabel data darinya.
    
    Library yang mungkin digunakan:
    - Pillow (PIL) untuk memuat dan memproses gambar.
    - Pytesseract (Tesseract-OCR) untuk mengekstrak teks.
    - Logika parsing kustom untuk mengubah teks mentah OCR menjadi struktur CSV.
    """
    print("Fitur OCR-to-CSV belum diimplementasikan.")
    # Contoh logika:
    # 1. Buka gambar (image_file) dengan PIL.
    # 2. Gunakan pytesseract.image_to_string() untuk mendapatkan teks.
    # 3. Parse teks untuk menemukan header tabel dan baris data.
    # 4. Buat DataFrame pandas dan simpan sebagai CSV.
    # 5. Kembalikan path ke file CSV baru.
    return None

def generate_additional_insights(analysis_json):
    """
    (FITUR MENDATANG)
    Menerima JSON hasil analisis dan menambahkan "penjelasan" atau "insight"
    yang mudah dipahami manusia.
    
    Metode yang mungkin digunakan:
    - Sistem berbasis aturan (Rule-based):
        - if p_value < 0.05 -> "Variabel X secara statistik signifikan..."
        - if vif > 10 -> "Terdapat masalah multikolinearitas..."
    - Model Generatif (LLM):
        - Mengirim ringkasan statistik ke API LLM dan meminta penjelasan.
    """
    print("Fitur insight tambahan belum diimplementasikan.")
    # Contoh logika berbasis aturan:
    insights = []
    
    # if analysis_json.get("chosen_model") == "Fixed Effects Model (FEM)":
    #     insights.append("Model Fixed Effects (FEM) dipilih, artinya ada karakteristik unik per individu/perusahaan yang memengaruhi hasil.")
        
    return insights