from rapidfuzz import process, fuzz

__SUMMARY_KEYWORDS = [
    "total", "subtotal", "sub total", "sub-total", "discount", "service", "service charge", "tax", "grand total", "kembali", "tunai",
    "pb1", "pb 1", "amount", "balance", "sales tax"
]

def __find_keyword(word='', scorer=fuzz.ratio, threshold=70, list_of_keywords=[]):
    best = process.extractOne(word.lower(), list_of_keywords, scorer=scorer)
    if best and best[1] >= threshold:
        return best[0]
    
    return None

def find_summary_keyword(word='', scorer=fuzz.ratio, threshold=70):
    return __find_keyword(word, scorer, threshold, __SUMMARY_KEYWORDS)