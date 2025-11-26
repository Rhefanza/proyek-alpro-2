# insight_engine.py
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

SYSTEM_INSTRUCTION_INSIGHT = """
Anda analis ekonomi dan ekonometrika.

Input: hasil analisis statistik dalam format JSON dari aplikasi (misal: model terpilih,
koefisien, p-value, R-squared, dsb).

Tugas Anda:
- Membuat ringkasan dan insight dalam bahasa Indonesia yang padat dan terstruktur (poin-poin).
- Jelaskan:
  - model apa yang digunakan / terpilih,
  - arah dan kekuatan pengaruh variabel-variabel utama (positif/negatif, kuat/lemah),
  - variabel mana yang signifikan / tidak signifikan (berdasarkan p-value),
  - kualitas model secara umum (R-squared, uji F atau metrik lain jika ada),
  - temuan penting / anomali yang perlu diperhatikan.
- Fokus pada interpretasi, bukan sekadar mengulang angka dari JSON.
- Jangan keluarkan JSON atau kode; hanya narasi teks.
"""

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum di-set di .env")

    model_name = os.getenv("INSIGHT_MODEL_NAME", "gemini-2.5-flash")

    genai.configure(api_key=api_key)
    _MODEL = genai.GenerativeModel(
        model_name,
        system_instruction=SYSTEM_INSTRUCTION_INSIGHT,
    )
    return _MODEL


def generate_insight(analysis_json):
    """
    Dipanggil dari main.py:
        res_dict = json.loads(json_res_string)
        insight_text = insight_engine.generate_insight(res_dict)
    """

    model = _get_model()

    # --- BAGIAN "PLACEHOLDER" LAMA: ambil chosen_model ---
    chosen_model = analysis_json.get("chosen_model")
    if chosen_model:
        intro = (
            f"Berdasarkan analisis, model yang terpilih adalah {chosen_model}. "
            "Berikan interpretasi yang menjelaskan mengapa model ini dipilih, "
            "dan bagaimana pengaruh variabel independen terhadap variabel dependen."
        )
    else:
        intro = (
            "Berikan ringkasan dan insight dari hasil analisis statistik berikut."
        )

    # Ubah dict hasil analisis jadi string JSON rapi
    json_str = json.dumps(analysis_json, ensure_ascii=False, indent=2)

    prompt = (
        f"{intro}\n\n"
        "Berikut hasil analisis dalam format JSON:\n\n"
        f"{json_str}\n\n"
        "Gunakan informasi di atas untuk menyusun insight yang terstruktur (poin-poin)."
    )

    resp = model.generate_content(prompt)
    text = getattr(resp, "text", None) or str(resp)

    # OPTIONAL: jaga-jaga kalau Gemini tidak menyebut nama model sama sekali
    if chosen_model and chosen_model not in text:
        text = (
            f"Berdasarkan analisis, model yang terpilih adalah {chosen_model}.\n\n"
            + text
        )

    return text
