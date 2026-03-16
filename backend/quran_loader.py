import os
import json

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