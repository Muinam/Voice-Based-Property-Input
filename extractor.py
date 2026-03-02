# extractor.py - Updated with million support in price extraction

import re

WORD_TO_NUMBER = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "madhala": "marla", "madala": "marla", "mala": "marla",
    "dh4": "DHA phase 4", "dha 4": "DHA 4", "dha4": "DHA 4", "dh": "DHA",
    "isla mawa": "Islamabad", "islamawa": "Islamabad", "islama": "Islamabad",
    "go over": "crore", "go": "crore", "over": "crore",
}

def normalize_number(val):
    if not val:
        return None
    val = val.lower().strip()
    return WORD_TO_NUMBER.get(val, val)

def post_process_field(field, value):
    """
    Speech errors ko thoda sahi karne ki koshish
    - String aur list dono handle karega
    - Features ke liye list return karega
    """
    
    # None ya N/A ko waise hi return
    if value is None or value == "N/A":
        return value

    # ────────────────────────────────────────────────
    # Agar value LIST hai (features ke liye common)
    # ────────────────────────────────────────────────
    if isinstance(value, list):
        # Har item ko individually process karo
        processed_list = []
        for item in value:
            if isinstance(item, str):
                # String item ko process karo (recursive call)
                processed_item = post_process_field(field, item)
                processed_list.append(processed_item)
            else:
                # Non-string item waise hi rakh do
                processed_list.append(item)
        return processed_list

    # ────────────────────────────────────────────────
    # Agar value STRING hai (price, size, city, area etc.)
    # ────────────────────────────────────────────────
    if not isinstance(value, str):
        return value  # safety fallback (unexpected type)

    # Ab string safe hai → lower aur strip kar sakte hain
    value = value.lower().strip()

    # Price normalization
    if field == "price":
        value = (value.replace("pkr", "")
                      .replace("rupees", "")
                      .replace("per month", "monthly")
                      .replace("one go over", "1 crore")
                      .replace("one crore", "1 crore"))
        value = re.sub(r'(\d+)\s*(crore|lakh|thousand|million|monthly)', r'\1 \2', value)
        return value.title()

    # Size normalization
    if field == "size":
        value = (value.replace("madhala", "marla")
                      .replace("madala", "marla")
                      .replace("mala", "marla"))
        value = re.sub(r'(\d+)\s*marla', r'\1 Marla', value, flags=re.I)
        return value.title()

    # City / Area common speech mistakes
    if field in ["city", "area"]:
        value = (value.replace("isla mawa", "Islamabad")
                      .replace("islama", "Islamabad")
                      .replace("dh4", "DHA 4")
                      .replace("dha4", "DHA 4")
                      .replace("dh", "DHA"))
        return value.title()

    # Features short words (optional extra layer)
    if field == "features":
        short_map = {
            "f": "furnished",
            "p": "parking",
            "por": "parking",
            "c": "corner",
            "g": "gas",
            "b": "balcony",
            "ba": "basement"
        }
        if value in short_map:
            return short_map[value].capitalize()
        return value.capitalize()

    # Default case – just capitalize
    return value.capitalize()

def extract_details(text, current_field=None):
    print("Raw input:", text)
    data = {
        "property_type": None, "city": None, "area": None, "size": None,
        "bedrooms": None, "bathrooms": None, "price": None, "listing_type": None,
        "features": []
    }
    t = text.lower().strip()

    if current_field == "listing_type":
        if t in ["s", "sale"]: data["listing_type"] = "Sale"
        elif t in ["r", "rent"]: data["listing_type"] = "Rent"
    elif current_field == "property_type":
        if t in ["h", "house"]: data["property_type"] = "House"
        elif t in ["a", "apartment", "f", "flat"]: data["property_type"] = "Apartment"
    elif current_field == "city":
        data["city"] = text.title()
    elif current_field == "area":
        data["area"] = text.title().replace("Dha", "DHA")
    elif current_field == "size":
        m = re.search(r'(\d+(?:\.\d+)?)\s*(marla|kanal|sq ?feet|sqft)', t)
        if m:
            data["size"] = f"{m.group(1)} {m.group(2).title()}"
        else:
            data["size"] = text
    elif current_field in ["bedrooms", "bathrooms"]:
        val = normalize_number(t)
        if val and val.isdigit():
            data[current_field] = val
    elif current_field == "price":
        t = t.replace("per month", "monthly").replace("pkr", "").strip()
        # ────────────────────────────────────────────────
        # Updated regex to include "million"
        # ────────────────────────────────────────────────
        parts = re.findall(r'(\d+(?:\.\d+)?)\s*(crore|lakh|thousand|million|monthly)', t)
        if parts:
            price_str = " ".join(f"{num} {unit.title()}" for num, unit in parts)
            data["price"] = price_str
        else:
            data["price"] = text.title()
    elif current_field == "features":
        if t == "none":
            data["features"] = []
        else:
            known = ["parking", "furnished", "corner", "gas", "balcony", "basement", "park facing", "lift", "far", "again"]
            extracted = [f.capitalize() for f in known if f in t]
            if not extracted:
                # fallback: split by commas/space
                extracted = [word.strip().capitalize() for word in re.split(r'[ ,]+', text) if word]
            data["features"] = extracted

    # Fallback
    if current_field and not data.get(current_field) and text:
        data[current_field] = text

    # Post-processing – speech errors fix (safe for list & string)
    if current_field and data.get(current_field) is not None:
        processed_value = post_process_field(current_field, data[current_field])
        data[current_field] = processed_value

    return data