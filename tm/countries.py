"""Коды и русские названия стран. Любой «хвост» на английском приводится к русскому."""

NAMES = {
    "RU": "Россия", "BY": "Беларусь", "KZ": "Казахстан", "UA": "Украина", "CN": "Китай", "US": "США",
    "JP": "Япония", "KR": "Южная Корея", "IN": "Индия", "IL": "Израиль", "TR": "Турция", "IR": "Иран",
    "GB": "Великобритания", "DE": "Германия", "FR": "Франция", "IT": "Италия", "ES": "Испания", "PT": "Португалия",
    "NL": "Нидерланды", "BE": "Бельгия", "LU": "Люксембург", "AT": "Австрия", "CH": "Швейцария", "PL": "Польша",
    "CZ": "Чехия", "SK": "Словакия", "HU": "Венгрия", "RO": "Румыния", "BG": "Болгария", "GR": "Греция",
    "SE": "Швеция", "NO": "Норвегия", "FI": "Финляндия", "DK": "Дания", "IE": "Ирландия", "EE": "Эстония",
    "LV": "Латвия", "LT": "Литва", "SI": "Словения", "HR": "Хорватия", "RS": "Сербия", "CY": "Кипр",
    "MT": "Мальта", "IS": "Исландия", "MK": "Северная Македония", "AL": "Албания", "ME": "Черногория",
    "BA": "Босния и Герцеговина", "MD": "Молдова", "CA": "Канада", "AU": "Австралия", "NZ": "Новая Зеландия",
    "BR": "Бразилия", "MX": "Мексика", "AR": "Аргентина", "CL": "Чили", "ZA": "ЮАР", "SG": "Сингапур",
    "TW": "Тайвань", "HK": "Гонконг", "SA": "Саудовская Аравия", "AE": "ОАЭ", "EG": "Египет", "VN": "Вьетнам",
    "TH": "Таиланд", "MY": "Малайзия", "ID": "Индонезия", "PK": "Пакистан", "NG": "Нигерия", "KE": "Кения",
    "BD": "Бангладеш", "LK": "Шри-Ланка", "PH": "Филиппины", "IQ": "Ирак", "JO": "Иордания", "MA": "Марокко",
    "DZ": "Алжир", "TN": "Тунис", "CO": "Колумбия", "PE": "Перу", "EC": "Эквадор", "LI": "Лихтенштейн",
    "UZ": "Узбекистан", "AM": "Армения", "AZ": "Азербайджан", "GE": "Грузия", "KG": "Киргизия", "QA": "Катар",
    "ET": "Эфиопия", "GH": "Гана", "NP": "Непал", "OM": "Оман", "KW": "Кувейт", "LB": "Ливан", "SY": "Сирия",
    "TJ": "Таджикистан", "MN": "Монголия", "XK": "Косово", "WS": "Самоа", "TZ": "Танзания", "UG": "Уганда",
    "RW": "Руанда", "SN": "Сенегал", "CI": "Кот-д'Ивуар", "CM": "Камерун", "ZM": "Замбия", "MW": "Малави",
    "MZ": "Мозамбик", "MG": "Мадагаскар", "AO": "Ангола", "LA": "Лаос", "KH": "Камбоджа", "PR": "Пуэрто-Рико",
    "KY": "Каймановы острова", "BM": "Бермуды", "JM": "Ямайка", "TT": "Тринидад и Тобаго", "BB": "Барбадос",
    "HT": "Гаити", "DO": "Доминиканская Республика", "CR": "Коста-Рика", "PA": "Панама", "GT": "Гватемала",
    "HN": "Гондурас", "SV": "Сальвадор", "NI": "Никарагуа", "BO": "Боливия", "PY": "Парагвай", "UY": "Уругвай",
    "VE": "Венесуэла", "CU": "Куба", "AF": "Афганистан", "YE": "Йемен", "SD": "Судан", "SS": "Южный Судан",
    "CD": "ДР Конго", "CG": "Конго", "GA": "Габон", "BJ": "Бенин", "BF": "Буркина-Фасо", "ML": "Мали",
    "NE": "Нигер", "TD": "Чад", "GM": "Гамбия", "SL": "Сьерра-Леоне", "LR": "Либерия", "GN": "Гвинея",
    "GW": "Гвинея-Бисау", "CV": "Кабо-Верде", "ST": "Сан-Томе и Принсипи", "GQ": "Экваториальная Гвинея",
    "CF": "ЦАР", "ER": "Эритрея", "DJ": "Джибути", "SO": "Сомали", "BI": "Бурунди", "MW": "Малави",
    "ZW": "Зимбабве", "BW": "Ботсвана", "NA": "Намибия", "SZ": "Эсватини", "LS": "Лесото", "MU": "Маврикий",
    "SC": "Сейшелы", "KM": "Коморы", "BT": "Бутан", "MM": "Мьянма", "BN": "Бруней", "FJ": "Фиджи",
    "PG": "Папуа — Новая Гвинея", "TO": "Тонга", "SB": "Соломоновы Острова", "VU": "Вануату",
    "PS": "Палестина", "XK": "Косово",
    # не страны, а ведомства / надписи источников
    "EP": "Европейское патентное ведомство", "WO": "Международная заявка (PCT)", "EA": "Евразийское патентное ведомство",
    "EU": "Европейский союз", "XK": "Косово",
}

