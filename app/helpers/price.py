import re

__PRICE_RGX = r"^([$€¥₩₹])?([^\d.,:\s]+)?(?:[\s.,:]+)?(\d{1,3}(?:([.,])\d{3})+|\d+)(?:((?!\2)[.,])(\d+))?(?:([\s.,:]+)?([^\d.,:\s]+))?$"

def parse_price(s):
    pattern = re.compile(__PRICE_RGX)

    res = pattern.match(s)

    if not res:
        return None
    
    res = res.groups()

    """
        Group1: Currency Symbol
        Group2: ISO Currency Code / Currency Prefix
        Group3: Numeric
        Group4: Thousand Separator
        Group5: Decimal Separator
        Group6: Cents
        Group7: Currency Suffix Separator
        Group8: Currency Suffix
    """

    currency = ""
    price = 0

    if res[1]:
        currency = res[1]
    elif res[0]:
        currency = res[0]
    elif res[7]:
        currency = res[7]
    else:
        currency = None

    price = float(res[2].replace('.', '').replace(',', ''))
    if res[5]:
        price += float(res[5].replace('.', '').replace(',', ''))/100

    return {'currency': currency, 'numeric': price}