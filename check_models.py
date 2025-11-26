import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API Key dari file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: API Key tidak ditemukan di .env")
else:
    print(f"Menggunakan API Key: {api_key[:5]}...*****")
    genai.configure(api_key=api_key)

    print("\nMencari model yang tersedia...")
    try:
        # List semua model
        for m in genai.list_models():
            # Kita hanya cari model yang bisa 'generateContent' (untuk chat/teks)
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Gagal terhubung ke Google: {e}")