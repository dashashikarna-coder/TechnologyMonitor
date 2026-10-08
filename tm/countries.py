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
    "EP": "Европейское патентное ведомство", "WO": "Международная заявка (PCT)", "EA": "Евразийское патентное ведомство",
}

ISO3 = {
    "RUS": "RU", "BLR": "BY", "KAZ": "KZ", "UKR": "UA", "CHN": "CN", "USA": "US", "JPN": "JP", "KOR": "KR",
    "GBR": "GB", "DEU": "DE", "FRA": "FR", "ITA": "IT", "ESP": "ES", "PRT": "PT", "NLD": "NL", "BEL": "BE",
    "LUX": "LU", "AUT": "AT", "CHE": "CH", "POL": "PL", "CZE": "CZ", "SVK": "SK", "HUN": "HU", "ROU": "RO",
    "BGR": "BG", "GRC": "GR", "SWE": "SE", "NOR": "NO", "FIN": "FI", "DNK": "DK", "IRL": "IE", "EST": "EE",
    "LVA": "LV", "LTU": "LT", "SVN": "SI", "HRV": "HR", "SRB": "RS", "CYP": "CY", "MLT": "MT", "ISL": "IS",
    "MKD": "MK", "ALB": "AL", "MNE": "ME", "BIH": "BA", "MDA": "MD", "LIE": "LI", "TUR": "TR",
}


ENGLISH = {
    "russian federation": "RU", "russia": "RU", "belarus": "BY", "kazakhstan": "KZ", "ukraine": "UA", "china": "CN",
    "united states": "US", "japan": "JP", "korea, republic of": "KR", "india": "IN", "turkiye": "TR", "turkey": "TR",
    "united kingdom": "GB", "germany": "DE", "france": "FR", "italy": "IT", "spain": "ES", "poland": "PL",
    "romania": "RO", "moldova": "MD", "georgia": "GE", "armenia": "AM", "azerbaijan": "AZ", "uzbekistan": "UZ",
    "kyrgyz republic": "KG", "tajikistan": "TJ", "mongolia": "MN", "serbia": "RS", "albania": "AL",
    "north macedonia": "MK", "montenegro": "ME", "bosnia and herzegovina": "BA", "kosovo": "XK", "brazil": "BR",
    "mexico": "MX", "argentina": "AR", "colombia": "CO", "peru": "PE", "ecuador": "EC", "chile": "CL",
    "indonesia": "ID", "philippines": "PH", "viet nam": "VN", "vietnam": "VN", "thailand": "TH", "pakistan": "PK",
    "bangladesh": "BD", "sri lanka": "LK", "nepal": "NP", "egypt, arab republic of": "EG", "egypt": "EG",
    "morocco": "MA", "tunisia": "TN", "jordan": "JO", "iraq": "IQ", "lebanon": "LB", "nigeria": "NG", "kenya": "KE",
    "ethiopia": "ET", "ghana": "GH", "south africa": "ZA", "samoa": "WS", "tanzania": "TZ", "uganda": "UG",
    "rwanda": "RW", "senegal": "SN", "cote d'ivoire": "CI", "cameroon": "CM", "zambia": "ZM", "malawi": "MW",
    "mozambique": "MZ", "madagascar": "MG", "angola": "AO", "lao people's democratic republic": "LA", "cambodia": "KH",
}
NAMES.update({"TJ": "Таджикистан", "MN": "Монголия", "XK": "Косово", "WS": "Самоа", "TZ": "Танзания",
              "UG": "Уганда", "RW": "Руанда", "SN": "Сенегал", "CI": "Кот-д'Ивуар", "CM": "Камерун", "ZM": "Замбия",
              "MW": "Малави", "MZ": "Мозамбик", "MG": "Мадагаскар", "AO": "Ангола", "LA": "Лаос", "KH": "Камбоджа"})


def code(value: str | None) -> str:
    raw = (value or "").strip()
    value = raw.upper()
    return ISO3.get(value) or (value if len(value) == 2 else ENGLISH.get(raw.lower(), ""))


def name(value: str | None) -> str:
    c = code(value)
    return NAMES.get(c, c or (value or "").strip() or "—")
