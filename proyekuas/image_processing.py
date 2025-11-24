# image_processing.py
import pandas as pd
import os

def process_image_to_data(image_path):
    """
    FUNGSI PLACEHOLDER UNTUK TIM OCR.
    Tugas: Menerima path gambar -> Mengembalikan DataFrame Pandas.
    """
    
    print(f"Memproses gambar dari: {image_path}")
    
    # --- AREA KERJA TIM ANDA DI SINI ---
    # 1. Load Image using OpenCV/PIL
    # 2. Perform OCR (Tesseract/EasyOCR)
    # 3. Parse text to Table
    # -----------------------------------

    # SEMENTARA: Kita return Dummy Data agar Frontend jalan
    # Nanti hapus ini dan ganti dengan hasil OCR asli
    dummy_data = {
        'perusahaan': ['A', 'B', 'C', 'D', 'E'],
        'tahun': [2020, 2021, 2022, 2023, 2024],
        'pendapatan': [100, 120, 150, 180, 200],
        'beban': [50, 60, 70, 80, 90]
    }
    df = pd.DataFrame(dummy_data)
    
    return df