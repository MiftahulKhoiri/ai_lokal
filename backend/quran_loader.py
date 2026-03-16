import os
import json
import re

QURAN_DIR = "knowledge/quran"

QURAN = []
SURAH_INDEX = {}

def load_quran():

    global QURAN, SURAH_INDEX

    for file in os.listdir(QURAN_DIR):

        if file.endswith(".json"):

            path = os.path.join(QURAN_DIR, file)

            with open(path, "r", encoding="utf-8") as f:

                data = json.load(f)

                for surah_id, surah in data.items():

                    SURAH_INDEX[surah["name_latin"].lower()] = int(surah_id)

                    for ayah_id, text in surah["text"].items():

                        QURAN.append({
                            "surah": int(surah_id),
                            "surah_name": surah["name_latin"],
                            "ayah": int(ayah_id),
                            "text": text
                        })

    print(f"[INFO] Quran loaded: {len(QURAN)} ayat")



def get_ayah(surah, ayah):

    for a in QURAN:

        if a["surah"] == surah and a["ayah"] == ayah:

            return f"QS {surah}:{ayah} ({a['surah_name']})\n{a['text']}"

    return "Ayat tidak ditemukan"


def search_keyword(keyword):

    keyword = keyword.lower()

    results = []

    for ayat in QURAN:

        if keyword in ayat["text"].lower():

            results.append(
                f"QS {ayat['surah']}:{ayat['ayah']} ({ayat['surah_name']})\n{ayat['text']}"
            )

    return "\n\n".join(results[:5])


def smart_quran_query(query):

    query = query.lower()

    # contoh: al baqarah 255
    match = re.search(r"([a-z ]+)\s*(\d+)", query)

    if match:

        surah_name = match.group(1).strip()
        ayah = int(match.group(2))

        if surah_name in SURAH_INDEX:

            return get_ayah(SURAH_INDEX[surah_name], ayah)

    # contoh: ayat kursi
    if "kursi" in query:

        return get_ayah(2, 255)

    # keyword search
    return search_keyword(query)