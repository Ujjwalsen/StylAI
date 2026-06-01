import os
import json
from dotenv import load_dotenv
load_dotenv()

from stylist import match_outfit

user_profile = {"skin_undertone": "Neutral", "style_preference": "Casual"}
wardrobe = [
    {
        "garment_id": 1,
        "category": "Top",
        "sub_category": "T-Shirt",
        "primary_color": "Blue | #0000FF",
        "fit": "Regular",
        "color_temperature": "Cool"
    },
    {
        "garment_id": 2,
        "category": "Bottom",
        "sub_category": "Jeans",
        "primary_color": "Black | #000000",
        "fit": "Slim",
        "color_temperature": "Neutral"
    }
]

try:
    res = match_outfit(user_profile, wardrobe)
    print("Result:", res)
except Exception as e:
    print("Top level error:", e)
