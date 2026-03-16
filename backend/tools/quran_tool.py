import re
from backend.quran_loader import get_ayah, search_keyword, SURAH_INDEX


def quran_ayah(params=None):

    """
    Ambil ayat berdasarkan nomor
    contoh: 2|255
    """

    if not params or "args" not in params:
        return "Parameter kosong"

    args = params["args"]

    if len(args) < 2:
        return "Format: surah|ayat"

    try:

        surah = int(args[0])
        ayah = int(args[1])

        return get_ayah(surah, ayah)

    except:
        return "Parameter tidak valid"


def quran_surah(params=None):

    """
    contoh: al baqarah|255
    """

    if not params or "args" not in params:
        return "Parameter kosong"

    args = params["args"]

    if len(args) < 2:
        return "Format: nama_surah|ayat"

    name = args[0].lower()
    ayah = int(args[1])

    if name not in SURAH_INDEX:
        return "Surah tidak ditemukan"

    surah = SURAH_INDEX[name]

    return get_ayah(surah, ayah)


def quran_search(params=None):

    """
    cari ayat berdasarkan keyword
    """

    if not params or "args" not in params:
        return "Parameter kosong"

    keyword = params["args"][0]

    return search_keyword(keyword)