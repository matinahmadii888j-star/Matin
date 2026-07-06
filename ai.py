import os
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def generate_description(title: str, extra_info: str = "") -> str:
    """Ask Gemini to write a short, catchy Persian description for the channel post."""
    prompt = (
        "یک توضیح کوتاه، جذاب و طبیعی به فارسی برای معرفی یک فیلم در یک کانال تلگرام بنویس.\n"
        f"عنوان فیلم: {title}\n"
    )
    if extra_info:
        prompt += f"اطلاعات اضافی که کاربر داده: {extra_info}\n"
    prompt += (
        "فقط ۲ تا ۴ جمله بنویس. بدون مقدمه، بدون عنوان‌بندی، مستقیم برو سراغ متن توضیح."
    )

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or "توضیحی تولید نشد."
    except Exception:
        return "توضیحی تولید نشد."
