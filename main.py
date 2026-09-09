import gc
import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# استيرادات MoviePy 2.x
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, concatenate_audioclips
import moviepy.video.fx as vfx

# --- الإعدادات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.txt"
TARGET_DURATION = 50.0  # مدة الفيديو المستهدفة ~50 ثانية

RECITERS = [
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary"},
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary"},
    {"name": "الشيخ حسن صالح", "id": "ar.hassansaleh"},
    {"name": "الشيخ محمود علي البنا", "id": "ar.mahmoudalibanna"},
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

def create_tiktok_chroma_image(ayah_text, surah_name, reciter_name, font_path, width=1080, height=1920):
    # خلفية سوداء جبارة لمقاس TikTok
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_ayah = ImageFont.truetype(font_path, 60) if font_path else ImageFont.load_default()
        font_sub = ImageFont.truetype(font_path, 38) if font_path else ImageFont.load_default()
    except Exception:
        font_ayah = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # تقسيم النص الطويل تلقائياً حتى لا يخرج عن جوانب الشاشة
    words = ayah_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_ayah, direction="rtl", language="ar")
        if (bbox[2] - bbox[0]) < (width - 160):
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # رسم الآية في المنتصف
    line_height = 85
    y_start = (height // 2) - ((len(lines) * line_height) // 2)
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_ayah, direction="rtl", language="ar")
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y_start), line, fill=(255, 255, 255), font=font_ayah, direction="rtl", language="ar")
        y_start += line_height

    # كتابة بيانات السورة والقارئ بتصميم جذاب بأسفل الفيديو
    info_text = f"سورة: {surah_name} | القارئ: {reciter_name}"
    bbox_info = draw.textbbox((0, 0), info_text, font=font_sub, direction="rtl", language="ar")
    w_info = bbox_info[2] - bbox_info[0]
    x_info = (width - w_info) // 2
    
    # إطار بسيط وجمالي
    draw.text((x_info, height - 280), info_text, fill=(200, 200, 200), font=font_sub, direction="rtl", language="ar")

    return np.array(img)

def fetch_quran_data():
    history = load_history()
    reciter = random.choice(RECITERS)

    for _ in range(20):
        surah = random.randint(1, 114)
        try:
            url = f"https://api.alquran.cloud/v1/surah/{surah}/{reciter['id']}"
            res = requests.get(url, timeout=10).json()
            ayahs = res["data"]["ayahs"]

            # إذا كانت سورة قصيرة (أقل من 10 آيات) آخذ السورة كاملة مهما كانت مدتها
            if len(ayahs) <= 10:
                selected = ayahs
                entry = f"full_{surah}_{reciter['id']}"
            else:
                # إذا كانت سورة طويلة نختار مجموعة آيات عشوائية تقترب مدتها من 50 ثانية
                start = random.randint(0, len(ayahs) - 5)
                selected = ayahs[start : start + 6]
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

        for i, ayah in enumerate(ayahs):
            file_path = f"temp_{i}.mp3"
            audio_url = ayah.get("audio")

            if audio_url and download_audio(audio_url, file_path):
                clip = AudioFileClip(file_path)
                downloaded.append((ayah, file_path, clip))
            else:
                break

        if len(downloaded) == len(ayahs):
            return downloaded, surah_name, reciter_name

        for _, f, c in downloaded:
            c.close()
            if os.path.exists(f):
                os.remove(f)

    raise Exception("فشل تحميل المقطع الصوتي.")

def generate_video():
    font_path = get_font()
    downloaded, surah_name, reciter_name = build_batch()

    audio_clips, video_clips = [], []

    for idx, (ayah, file_path, clip) in enumerate(downloaded):
        audio_clips.append(clip)

        img = create_tiktok_chroma_image(ayah['text'], surah_name, reciter_name, font_path)
        
        # إنشاء المقطع الصوري وإضافة تأثير ظهور/اختفاء ناعم (Crossfade Effect)
        img_clip = ImageClip(img).with_duration(clip.duration)
        if clip.duration > 0.8:
            img_clip = img_clip.with_effects([
                vfx.FadeIn(0.4),
                vfx.FadeOut(0.4)
            ])
            
        video_clips.append(img_clip)

    final_audio = concatenate_audioclips(audio_clips)
    final_video = concatenate_videoclips(video_clips, method="compose").with_audio(final_audio)

    output_path = "quran_video.mp4"
    
    # تصدير مناسب لـ TikTok
    final_video.write_videofile(
        output_path, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac", 
        preset="veryfast"
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
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
            with open(video_path, "rb") as video_file:
                res = requests.post(
                    url,
                    files={"video": video_file},
                    data={"chat_id": TELEGRAM_CHAT_ID},
                    timeout=120,
                )
                print(f"نتيجة إرسال تيليجرام: {res.status_code}")
        else:
            print("❌ ملف الفيديو غير موجود أو حجمه 0!")

if __name__ == "__main__":
    try:
        print("🚀 بدء إنشاء فيديو القرآن للتيك توك...")
        output = generate_video()
        print(f"✅ تم الانتهاء بنجاح: {output}")
        send_to_telegram(output)
    except Exception as err:
        print(f"❌ حدث خطأ أثناء التشغيل: {err}")
