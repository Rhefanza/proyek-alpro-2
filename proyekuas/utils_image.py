# utils.py
import json
import re
from typing import Any
import pandas as pd
import numpy as np

# cari blok ```json ... ```
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)

def extract_json(text: str) -> Any:
    if not text:
        raise ValueError("Teks kosong, tidak bisa di-parse.")

    # 1) coba cari blok ```json ... ```
    m = JSON_BLOCK_RE.search(text)
    if m:
        raw = m.group(1).strip()
        return json.loads(raw)

    # 2) kalau tidak ada blok markdown, coba langsung
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3) fallback: cari {...} atau [...] pertama di dalam teks
    m2 = re.search(r"(\{.*\}|\[.*\])", stripped, re.DOTALL)
    if m2:
        raw = m2.group(1)
        return json.loads(raw)

    # 4) kalau tetap gagal, baru meledak
    raise ValueError("Tidak bisa menemukan JSON valid di teks respon.")


def normalize_dataframe(obj: Any) -> pd.DataFrame:
    """
    Terima:
      - list[dict], atau
      - {"rows": [...]}.

    Kembalikan pandas.DataFrame.
    """
    if isinstance(obj, dict) and "rows" in obj:
        data = obj["rows"]
    else:
        data = obj

    if not isinstance(data, list):
        raise ValueError("Struktur JSON tidak berupa list baris / 'rows'.")

    df = pd.DataFrame(data)

    # coba konversi angka
    for col in df.columns:
        try:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except Exception:
            pass

    return df  # <- PENTING, pastikan baris ini ada dan tidak ter-indented salah

UNIT_PATTERN = re.compile(r"^\s*([^\d\-+.,]*?)\s*([\d.,]+)\s*([^\d]*)\s*$")

def auto_split_unit_columns(df: pd.DataFrame, min_match_ratio: float = 0.6) -> pd.DataFrame:
    """
    Kolom string yang banyak berisi pola 'unit + angka + unit' akan dipecah jadi:
      - kolom asli -> angka (float)
      - kolom_asli + '_unit' -> satuan
    """
    if df is None:
        raise ValueError("auto_split_unit_columns menerima df=None")

    df = df.copy()

    for col in df.columns:
        if df[col].dtype != object:
            continue

        series = df[col].astype(str)
        matches = series.str.match(UNIT_PATTERN)
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
            unit = (pre + " " + post).strip() or None

            num_clean = num.replace(" ", "")

            if "," in num_clean and "." not in num_clean:
                # format lokal: 22,6 -> 22.6
                num_clean = num_clean.replace(",", ".")
            else:
                # buang koma sebagai pemisah ribuan kasar
                num_clean = num_clean.replace(",", "")

            try:
                val = float(num_clean)
            except ValueError:
                val = np.nan

            values.append(val)
            units.append(unit)

        df[col] = values
        df[col + "_unit"] = units

    return df
