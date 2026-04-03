import json
import re
from collections import OrderedDict

from services.common import normalize_text, row_value


def build_option_group(key, label, choices, default=None, multiple=False):
    choice_rows = [{"value": value, "label": choice_label} for value, choice_label in choices]
    if multiple:
        if default is None:
            default_value = [choice_rows[0]["value"]] if choice_rows else []
        elif isinstance(default, (list, tuple, set)):
            default_value = [str(value).strip() for value in default if str(value).strip()]
        else:
            default_value = [str(default).strip()] if str(default).strip() else []
    else:
        default_value = default or (choice_rows[0]["value"] if choice_rows else "")

    return {
        "key": key,
        "label": label,
        "default": default_value,
        "multiple": multiple,
        "choices": choice_rows,
    }


SERVING_TYPE_OPTIONS = build_option_group(
    "serving_type",
    "Pilih Paket atau PCS",
    [("paket", "Paket"), ("pcs", "PCS")],
    default="pcs",
)
CHICKEN_GEPREK_PART_OPTIONS = build_option_group(
    "chicken_part",
    "Bagian Ayam",
    [("paha_bawah", "Paha Bawah"), ("paha_atas", "Paha Atas")],
)
CHICKEN_STANDARD_PART_OPTIONS = build_option_group(
    "chicken_part",
    "Bagian Ayam",
    [("dada", "Dada"), ("paha", "Paha")],
)
GEPREK_RICA_OPTIONS = build_option_group(
    "rica_mode",
    "Sambal Rica",
    [("langsung", "Langsung"), ("pisah", "Pisah Rica")],
)
TUNA_COOKING_OPTIONS = build_option_group(
    "cook_style",
    "Cara Masak",
    [("bakar", "Bakar"), ("goreng", "Goreng")],
)
EGG_STYLE_OPTIONS = build_option_group(
    "egg_style",
    "Pilihan Telur",
    [("dadar", "Dadar"), ("rebus", "Rebus"), ("mata_sapi", "Mata Sapi")],
)
FRIED_RICE_EGG_OPTIONS = build_option_group(
    "egg_style",
    "Pilihan Telur",
    [
        ("ceplok_setengah_matang", "Ceplok Setengah Matang"),
        ("ceplok_matang", "Ceplok Matang"),
        ("rebus", "Rebus"),
        ("dadar", "Dadar"),
    ],
)
BROTH_STYLE_OPTIONS = build_option_group(
    "broth_style",
    "Pilihan Kuah",
    [("pisah", "Pisah Kuah"), ("campur", "Campur Kuah")],
)
BANANA_TYPE_OPTIONS = build_option_group(
    "banana_type",
    "Jenis Pisang",
    [("raja", "Raja"), ("pagata", "Pagata")],
)
SERUT_STYLE_OPTIONS = build_option_group(
    "serut_style",
    "Pilihan Siraman",
    [("gulmer", "Gulmer"), ("sirup", "Sirup")],
)
BIG_FRIED_STYLE_OPTIONS = build_option_group(
    "fried_style",
    "Varian Ayam",
    [("ori", "Ori"), ("bubble", "Bubble")],
)
BIG_FRIED_SIZE_OPTIONS = build_option_group(
    "fried_size",
    "Ukuran",
    [("small", "Small"), ("large", "Large")],
)
BIG_FRIED_SEASONING_OPTIONS = build_option_group(
    "seasoning",
    "Bumbu",
    [
        ("balado", "Balado"),
        ("keju", "Keju"),
        ("bbq", "BBQ"),
        ("jagung_bakar", "Jagung Bakar"),
        ("sapi_panggang", "Sapi Panggang"),
        ("extra_hot", "Extra Hot"),
    ],
    multiple=True,
)
TOPPING_SAUCE_OPTIONS = build_option_group(
    "topping_sauce",
    "Topping Saus",
    [
        ("saus_keju", "Saus Keju"),
        ("saus_mayo", "Saus Mayo"),
        ("saus_bbq", "Saus BBQ"),
        ("saus_pedas_manis", "Saus Pedas Manis"),
        ("saus_rica_bawang", "Saus Rica Bawang"),
    ],
    multiple=True,
)
TEMPERATURE_OPTIONS = build_option_group(
    "temperature",
    "Suhu Minuman",
    [("ice", "Ice"), ("hangat", "Hangat"), ("hot", "Hot")],
)
FRUIT_JUICE_OPTIONS = build_option_group(
    "juice_fruit",
    "Pilihan Buah",
    [("buah_naga", "Buah Naga"), ("alpukat", "Alpukat"), ("sirsak", "Sirsak")],
)
STEAM_SAUCE_OPTIONS = build_option_group(
    "steam_sauce",
    "Pilihan Saus",
    [("kecap_rica", "Kecap Rica"), ("bawang_putih", "Bawang Putih")],
)
SATE_SAUCE_OPTIONS = build_option_group(
    "sate_sauce",
    "Penyajian Saus",
    [("campur", "Campur Saus"), ("pisah", "Pisah Saus")],
)

