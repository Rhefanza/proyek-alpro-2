# image_processing.py
import os

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

from utils_image import extract_json, normalize_dataframe, auto_split_unit_columns

SYSTEM_INSTRUCTION_IMAGE = """
Anda diberi gambar/PDF berisi tabel (bisa tulisan tangan).

Tugas Anda:
- Ekstrak tabel menjadi JSON dengan struktur:
  {
    "rows": [
      { "kolom1": nilai1, "kolom2": nilai2, ... },
      ...
    ]
  }

Aturan:
- Anggap baris pertama tabel sebagai HEADER (nama kolom).
- Gunakan teks di header sebagai nama field, boleh:
  - trim spasi di awal/akhir,
  - di-lowercase,
  - spasi diganti underscore.
- Setiap baris berikutnya adalah 1 objek dalam "rows".
- Jika suatu sel kosong, gunakan null.
- Jangan tambahkan penjelasan lain di luar JSON.
- Jangan kirim markdown, hanya JSON murni.
"""


def _get_model(model_name: str = "gemini-2.5-flash"):
    """Inisialisasi model sekali (lazy)."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum di-set di .env")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name,
        system_instruction=SYSTEM_INSTRUCTION_IMAGE,
    )
    return model


# cache model biar tidak configure terus-terusan
_MODEL = None


def process_image_to_data(image_path: str) -> pd.DataFrame:
    """
    Fungsi yang dipakai main.py:
    - Terima path gambar
    - Panggil Gemini
    - Kembalikan DataFrame
    """
    global _MODEL
    if _MODEL is None:
        _MODEL = _get_model()

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Gambar tidak ditemukan: {image_path}")

    gfile = genai.upload_file(image_path)
    resp = _MODEL.generate_content(
        [gfile, "Ekstrak tabel sesuai instruksi dan kembalikan JSON saja."]
    )
    text = getattr(resp, "text", None) or str(resp)

    obj = extract_json(text)
    df = normalize_dataframe(obj)
    df = auto_split_unit_columns(df)

    return df



    # # SEMENTARA: Kita return Dummy Data agar Frontend jalan
    # # Nanti hapus ini dan ganti dengan hasil OCR asli
    # dummy_data = {
    #     'perusahaan': ['A', 'B', 'C', 'D', 'E'],
    #     'tahun': [2020, 2021, 2022, 2023, 2024],
    #     'pendapatan': [100, 120, 150, 180, 200],
    #     'beban': [50, 60, 70, 80, 90]
    # }
    # df = pd.DataFrame(dummy_data)
    
    # return df