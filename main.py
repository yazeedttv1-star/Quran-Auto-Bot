import gc
import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# استيرادات MoviePy 2.x الحديثة
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, concatenate_audioclips
import moviepy.audio.fx as afx

# --- الإعدادات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.txt"
AYAHS_COUNT = 5
TARGET_DURATION = 30.0

RECITERS = [
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi", "folder": "Minshawy_Murattal_128kbps"},
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary", "folder": "Yasser_Ad-Dussary_128kbps"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary", "folder": "Husary_128kbps"},
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_history(entry):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{entry}\n")

def get_font():
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
            r = requests.get(url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception:
            return None
    return font_path

def format_arabic_text(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def create_text_image(text, font_path, width=1080, height=1920):
    img = Image.new("RGB", (width, height), color=(15, 15, 20))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, 50) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    lines = text.split("\n")
    formatted_lines = [format_arabic_text(line) for line in lines]
    
    y_center = height // 2 - (len(formatted_lines) * 40)

    for line in formatted_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y_center), line, fill=(255, 255, 255), font=font)
        y_center += (bbox[3] - bbox[1]) + 30

    return np.array(img)

def fetch_quran_data():
    history = load_history()
    reciter = random.choice(RECITERS)

    for _ in range(15):
        surah = random.randint(1, 114)
        try:
            url = f"https://api.alquran.cloud/v1/surah/{surah}/{reciter['id']}"
            res = requests.get(url, timeout=10).json()
            ayahs = res["data"]["ayahs"]

            if len(ayahs) < AYAHS_COUNT:
                continue

            start = random.randint(0, len(ayahs) - AYAHS_COUNT)
            selected = ayahs[start : start + AYAHS_COUNT]
            entry = f"{surah}_{start}_{reciter['id']}"

            if entry not in history:
                save_history(entry)
                return selected, res["data"]["name"], reciter["name"], surah, reciter
        except Exception:
            continue

    fallback_ayahs = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "number": 1},
        {"text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "number": 2},
    ]
    return fallback_ayahs, "الفاتحة", RECITERS[0]["name"], 1, RECITERS[0]

def download_audio(url, filename):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filename, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def build_batch():
    for _ in range(5):
        ayahs, surah_name, reciter_name, surah_num, reciter = fetch_quran_data()
        downloaded = []
        total_duration = 0.0

        for i, ayah in enumerate(ayahs):
            file_path = f"temp_{i}.mp3"
            audio_url = ayah.get("audio") or (
                f"https://www.everyayah.com/data/{reciter['folder']}/"
                f"{str(surah_num).zfill(3)}{str(ayah.get('numberInSurah', i+1)).zfill(3)}.mp3"
            )

            if download_audio(audio_url, file_path):
                clip = AudioFileClip(file_path)
                total_duration += clip.duration
                downloaded.append((ayah, file_path, clip))
            else:
                break

        if len(downloaded) == len(ayahs):
            return downloaded, surah_name, reciter_name, total_duration

        for _, f, c in downloaded:
            c.close()
            if os.path.exists(f):
                os.remove(f)

    raise Exception("فشل تحميل المقطع الصوتي.")

def generate_video():
    font_path = get_font()
    downloaded, surah_name, reciter_name, total_duration = build_batch()

    speed = max(0.8, min(1.35, total_duration / TARGET_DURATION))
    audio_clips, video_clips = [], []

    for idx, (ayah, file_path, clip) in enumerate(downloaded):
        # تطبيق سرعة الصوت في MoviePy 2.x
        adjusted_audio = clip.with_effects([afx.AudioSpeedX(factor=speed)])
        audio_clips.append(adjusted_audio)

        text_content = f"{ayah['text']}\n\nسورة {surah_name}\nالقارئ: {reciter_name}"
        img = create_text_image(text_content, font_path)
        img_clip = ImageClip(img).with_duration(adjusted_audio.duration)
        video_clips.append(img_clip)

    final_audio = concatenate_audioclips(audio_clips)
    final_video = concatenate_videoclips(video_clips, method="compose").with_audio(final_audio)

    output_path = "quran_video.mp4"
    final_video.write_videofile(
        output_path, fps=24, codec="libx264", audio_codec="aac"
    )

    final_video.close()
    final_audio.close()
    for _, f, c in downloaded:
        c.close()
        if os.path.exists(f):
            os.remove(f)
    gc.collect()

    return output_path

def send_to_telegram(video_path):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
        with open(video_path, "rb") as video_file:
            requests.post(
                url,
                files={"video": video_file},
                data={"chat_id": TELEGRAM_CHAT_ID},
                timeout=60,
            )

if __name__ == "__main__":
    try:
        print("🚀 بدء إنشاء فيديو القرآن...")
        output = generate_video()
        print(f"✅ تم الانتهاء بنجاح: {output}")
        send_to_telegram(output)
    except Exception as err:
        print(f"❌ حدث خطأ أثناء التشغيل: {err}")
