import json
import re
from typing import Any
import pandas as pd
import numpy as np

# Regex untuk mencari blok ```json ... ``` atau [...]
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)

def extract_json(text: str) -> Any:
    """
    Mengekstrak objek JSON dari string teks yang mungkin kotor (berisi markdown).
    """
    if not text:
        raise ValueError("Teks kosong, tidak bisa di-parse.")

    # 1) Coba cari blok markdown ```json ... ```
    m = JSON_BLOCK_RE.search(text)
    if m:
        raw = m.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass # Lanjut ke metode berikutnya jika gagal

    # 2) Coba langsung parse string (siapa tahu sudah bersih)
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3) Fallback: Cari kurung kurawal {...} atau kurung siku [...] pertama
    # Ini berguna jika AI memberikan teks pengantar sebelum JSON
    m2 = re.search(r"(\{.*\}|\[.*\])", stripped, re.DOTALL)
    if m2:
        raw = m2.group(1)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

    # 4) Menyerah
    raise ValueError(f"Tidak bisa menemukan JSON valid. Raw text: {text[:50]}...")


def normalize_dataframe(obj: Any) -> pd.DataFrame:
    """
    Mengubah list of dicts atau struktur {'rows': [...]} menjadi DataFrame.
    Juga membersihkan format angka string (misal '1,000' -> 1000).
    """
    # Normalisasi struktur input
    if isinstance(obj, dict) and "rows" in obj:
        data = obj["rows"]
    elif isinstance(obj, list):
        data = obj
    else:
        # Jika format tidak dikenal, coba bungkus jadi list
        data = [obj] if obj else []

    if not isinstance(data, list):
        raise ValueError("Struktur JSON tidak valid untuk tabel (bukan list).")

    df = pd.DataFrame(data)

    # Pembersihan Angka: Coba konversi setiap kolom string ke numerik
    for col in df.columns:
        if df[col].dtype == object: # Hanya proses kolom tipe Object (String)
            try:
                # Buat salinan untuk dibersihkan
                cleaned_col = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False) # Hapus koma ribuan
                    .str.strip()
                )
                # Coba ubah ke angka
                df[col] = pd.to_numeric(cleaned_col, errors="ignore")
            except Exception:
                pass # Jika gagal, biarkan apa adanya

    # Normalisasi Header: Lowercase & Underscore
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    return df


# Pola Regex untuk mendeteksi "Unit Angka Unit" (misal: "Rp 50.000" atau "50 kg")
UNIT_PATTERN = re.compile(r"^\s*([^\d\-+.,]*?)\s*([\d.,]+)\s*([^\d]*)\s*$")

def auto_split_unit_columns(df: pd.DataFrame, min_match_ratio: float = 0.6) -> pd.DataFrame:
    """
    Mendeteksi kolom yang berisi angka bercampur satuan, lalu memecahnya.
    Contoh: Kolom "Harga" berisi ["Rp 10.000", "Rp 20.000"]
    Hasil: Kolom "Harga" jadi [10000, 20000] (Float), kolom baru "Harga_unit" jadi ["Rp", "Rp"].
    """
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    for col in df.columns:
        # Hanya cek kolom string
        if df[col].dtype != object:
            continue

        # Cek berapa persen baris yang cocok dengan pola "Unit Angka"
        series = df[col].astype(str)
        matches = series.str.match(UNIT_PATTERN)
        
        # Jika kurang dari 60% data cocok, anggap bukan kolom bersatuan
        if matches.mean() < min_match_ratio:
            continue

        values = []
        units = []

        for s in series:
            m = UNIT_PATTERN.match(s)
            if not m:
                values.append(np.nan)
                units.append(None)
                continue

            pre, num, post = m.groups()
            # Satuan bisa di depan (Rp) atau di belakang (kg)
            unit = (pre + " " + post).strip() or None

            # Bersihkan angka
            num_clean = num.replace(" ", "") # Hapus spasi dalam angka

            # Logika desimal Indonesia vs Internasional
            if "," in num_clean and "." not in num_clean:
                # Asumsi format Indo: 22,6 -> 22.6
                num_clean = num_clean.replace(",", ".")
            else:
                # Asumsi format Internasional: 1,000 -> 1000
                num_clean = num_clean.replace(",", "")

            try:
                val = float(num_clean)
            except ValueError:
                val = np.nan

            values.append(val)
            units.append(unit)

        # Update DataFrame
        df[col] = values
        # Jika ada satuan yang terdeteksi, simpan di kolom baru
        if any(units):
            df[f"{col}_unit"] = units

    return df