ISO3 = {
    "RUS": "RU", "BLR": "BY", "KAZ": "KZ", "UKR": "UA", "CHN": "CN", "USA": "US", "JPN": "JP", "KOR": "KR",
    "IND": "IN", "ISR": "IL", "TUR": "TR", "IRN": "IR", "GBR": "GB", "DEU": "DE", "FRA": "FR", "ITA": "IT",
    "ESP": "ES", "PRT": "PT", "NLD": "NL", "BEL": "BE", "LUX": "LU", "AUT": "AT", "CHE": "CH", "POL": "PL",
    "CZE": "CZ", "SVK": "SK", "HUN": "HU", "ROU": "RO", "BGR": "BG", "GRC": "GR", "SWE": "SE", "NOR": "NO",
    "FIN": "FI", "DNK": "DK", "IRL": "IE", "EST": "EE", "LVA": "LV", "LTU": "LT", "SVN": "SI", "HRV": "HR",
    "SRB": "RS", "CYP": "CY", "MLT": "MT", "ISL": "IS", "MKD": "MK", "ALB": "AL", "MNE": "ME", "BIH": "BA",
    "MDA": "MD", "CAN": "CA", "AUS": "AU", "NZL": "NZ", "BRA": "BR", "MEX": "MX", "ARG": "AR", "CHL": "CL",
    "ZAF": "ZA", "SGP": "SG", "TWN": "TW", "HKG": "HK", "SAU": "SA", "ARE": "AE", "EGY": "EG", "VNM": "VN",
    "THA": "TH", "MYS": "MY", "IDN": "ID", "PAK": "PK", "NGA": "NG", "KEN": "KE", "BGD": "BD", "LKA": "LK",
    "PHL": "PH", "IRQ": "IQ", "JOR": "JO", "MAR": "MA", "DZA": "DZ", "TUN": "TN", "COL": "CO", "PER": "PE",
    "ECU": "EC", "LIE": "LI", "UZB": "UZ", "ARM": "AM", "AZE": "AZ", "GEO": "GE", "KGZ": "KG", "QAT": "QA",
    "ETH": "ET", "GHA": "GH", "NPL": "NP", "OMN": "OM", "KWT": "KW", "LBN": "LB", "SYR": "SY", "TJK": "TJ",
    "MNG": "MN", "TZA": "TZ", "UGA": "UG", "RWA": "RW", "SEN": "SN", "CIV": "CI", "CMR": "CM", "ZMB": "ZM",
    "MWI": "MW", "MOZ": "MZ", "MDG": "MG", "AGO": "AO", "LAO": "LA", "KHM": "KH", "PRI": "PR", "CYM": "KY",
    "HTI": "HT", "LBR": "LR", "SLE": "SL", "GMB": "GM", "BFA": "BF", "MLI": "ML", "SOM": "SO", "CAF": "CF",
    "STP": "ST", "TON": "TO", "BTN": "BT", "PSE": "PS", "SWZ": "SZ", "SSD": "SS", "COD": "CD", "COG": "CG",
}

