# services/insight_service.py
import google.generativeai as genai

SYSTEM_INSTRUCTION_INSIGHT = """
Anda analis ekonomi. Buat ringkasan dan insight dari data tabel ekonomi.
Fokus pada tren, pertumbuhan, anomali, dan interpretasi singkat.
Jawab dalam bahasa Indonesia yang padat dan terstruktur (poin-poin).
"""

def configure_gemini(api_key: str, model_name: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_INSTRUCTION_INSIGHT)
    return model

def generate_insight_from_df(df, model) -> str:
    # kamu boleh ubah format serialisasi data sesuai prompt di notebook
    csv_like = df.to_csv(index=False)
    prompt = f"Berikan insight dari data berikut (format CSV):\n\n{csv_like}"
    resp = model.generate_content(prompt)
    return getattr(resp, "text", None) or str(resp)