OPTION_GROUP_CATALOG = [
    CHICKEN_GEPREK_PART_OPTIONS,
    CHICKEN_STANDARD_PART_OPTIONS,
    GEPREK_RICA_OPTIONS,
    TUNA_COOKING_OPTIONS,
    EGG_STYLE_OPTIONS,
    FRIED_RICE_EGG_OPTIONS,
    BROTH_STYLE_OPTIONS,
    BANANA_TYPE_OPTIONS,
    SERUT_STYLE_OPTIONS,
    BIG_FRIED_STYLE_OPTIONS,
    BIG_FRIED_SIZE_OPTIONS,
    BIG_FRIED_SEASONING_OPTIONS,
    TOPPING_SAUCE_OPTIONS,
    TEMPERATURE_OPTIONS,
    FRUIT_JUICE_OPTIONS,
    STEAM_SAUCE_OPTIONS,
    SATE_SAUCE_OPTIONS,
]


MENU_DISPLAY_GROUPS = [
    {
        "id": "ayam_geprek",
        "name": "Ayam Geprek",
        "match_names": ["Ayam Geprek"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_GEPREK_PART_OPTIONS, GEPREK_RICA_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Geprek", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Geprek", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_crispy",
        "name": "Ayam Crispy",
        "match_names": ["Ayam Crispy"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_GEPREK_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Crispy", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Crispy", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_kalasan",
        "name": "Ayam Kalasan",
        "match_names": ["Ayam Kalasan"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_STANDARD_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Kalasan", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Kalasan", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_bakar_rica",
        "name": "Ayam Bakar Rica",
        "match_names": ["Ayam Bakar Rica"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_STANDARD_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Bakar Rica", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Bakar Rica", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_bakar_kecap",
        "name": "Ayam Bakar Kecap",
        "match_names": ["Ayam Bakar Kecap"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_STANDARD_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Bakar Kecap", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Bakar Kecap", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_bakar_iloni",
        "name": "Ayam Bakar Iloni",
        "match_names": ["Ayam Bakar Iloni"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_STANDARD_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Bakar Iloni", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Bakar Iloni", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_serundeng_manna",
        "name": "Ayam Serundeng Manna",
        "match_names": ["Ayam Serundeng Manna"],
        "option_groups": [SERVING_TYPE_OPTIONS, CHICKEN_STANDARD_PART_OPTIONS],
        "combo_keys": ["serving_type"],
        "combo_variants": [
            {"combo": {"serving_type": "pcs"}, "name": "Ayam Serundeng Manna", "serving_type": "pcs"},
            {"combo": {"serving_type": "paket"}, "name": "Ayam Serundeng Manna", "serving_type": "paket"},
        ],
    },
    {
        "id": "dada_tuna",
        "name": "Dada Tuna",
        "match_names": ["Dada Tuna Goreng", "dada tuna bakar"],
        "option_groups": [TUNA_COOKING_OPTIONS],
        "combo_keys": ["cook_style"],
        "combo_variants": [
            {"combo": {"cook_style": "goreng"}, "name": "Dada Tuna Goreng", "serving_type": "pcs"},
            {"combo": {"cook_style": "bakar"}, "name": "dada tuna bakar", "serving_type": "pcs"},
        ],
    },
    {
        "id": "paket_dada_tuna",
        "name": "Paket Dada Tuna",
        "match_names": ["Paket Dada Tuna goreng", "paket dada tuna bakar"],
        "option_groups": [TUNA_COOKING_OPTIONS],
        "combo_keys": ["cook_style"],
        "combo_variants": [
            {"combo": {"cook_style": "goreng"}, "name": "Paket Dada Tuna goreng", "serving_type": "paket"},
            {"combo": {"cook_style": "bakar"}, "name": "paket dada tuna bakar", "serving_type": "paket"},
        ],
    },
    {
        "id": "pisang_goreng",
        "name": "Pisang Goreng",
        "match_names": ["Pisang Goreng Raja", "Pisang Goreng Pagata"],
        "option_groups": [BANANA_TYPE_OPTIONS],
        "combo_keys": ["banana_type"],
        "combo_variants": [
            {"combo": {"banana_type": "raja"}, "name": "Pisang Goreng Raja"},
            {"combo": {"banana_type": "pagata"}, "name": "Pisang Goreng Pagata"},
        ],
    },
    {
        "id": "es_serut_kacang_susu",
        "name": "Es Serut Kacang Susu",
        "match_names": ["Es Serut Kacang Susu Gulmer", "Es Serut Kacang Susu Sirup"],
        "option_groups": [SERUT_STYLE_OPTIONS],
        "combo_keys": ["serut_style"],
        "combo_variants": [
            {"combo": {"serut_style": "gulmer"}, "name": "Es Serut Kacang Susu Gulmer"},
            {"combo": {"serut_style": "sirup"}, "name": "Es Serut Kacang Susu Sirup"},
        ],
    },
    {
        "id": "big_fried_chicken",
        "name": "Big Fried Chicken",
        "match_names": [
            "Big Fried Chicken Original small",
            "Big Fried Chicken Original large",
            "Big Fried Chicken Bubble small",
            "Big Fried Chicken Bubble large",
        ],
        "option_groups": [BIG_FRIED_STYLE_OPTIONS, BIG_FRIED_SIZE_OPTIONS, BIG_FRIED_SEASONING_OPTIONS],
        "combo_keys": ["fried_style", "fried_size"],
        "combo_variants": [
            {"combo": {"fried_style": "ori", "fried_size": "small"}, "name": "Big Fried Chicken Original small"},
            {"combo": {"fried_style": "ori", "fried_size": "large"}, "name": "Big Fried Chicken Original large"},
            {"combo": {"fried_style": "bubble", "fried_size": "small"}, "name": "Big Fried Chicken Bubble small"},
            {"combo": {"fried_style": "bubble", "fried_size": "large"}, "name": "Big Fried Chicken Bubble large"},
        ],
    },
    {
        "id": "big_fried_chicken_topping",
        "name": "Big Fried Chicken + Topping",
        "match_names": [
            "Big Fried Chicken Original small + topping",
            "Big Fried Chicken Original large + topping",
            "Big Fried Chicken Bubble small + topping",
            "Big Fried Chicken Bubble large + topping",
        ],
        "option_groups": [BIG_FRIED_STYLE_OPTIONS, BIG_FRIED_SIZE_OPTIONS, BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS],
        "combo_keys": ["fried_style", "fried_size"],
        "combo_variants": [
            {"combo": {"fried_style": "ori", "fried_size": "small"}, "name": "Big Fried Chicken Original small + topping"},
            {"combo": {"fried_style": "ori", "fried_size": "large"}, "name": "Big Fried Chicken Original large + topping"},
            {"combo": {"fried_style": "bubble", "fried_size": "small"}, "name": "Big Fried Chicken Bubble small + topping"},
            {"combo": {"fried_style": "bubble", "fried_size": "large"}, "name": "Big Fried Chicken Bubble large + topping"},
        ],
    },
    {
        "id": "ayam_ori_nasi_topping",
        "name": "Ayam Ori + Nasi + Topping",
        "match_names": ["Ayam Ori chilin + nasi + topping"],
        "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS],
        "combo_keys": [],
        "combo_variants": [
            {"combo": {}, "name": "Ayam Ori chilin + nasi + topping", "serving_type": "paket"},
        ],
    },
    {
        "id": "ayam_bubble_nasi_topping",
        "name": "Ayam Bubble + Nasi + Topping",
        "match_names": ["Ayam Bubble Chilin + nasi + topping"],
        "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS],
        "combo_keys": [],
        "combo_variants": [
            {"combo": {}, "name": "Ayam Bubble Chilin + nasi + topping", "serving_type": "paket"},
        ],
    },
    {
        "id": "chicken_skin_nasi_topping",
        "name": "Chicken Skin + Nasi + Topping",
        "match_names": ["Chicken Skin"],
        "option_groups": [TOPPING_SAUCE_OPTIONS],
        "combo_keys": [],
        "combo_variants": [
            {"combo": {}, "name": "Chicken Skin", "serving_type": "paket"},
        ],
    },
    {
        "id": "teh_tawar",
        "name": "Teh Tawar",
        "match_names": ["Teh Tawar", "Teh Tawar Panas", "Teh Tawar Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Teh Tawar Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Teh Tawar"},
            {"combo": {"temperature": "hot"}, "name": "Teh Tawar Panas"},
        ],
    },
    {
        "id": "teh_manis",
        "name": "Teh Manis",
        "match_names": ["Teh Manis", "Teh Manis Panas", "Teh Manis Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Teh Manis Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Teh Manis"},
            {"combo": {"temperature": "hot"}, "name": "Teh Manis Panas"},
        ],
    },
    {
        "id": "kopi_hitam",
        "name": "Kopi Hitam",
        "match_names": ["Kopi Hitam", "Kopi Hitam Panas", "Kopi Hitam Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Kopi Hitam Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Kopi Hitam"},
            {"combo": {"temperature": "hot"}, "name": "Kopi Hitam Panas"},
        ],
    },
    {
        "id": "kopi_susu",
        "name": "Kopi Susu",
        "match_names": ["Kopi Susu", "Kopi Susu Panas", "Kopi Susu Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Kopi Susu Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Kopi Susu"},
            {"combo": {"temperature": "hot"}, "name": "Kopi Susu Panas"},
        ],
    },
    {
        "id": "nutrisari",
        "name": "Nutrisari",
        "match_names": ["nutrisari dingin", "nutrisari Dingin", "nutrisari Panas"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "nutrisari dingin"},
            {"combo": {"temperature": "hangat"}, "name": "nutrisari Panas"},
            {"combo": {"temperature": "hot"}, "name": "nutrisari Panas"},
        ],
    },
    {
        "id": "jeruk_nipis",
        "name": "Jeruk Nipis",
        "match_names": ["Jeruk Nipis", "Jeruk Nipis Panas", "Jeruk Nipis Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Jeruk Nipis Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Jeruk Nipis"},
            {"combo": {"temperature": "hot"}, "name": "Jeruk Nipis Panas"},
        ],
    },
    {
        "id": "jeruk_manis",
        "name": "Jeruk Manis",
        "match_names": ["Jeruk Manis", "Jeruk Manis Panas", "Jeruk Manis Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Jeruk Manis Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Jeruk Manis"},
            {"combo": {"temperature": "hot"}, "name": "Jeruk Manis Panas"},
        ],
    },
    {
        "id": "lemon_tea",
        "name": "Lemon Tea",
        "match_names": ["Lemon Tea", "Lemon Tea Panas", "Lemon Tea Dingin"],
        "option_groups": [TEMPERATURE_OPTIONS],
        "combo_keys": ["temperature"],
        "combo_variants": [
            {"combo": {"temperature": "ice"}, "name": "Lemon Tea Dingin"},
            {"combo": {"temperature": "hangat"}, "name": "Lemon Tea"},
            {"combo": {"temperature": "hot"}, "name": "Lemon Tea Panas"},
        ],
    },
    {
        "id": "jus_buah",
        "name": "Jus Buah",
        "match_names": ["Jus Buah Naga", "Jus Buah Sirsak", "Jus Buah Avocado"],
        "option_groups": [FRUIT_JUICE_OPTIONS],
        "combo_keys": ["juice_fruit"],
        "combo_variants": [
            {"combo": {"juice_fruit": "buah_naga"}, "name": "Jus Buah Naga"},
            {"combo": {"juice_fruit": "alpukat"}, "name": "Jus Buah Avocado"},
            {"combo": {"juice_fruit": "sirsak"}, "name": "Jus Buah Sirsak"},
        ],
    },
]