# английские и «региональные» подписи Всемирного банка / TED → ISO2 или спец. код
ENGLISH = {
    "russian federation": "RU", "russia": "RU", "belarus": "BY", "kazakhstan": "KZ", "ukraine": "UA", "china": "CN",
    "united states": "US", "united states of america": "US", "japan": "JP", "korea, republic of": "KR",
    "republic of korea": "KR", "south korea": "KR", "india": "IN", "israel": "IL", "turkiye": "TR", "turkey": "TR",
    "united kingdom": "GB", "germany": "DE", "france": "FR", "italy": "IT", "spain": "ES", "poland": "PL",
    "romania": "RO", "moldova": "MD", "georgia": "GE", "armenia": "AM", "azerbaijan": "AZ", "uzbekistan": "UZ",
    "kyrgyz republic": "KG", "kyrgyzstan": "KG", "tajikistan": "TJ", "mongolia": "MN", "serbia": "RS",
    "albania": "AL", "north macedonia": "MK", "montenegro": "ME", "bosnia and herzegovina": "BA", "kosovo": "XK",
    "brazil": "BR", "mexico": "MX", "argentina": "AR", "colombia": "CO", "peru": "PE", "ecuador": "EC", "chile": "CL",
    "indonesia": "ID", "philippines": "PH", "viet nam": "VN", "vietnam": "VN", "thailand": "TH", "pakistan": "PK",
    "bangladesh": "BD", "sri lanka": "LK", "nepal": "NP", "egypt, arab republic of": "EG", "egypt": "EG",
    "morocco": "MA", "tunisia": "TN", "jordan": "JO", "iraq": "IQ", "lebanon": "LB", "nigeria": "NG", "kenya": "KE",
    "ethiopia": "ET", "ghana": "GH", "south africa": "ZA", "samoa": "WS", "tanzania": "TZ", "uganda": "UG",
    "rwanda": "RW", "senegal": "SN", "cote d'ivoire": "CI", "côte d'ivoire": "CI", "cameroon": "CM", "zambia": "ZM",
    "malawi": "MW", "mozambique": "MZ", "madagascar": "MG", "angola": "AO", "lao people's democratic republic": "LA",
    "cambodia": "KH", "canada": "CA", "australia": "AU", "new zealand": "NZ", "switzerland": "CH", "austria": "AT",
    "belgium": "BE", "netherlands": "NL", "sweden": "SE", "norway": "NO", "finland": "FI", "denmark": "DK",
    "ireland": "IE", "portugal": "PT", "greece": "GR", "czech republic": "CZ", "czechia": "CZ", "slovakia": "SK",
    "hungary": "HU", "bulgaria": "BG", "croatia": "HR", "slovenia": "SI", "lithuania": "LT", "latvia": "LV",
    "estonia": "EE", "cyprus": "CY", "malta": "MT", "luxembourg": "LU", "iceland": "IS", "singapore": "SG",
    "taiwan": "TW", "hong kong": "HK", "saudi arabia": "SA", "united arab emirates": "AE", "uae": "AE",
    "qatar": "QA", "kuwait": "KW", "oman": "OM", "malaysia": "MY", "iran": "IR", "iran, islamic republic of": "IR",
    "gambia, the": "GM", "gambia": "GM", "sierra leone": "SL", "liberia": "LR", "haiti": "HT", "burkina faso": "BF",
    "tonga": "TO", "sao tome and principe": "ST", "são tomé and principe": "ST", "mali": "ML",
    "somalia, federal republic of": "SO", "somalia": "SO", "bhutan": "BT", "west bank and gaza": "PS",
    "palestine": "PS", "central african republic": "CF", "eswatini": "SZ", "swaziland": "SZ",
    "puerto rico": "PR", "cayman islands": "KY", "world": "WORLD", "worldwide": "WORLD", "global": "WORLD",
    "western and central africa": "WCA", "eastern and southern africa": "ESA", "caribbean": "CARIB",
    "africa": "AFR", "asia": "ASIA", "europe": "EUR", "latin america": "LATAM",
    "multi-country": "MULTI", "multiple countries": "MULTI", "regional": "REG",
}

# спец. подписи без ISO2
SPECIAL = {
    "WORLD": "Международный проект",
    "WCA": "Западная и Центральная Африка",
    "ESA": "Восточная и Южная Африка",
    "CARIB": "Карибский регион",
    "AFR": "Африка (регион)",
    "ASIA": "Азия (регион)",
    "EUR": "Европа (регион)",
    "LATAM": "Латинская Америка",
    "MULTI": "Несколько стран",
    "REG": "Региональный проект",
}
NAMES.update(SPECIAL)


def code(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw or raw in {"—", "-", "n/a", "N/A", "null", "None"}:
        return ""
    # уже русское название → обратный поиск
    for iso, ru in NAMES.items():
        if raw == ru:
            return iso
    up = raw.upper().replace(".", "")
    if up in NAMES:
        return up
    if up in ISO3:
        return ISO3[up]
    if len(up) == 2 and up.isalpha():
        return up
    if len(up) == 3 and up.isalpha():
        return ISO3.get(up, "")
    return ENGLISH.get(raw.lower().strip(), "")


def name(value: str | None) -> str:
    """Всегда русское название; неизвестное → «не указана», без английских хвостов."""
    c = code(value)
    if c and c in NAMES:
        return NAMES[c]
    raw = (value or "").strip()
    if not raw or raw in {"—", "-"}:
        return "не указана"
    # если пришло уже по-русски (кириллица) — оставляем
    if any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in raw):
        return raw
    return "не указана"
