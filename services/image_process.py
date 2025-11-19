# services/image_process.py
import google.generativeai as genai
import pandas as pd
from utils import extract_json, normalize_dataframe, auto_split_unit_columns

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

def configure_gemini(api_key: str, model_name: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name,
        system_instruction=SYSTEM_INSTRUCTION_IMAGE
    )
    return model

def extract_table_from_file(file_path: str, model) -> pd.DataFrame:
    gfile = genai.upload_file(file_path)
    resp = model.generate_content(
        [gfile, "Ekstrak tabel sesuai instruksi dan kembalikan JSON saja."]
    )
    text = getattr(resp, "text", None) or str(resp)

    obj = extract_json(text)
    df = normalize_dataframe(obj)              
    df = auto_split_unit_columns(df)           
    return df