MENU_SINGLE_OPTION_CONFIGS = {
    "ayam geprek": {"display_name": "Ayam Geprek", "option_groups": [GEPREK_RICA_OPTIONS]},
    "ayam crispy": {"display_name": "Ayam Crispy", "option_groups": []},
    "ayam kalasan": {"display_name": "Ayam Kalasan", "option_groups": []},
    "ayam bakar rica": {"display_name": "Ayam Bakar Rica", "option_groups": []},
    "ayam bakar kecap": {"display_name": "Ayam Bakar Kecap", "option_groups": []},
    "ayam bakar iloni": {"display_name": "Ayam Bakar Iloni", "option_groups": []},
    "ayam serundeng manna": {"display_name": "Ayam Serundeng Manna", "option_groups": []},
    "telur": {"display_name": "Telur", "option_groups": [EGG_STYLE_OPTIONS]},
    "nasi goreng kampung": {"display_name": "Nasi Goreng Kampung", "option_groups": [FRIED_RICE_EGG_OPTIONS]},
    "nasi goreng sagela": {"display_name": "Nasi Goreng Sagela", "option_groups": [FRIED_RICE_EGG_OPTIONS]},
    "nasi goreng spesial": {"display_name": "Nasi Goreng Spesial", "option_groups": [FRIED_RICE_EGG_OPTIONS]},
    "nasi goreng pete": {"display_name": "Nasi Goreng Pete", "option_groups": [FRIED_RICE_EGG_OPTIONS]},
    "mie titi": {"display_name": "Mie Titi", "option_groups": [BROTH_STYLE_OPTIONS]},
    "nila steam kecap rica": {"display_name": "Nila Steam", "option_groups": [STEAM_SAUCE_OPTIONS]},
    "sate ayam (6 tusuk)": {"display_name": "Sate Ayam (6 Tusuk)", "option_groups": [SATE_SAUCE_OPTIONS]},
    "sate tuna (5 tusuk)": {"display_name": "Sate Tuna (5 Tusuk)", "option_groups": [SATE_SAUCE_OPTIONS]},
    "sate daging (5 tusuk)": {"display_name": "Sate Daging (5 Tusuk)", "option_groups": [SATE_SAUCE_OPTIONS]},
    "big fried chicken original small": {"display_name": "Big Fried Chicken Original small", "option_groups": [BIG_FRIED_SEASONING_OPTIONS]},
    "big fried chicken original large": {"display_name": "Big Fried Chicken Original large", "option_groups": [BIG_FRIED_SEASONING_OPTIONS]},
    "big fried chicken bubble small": {"display_name": "Big Fried Chicken Bubble small", "option_groups": [BIG_FRIED_SEASONING_OPTIONS]},
    "big fried chicken bubble large": {"display_name": "Big Fried Chicken Bubble large", "option_groups": [BIG_FRIED_SEASONING_OPTIONS]},
    "big fried chicken original small + topping": {"display_name": "Big Fried Chicken Original small + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "big fried chicken original large + topping": {"display_name": "Big Fried Chicken Original large + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "big fried chicken bubble small + topping": {"display_name": "Big Fried Chicken Bubble small + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "big fried chicken bubble large + topping": {"display_name": "Big Fried Chicken Bubble large + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "ayam ori chilin + nasi + topping": {"display_name": "Ayam Ori chilin + nasi + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "ayam bubble chilin + nasi + topping": {"display_name": "Ayam Bubble Chilin + nasi + topping", "option_groups": [BIG_FRIED_SEASONING_OPTIONS, TOPPING_SAUCE_OPTIONS]},
    "chicken skin": {"display_name": "Chicken Skin", "option_groups": [TOPPING_SAUCE_OPTIONS]},
}

OPTION_STOCK_LABELS = OrderedDict(
    [
        (
            "seasoning",
            OrderedDict(
                [
                    ("balado", "Balado"),
                    ("keju", "Keju"),
                    ("bbq", "BBQ"),
                    ("jagung_bakar", "Jagung Bakar"),
                    ("sapi_panggang", "Sapi Panggang"),
                    ("extra_hot", "Extra Hot"),
                ]
            ),
        ),
        (
            "topping_sauce",
            OrderedDict(
                [
                    ("saus_keju", "Saus Keju"),
                    ("saus_mayo", "Saus Mayo"),
                    ("saus_bbq", "Saus BBQ"),
                    ("saus_pedas_manis", "Saus Pedas Manis"),
                    ("saus_rica_bawang", "Saus Rica Bawang"),
                ]
            ),
        ),
    ]
)


def normalize_serving_type(serving_type):
    serving = normalize_text(serving_type)
    serving_map = {
        "paket": "paket",
        "package": "paket",
        "pcs": "pcs",
        "piece": "pcs",
        "menu_piece": "pcs",
        "porsi": "porsi",
        "portion": "porsi",
    }
    return serving_map.get(serving, serving)


def serialize_combo_key(combo_values, combo_keys):
    if not combo_keys:
        return "__default__"
    return "|".join(f"{key}={normalize_text(combo_values.get(key))}" for key in combo_keys)


def normalize_menu_options_payload(menu_options_json):
    payload = {}

    if not menu_options_json:
        return payload

    if isinstance(menu_options_json, dict):
        payload = dict(menu_options_json)
    else:
        try:
            payload = json.loads(menu_options_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

    if not isinstance(payload, dict):
        return {}

    selected_options = payload.get("selected_options")
    if isinstance(selected_options, dict):
        selected_options = dict(selected_options)
        selected_options.pop("serving_type", None)
        selected_options.pop("chicken_part", None)
        payload["selected_options"] = selected_options

    return payload


def normalize_option_value_list(raw_value):
    if raw_value is None:
        return []

    if isinstance(raw_value, (list, tuple, set)):
        values = raw_value
    else:
        values = [raw_value]

    normalized_values = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized_values.append(text)
    return normalized_values


def extract_selected_option_values(menu_options_json):
    payload = normalize_menu_options_payload(menu_options_json)
    selected_options = payload.get("selected_options") or {}
    option_values = {}

    for option_key, option in selected_options.items():
        raw_value = option.get("value")
        if isinstance(raw_value, (list, tuple, set)):
            option_values[option_key] = normalize_option_value_list(raw_value)
        else:
            normalized_values = normalize_option_value_list(raw_value)
            option_values[option_key] = normalized_values[0] if normalized_values else ""

    return option_values


def get_option_group_metadata():
    metadata = {}
    for group in OPTION_GROUP_CATALOG:
        bucket = metadata.setdefault(
            group["key"],
            {"label": group["label"], "multiple": group.get("multiple", False), "choices": {}},
        )
        for choice in group.get("choices", []):
            bucket["choices"][choice["value"]] = choice["label"]
    return metadata


OPTION_GROUP_METADATA = get_option_group_metadata()


def build_selected_option_entry(option_key, raw_value):
    meta = OPTION_GROUP_METADATA.get(option_key, {})
    label = meta.get("label") or option_key.replace("_", " ").title()
    choices = meta.get("choices", {})
    multiple = meta.get("multiple", False)

    normalized_values = normalize_option_value_list(raw_value)
    if not normalized_values:
        return None

    display_values = [choices.get(value, value) for value in normalized_values]
    if multiple or len(normalized_values) > 1:
        return {"label": label, "value": normalized_values, "display": display_values}

    return {"label": label, "value": normalized_values[0], "display": display_values[0]}


def build_menu_options_payload_from_form(form_data, menu_catalog, display_menu_id, fallback_payload=None):
    selected_display_menu_id = str(display_menu_id or "").strip()
    if not selected_display_menu_id:
        return fallback_payload

    selected_menu = next((menu for menu in menu_catalog if str(menu.get("id")) == selected_display_menu_id), None)
    if not selected_menu or not selected_menu.get("option_groups"):
        return fallback_payload

    selected_options = OrderedDict()
    for group in selected_menu.get("option_groups", []):
        option_key = group.get("key")
        field_name = f"option__{option_key}"
        raw_value = form_data.getlist(field_name) if group.get("multiple") else form_data.get(field_name)

        option_entry = build_selected_option_entry(option_key, raw_value)
        if option_entry:
            selected_options[option_key] = option_entry

    if not selected_options:
        return fallback_payload

    return json.dumps(
        {
            "display_menu_id": selected_menu.get("id"),
            "display_name": selected_menu.get("name"),
            "selected_options": selected_options,
        }
    )


def infer_selected_options_from_row(row):
    inferred_options = OrderedDict()
    name_key = normalize_text(row.get("name"))

    if "big fried chicken original" in name_key or "ayam ori chilin" in name_key:
        option_entry = build_selected_option_entry("fried_style", "ori")
        if option_entry:
            inferred_options["fried_style"] = option_entry
    elif "big fried chicken bubble" in name_key or "ayam bubble chilin" in name_key:
        option_entry = build_selected_option_entry("fried_style", "bubble")
        if option_entry:
            inferred_options["fried_style"] = option_entry

    if " small" in name_key:
        option_entry = build_selected_option_entry("fried_size", "small")
        if option_entry:
            inferred_options["fried_size"] = option_entry
    elif " large" in name_key:
        option_entry = build_selected_option_entry("fried_size", "large")
        if option_entry:
            inferred_options["fried_size"] = option_entry

    if " dingin" in name_key or " ice" in name_key:
        option_entry = build_selected_option_entry("temperature", "ice")
        if option_entry:
            inferred_options["temperature"] = option_entry
    elif " panas" in name_key or name_key.endswith(" hot"):
        option_entry = build_selected_option_entry("temperature", "hot")
        if option_entry:
            inferred_options["temperature"] = option_entry
    elif name_key in {"teh tawar", "teh manis", "kopi hitam", "kopi susu", "nutrisari panas", "jeruk nipis", "jeruk manis", "lemon tea"}:
        option_entry = build_selected_option_entry("temperature", "hangat")
        if option_entry:
            inferred_options["temperature"] = option_entry

    if "dada tuna bakar" in name_key or "paket dada tuna bakar" in name_key:
        option_entry = build_selected_option_entry("cook_style", "bakar")
        if option_entry:
            inferred_options["cook_style"] = option_entry
    elif "dada tuna goreng" in name_key or "paket dada tuna goreng" in name_key:
        option_entry = build_selected_option_entry("cook_style", "goreng")
        if option_entry:
            inferred_options["cook_style"] = option_entry

    if "pisang goreng raja" in name_key:
        option_entry = build_selected_option_entry("banana_type", "raja")
        if option_entry:
            inferred_options["banana_type"] = option_entry
    elif "pisang goreng pagata" in name_key:
        option_entry = build_selected_option_entry("banana_type", "pagata")
        if option_entry:
            inferred_options["banana_type"] = option_entry

    if "gulmer" in name_key:
        option_entry = build_selected_option_entry("serut_style", "gulmer")
        if option_entry:
            inferred_options["serut_style"] = option_entry
    elif "sirup" in name_key:
        option_entry = build_selected_option_entry("serut_style", "sirup")
        if option_entry:
            inferred_options["serut_style"] = option_entry

    if "buah naga" in name_key:
        option_entry = build_selected_option_entry("juice_fruit", "buah_naga")
        if option_entry:
            inferred_options["juice_fruit"] = option_entry
    elif "avocado" in name_key or "alpukat" in name_key:
        option_entry = build_selected_option_entry("juice_fruit", "alpukat")
        if option_entry:
            inferred_options["juice_fruit"] = option_entry
    elif "sirsak" in name_key:
        option_entry = build_selected_option_entry("juice_fruit", "sirsak")
        if option_entry:
            inferred_options["juice_fruit"] = option_entry

    return inferred_options


def get_effective_selected_options(row):
    payload = normalize_menu_options_payload(row.get("menu_options_json"))
    selected_options = OrderedDict(payload.get("selected_options") or {})
    inferred_options = infer_selected_options_from_row(row)

    for option_key, option in inferred_options.items():
        selected_options.setdefault(option_key, option)

    return selected_options


def resolve_menu_submission(menu_catalog, submitted_menu_id, display_menu_id=None, menu_options_json=None):
    payload = normalize_menu_options_payload(menu_options_json)
    effective_display_menu_id = str(display_menu_id or payload.get("display_menu_id") or "").strip()

    if effective_display_menu_id:
        selected_menu = next((menu for menu in menu_catalog if str(menu.get("id")) == effective_display_menu_id), None)
        if selected_menu:
            if selected_menu.get("combo_map"):
                option_values = extract_selected_option_values(menu_options_json)
                combo_key = serialize_combo_key(option_values, selected_menu.get("combo_keys", []))
                resolved_choice = selected_menu.get("combo_map", {}).get(combo_key) or next(
                    iter(selected_menu.get("combo_map", {}).values()), None
                )
                if resolved_choice and resolved_choice.get("menu_id") is not None:
                    return int(resolved_choice["menu_id"])

            if selected_menu.get("menu_id") is not None:
                return int(selected_menu["menu_id"])

    submitted_menu_id = str(submitted_menu_id or "").strip()
    if submitted_menu_id == "":
        return None

    if submitted_menu_id.lstrip("-").isdigit():
        return int(submitted_menu_id)

    return None


def format_option_display_value(raw_value):
    return ", ".join(normalize_option_value_list(raw_value))


def build_option_summary_from_payload(menu_options_payload):
    payload = normalize_menu_options_payload(menu_options_payload)
    selected_options = payload.get("selected_options") or {}
    summary_parts = []

    for option in selected_options.values():
        label = (option.get("label") or "").strip()
        display = format_option_display_value(option.get("display"))
        if label and display:
            summary_parts.append(f"{label}: {display}")

    return " | ".join(summary_parts)


def build_option_summary_from_row(row):
    summary_parts = []

    for option in (row.get("effective_selected_options") or get_effective_selected_options(row)).values():
        label = (option.get("label") or "").strip()
        display = format_option_display_value(option.get("display"))
        if label and display:
            summary_parts.append(f"{label}: {display}")

    return " | ".join(summary_parts)


def normalize_base_menu_name(menu_name, serving_type):
    cleaned_name = re.sub(r"\s+", " ", (menu_name or "").strip())
    if not cleaned_name:
        return "-"

    base_name = re.sub(r"\s*\((paket|package|pcs|piece|porsi|portion|menu_piece)\)\s*$", "", cleaned_name, flags=re.IGNORECASE).strip()
    base_name = re.sub(r"\s+(pcs|piece|porsi|portion)\s*$", "", base_name, flags=re.IGNORECASE).strip()

    if normalize_serving_type(serving_type) == "paket":
        base_name = re.sub(r"^(paket|package)\s+", "", base_name, flags=re.IGNORECASE).strip()

    if not base_name:
        return cleaned_name

    return base_name


def get_payload_display_name(menu_options_payload, fallback_name, fallback_serving_type=None):
    payload = normalize_menu_options_payload(menu_options_payload)
    payload_name = (payload.get("display_name") or "").strip()
    if payload_name:
        return payload_name
    return normalize_base_menu_name(fallback_name, fallback_serving_type)


def build_menu_display_note(menu_options_payload, custom_note=None):
    option_summary = build_option_summary_from_payload(menu_options_payload)
    note_parts = []

    if option_summary:
        note_parts.append(option_summary)

    if custom_note:
        note_parts.append(custom_note.strip())

    return " | ".join(part for part in note_parts if part)


def build_menu_display_note_from_row(row):
    note_parts = []
    option_summary = build_option_summary_from_row(row)
    custom_note = (row.get("dish_description") or "").strip()

    if option_summary:
        note_parts.append(option_summary)

    if custom_note:
        note_parts.append(custom_note)

    return " | ".join(part for part in note_parts if part)


def get_latest_menu_status_map(cursor, selected_date):
    cursor.execute(
        """
    SELECT menu_id, status, stock_date, id
    FROM daily_menu_stock
    WHERE stock_date <= %s
    ORDER BY stock_date DESC, id DESC
    """,
        (selected_date,),
    )

    status_map = {}
    for row in cursor.fetchall():
        menu_id = row_value(row, "menu_id", 0)
        if menu_id not in status_map:
            status_map[menu_id] = row
    return status_map


def get_latest_nila_status_map(cursor, selected_date):
    cursor.execute(
        """
    SELECT id, size_category, status, stock_date
    FROM fish_stock
    WHERE fish_type_id = 4
    AND size_category IS NOT NULL
    AND stock_date <= %s
    ORDER BY stock_date DESC, id DESC
    """,
        (selected_date,),
    )

    nila_map = {}
    for row in cursor.fetchall():
        size_key = row_value(row, "size_category", 1)
        if size_key not in nila_map:
            nila_map[size_key] = row
    return nila_map


def get_latest_daily_item_stock_rows(cursor, menu_ids, selected_date):
    if not menu_ids:
        return []

    placeholders = ",".join(["%s"] * len(menu_ids))
    cursor.execute(
        f"""
        SELECT
            ds.id,
            ds.menu_id,
            ds.weight_ons,
            COALESCE(ds.weight_unit,'ons') AS weight_unit,
            ds.available_qty,
            ds.status,
            ds.stock_date,
            m.name
        FROM daily_item_stock ds
        JOIN menus m ON m.id = ds.menu_id
        WHERE ds.menu_id IN ({placeholders})
        AND ds.stock_date <= %s
        ORDER BY ds.stock_date DESC, ds.id DESC
        """,
        list(menu_ids) + [selected_date],
    )

    latest_rows = OrderedDict()
    for row in cursor.fetchall():
        row_key = (row_value(row, "menu_id", 1), float(row_value(row, "weight_ons", 2, 0) or 0))
        if row_key not in latest_rows:
            latest_rows[row_key] = row
    return list(latest_rows.values())


def get_latest_option_stock_map(cursor, selected_date):
    cursor.execute(
        """
    SELECT
        option_key,
        option_value,
        status,
        stock_date,
        id
    FROM menu_option_stock
    WHERE stock_date <= %s
    ORDER BY stock_date DESC, id DESC
    """,
        (selected_date,),
    )

    option_map = {}
    for row in cursor.fetchall():
        option_key = row_value(row, "option_key", 0)
        option_value = row_value(row, "option_value", 1)
        pair_key = (option_key, option_value)
        if pair_key not in option_map:
            option_map[pair_key] = row_value(row, "status", 2, "ready")
    return option_map


def get_latest_sea_fish_stock_rows(cursor, selected_date):
    cursor.execute(
        """
    SELECT
        fs.id,
        fs.fish_type_id,
        ft.name,
        fs.weight_ons,
        COALESCE(fs.weight_unit,'ons') AS weight_unit,
        fs.fish_count,
        fs.status,
        fs.stock_date
    FROM fish_stock fs
    JOIN fish_types ft ON ft.id = fs.fish_type_id
    WHERE fs.stock_date <= %s
    AND ft.fish_category = 'sea'
    ORDER BY fs.stock_date DESC, fs.id DESC
    """,
        (selected_date,),
    )

    latest_rows = OrderedDict()
    for row in cursor.fetchall():
        row_key = (row_value(row, "fish_type_id", 1), float(row_value(row, "weight_ons", 3, 0) or 0))
        if row_key not in latest_rows:
            latest_rows[row_key] = row

    return list(latest_rows.values())


def apply_option_stock_to_catalog(menu_catalog, option_stock_map):
    for menu in menu_catalog:
        updated_groups = []
        for group in menu.get("option_groups", []):
            group_copy = dict(group)
            updated_choices = []
            for choice in group.get("choices", []):
                choice_copy = dict(choice)
                choice_status = option_stock_map.get((group.get("key"), choice.get("value")), "ready")
                choice_copy["status"] = choice_status
                updated_choices.append(choice_copy)
            group_copy["choices"] = updated_choices
            updated_groups.append(group_copy)
        menu["option_groups"] = updated_groups
    return menu_catalog


def validate_menu_option_stock(cursor, reservation_date, menu_options_json):
    payload = normalize_menu_options_payload(menu_options_json)
    selected_options = payload.get("selected_options") or {}
    if not selected_options:
        return True, None

    option_status_map = get_latest_option_stock_map(cursor, reservation_date)
    for option_key, option in selected_options.items():
        selected_values = normalize_option_value_list(option.get("value"))
        if not selected_values:
            continue

        selected_displays = normalize_option_value_list(option.get("display"))
        for index, selected_value in enumerate(selected_values):
            current_status = option_status_map.get((option_key, selected_value), "ready")
            if current_status != "ready":
                option_label = option.get("label") or option_key
                option_display = selected_displays[index] if index < len(selected_displays) else selected_value
                return False, f"Pilihan {option_label} - {option_display} sedang not ready."

    return True, None


def ensure_menu_catalog_updates(cursor):
    cursor.execute(
        """
        UPDATE menus
        SET divisi = 'local'
        WHERE LOWER(name) = 'udang sambal pete'
        AND divisi <> 'local'
    """
    )
    cursor.execute(
        """
        UPDATE menus
        SET divisi = 'seafood'
        WHERE LOWER(name) = 'paket tuna goreng rica'
        AND divisi <> 'seafood'
    """
    )
    cursor.execute(
        """
        INSERT INTO menus (name, category, serving_type, stock_type, divisi, price)
        SELECT %s, %s, %s, %s, %s, %s
        FROM DUAL
        WHERE NOT EXISTS (
            SELECT 1
            FROM menus
            WHERE LOWER(name) = %s
            AND serving_type = %s
        )
    """,
        (
            "Paket Tuna Goreng Rica",
            "ikan tuna",
            "paket",
            "normal",
            "seafood",
            35000,
            "paket tuna goreng rica",
            "paket",
        ),
    )
    cursor.execute(
        """
        INSERT INTO menus (name, category, serving_type, stock_type, divisi, price)
        SELECT %s, %s, %s, %s, %s, %s
        FROM DUAL
        WHERE NOT EXISTS (
            SELECT 1
            FROM menus
            WHERE LOWER(name) = %s
            AND serving_type = %s
        )
    """,
        (
            "Tahu/Tempe Goreng Crispy",
            "side",
            "porsi",
            "normal",
            "seafood",
            20000,
            "tahu/tempe goreng crispy",
            "porsi",
        ),
    )


def build_display_menu_catalog(raw_menus):
    catalog = []

    for raw_menu in raw_menus:
        name_key = normalize_text(raw_menu.get("name"))
        single_config = MENU_SINGLE_OPTION_CONFIGS.get(name_key, {})
        catalog.append(
            {
                "id": f"raw::{raw_menu.get('id')}",
                "name": single_config.get("display_name") or raw_menu.get("name"),
                "category": raw_menu.get("category"),
                "divisi": raw_menu.get("divisi"),
                "stock_type": raw_menu.get("stock_type"),
                "stock_source": raw_menu.get("stock_source") or raw_menu.get("stock_type"),
                "status": raw_menu.get("status") or "ready",
                "price": raw_menu.get("price"),
                "option_groups": single_config.get("option_groups", []),
                "combo_keys": [],
                "combo_map": {},
                "menu_id": raw_menu.get("id"),
                "actual_menu_name": raw_menu.get("name"),
                "serving_type": raw_menu.get("serving_type"),
            }
        )

    combo_groups = OrderedDict()
    for group in MENU_DISPLAY_GROUPS:
        group_map = {
            "id": group["id"],
            "name": group["name"],
            "category": None,
            "divisi": None,
            "stock_type": None,
            "stock_source": None,
            "status": "ready",
            "price": None,
            "option_groups": group.get("option_groups", []),
            "combo_keys": group.get("combo_keys", []),
            "combo_map": OrderedDict(),
            "menu_id": None,
            "actual_menu_name": None,
            "serving_type": None,
        }

        for variant in group.get("combo_variants", []):
            raw_menu = next(
                (row for row in raw_menus if normalize_text(row.get("name")) == normalize_text(variant.get("name"))),
                None,
            )
            if not raw_menu:
                continue

            combo_key = serialize_combo_key(variant.get("combo", {}), group.get("combo_keys", []))
            group_map["combo_map"][combo_key] = {
                "menu_id": raw_menu.get("id"),
                "menu_name": raw_menu.get("name"),
                "serving_type": variant.get("serving_type") or raw_menu.get("serving_type"),
                "combo": variant.get("combo", {}),
            }
            group_map["category"] = group_map["category"] or raw_menu.get("category")
            group_map["divisi"] = group_map["divisi"] or raw_menu.get("divisi")
            group_map["stock_type"] = group_map["stock_type"] or raw_menu.get("stock_type")
            group_map["stock_source"] = group_map["stock_source"] or raw_menu.get("stock_source") or raw_menu.get("stock_type")
            group_map["price"] = group_map["price"] or raw_menu.get("price")
            if raw_menu.get("status") != "ready":
                group_map["status"] = raw_menu.get("status")

        if group_map["combo_map"]:
            combo_groups[group["id"]] = group_map

    catalog.extend(combo_groups.values())
    return sorted(catalog, key=lambda item: normalize_text(item.get("name")))
