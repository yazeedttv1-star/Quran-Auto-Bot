import gc
import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# استيرادات MoviePy 2.x
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import moviepy.video.fx as vfx

# --- الإعدادات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.txt"

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

# 1. صورة ثابتة لاسم السورة والقارئ فقط (تظهر في الخلفية طوال الفيديو)
def create_static_info_image(surah_name, reciter_name, font_path, width=540, height=960):
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_sub = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
    except Exception:
        font_sub = ImageFont.load_default()

    info_text = f"سورة {surah_name} | القارئ {reciter_name}"
    bbox_info = draw.textbbox((0, 0), info_text, font=font_sub, direction="rtl", language="ar")
    w_info = bbox_info[2] - bbox_info[0]
    x_info = (width - w_info) // 2
    
    # كتابة المعلومات ثابته بالأسفل
    draw.text((x_info, height - 120), info_text, fill=(200, 200, 200, 255), font=font_sub, direction="rtl", language="ar")

    return np.array(img)

# 2. صورة نص الآية فقط (بشفافية لتوضع فوق الخلفية الثابتة)
def create_ayah_text_image(ayah_text, font_path, width=540, height=960):
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_ayah = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()
    except Exception:
        font_ayah = ImageFont.load_default()

    words = ayah_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_ayah, direction="rtl", language="ar")
        if (bbox[2] - bbox[0]) < (width - 60):
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    line_height = 45
    y_start = (height // 2) - ((len(lines) * line_height) // 2)
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_ayah, direction="rtl", language="ar")
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y_start), line, fill=(255, 255, 255, 255), font=font_ayah, direction="rtl", language="ar")
        y_start += line_height

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

            if len(ayahs) <= 8:
                selected = ayahs
                entry = f"full_{surah}_{reciter['id']}"
            else:
                start = random.randint(0, len(ayahs) - 4)
                selected = ayahs[start : start + 4]
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
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filename, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

# كتابة السكريبت / الوصف بالتنسيق المطلوب بالضبط
def generate_tiktok_script(surah_name, reciter_name, duration_sec):
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{seconds} ثانية" if minutes == 0 else f"{minutes}:{seconds:02d} دقيقة"

    caption = (
        f"سورة {surah_name} | {duration_str}\n"
        f"القارئ {reciter_name}\n\n"
        f"#القران_الكريم #{surah_name.replace(' ', '_')} #{reciter_name.replace(' ', '_')} "
        f"#تلاوات_خاشعة #قران #راحة_نفسية #fyp #viral #foryou #اكسبلور"
    )
    return caption

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

    audio_clips = []
    ayah_clips = []

    # 1. تجهيز المقاطع الصوتية ونصوص الآيات بمؤثر خفيف لكل آية
    for idx, (ayah, file_path, clip) in enumerate(downloaded):
        audio_clips.append(clip)

        # صورة الآية الشفافة
        ayah_img = create_ayah_text_image(ayah['text'], font_path)
        ayah_clip = ImageClip(ayah_img).with_duration(clip.duration)
        
        # إضافة مؤثر خفيف (FadeIn و FadeOut) للآية فقط
        if clip.duration > 0.6:
            ayah_clip = ayah_clip.with_effects([
                vfx.FadeIn(0.3),
                vfx.FadeOut(0.3)
            ])
            
        ayah_clips.append(ayah_clip)

    final_audio = concatenate_audioclips(audio_clips)
    total_duration = final_audio.duration

    # 2. إنشاء خلفية ثابتة تحتوي على اسم السورة والقارئ طوال مدة الفيديو
    static_info_img = create_static_info_image(surah_name, reciter_name, font_path)
    background_clip = ImageClip(static_info_img).with_duration(total_duration)

    # 3. تجميع نصوص الآيات المتتابعة فوق الخلفية الثابتة
    concat_ayahs = concatenate_videoclips(ayah_clips, method="compose")
    final_video = CompositeVideoClip([background_clip, concat_ayahs]).with_audio(final_audio)

    output_path = "quran_video.mp4"
    
    # تصدير أسرع بطلب السيرفر
    final_video.write_videofile(
        output_path, 
        fps=15, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast",
        threads=4,
        logger=None
    )

    final_video.close()
    final_audio.close()
    background_clip.close()
    for _, f, c in downloaded:
        c.close()
        if os.path.exists(f):
            os.remove(f)
    gc.collect()

    # توليد الوصف/السكريبت المخصص للتيليجرام وتيك توك
    caption = generate_tiktok_script(surah_name, reciter_name, total_duration)

    return output_path, caption

def send_to_telegram(video_path, caption):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
            with open(video_path, "rb") as video_file:
                res = requests.post(
                    url,
                    files={"video": video_file},
                    data={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "caption": caption
                    },
                    timeout=120,
                )
                print(f"نتيجة إرسال تيليجرام: {res.status_code}")

if __name__ == "__main__":
    try:
        print("🚀 بدء إنشاء فيديو القرآن للتيك توك...")
        output_video, caption_text = generate_video()
        print(f"✅ تم الانتهاء بنجاح: {output_video}")
        send_to_telegram(output_video, caption_text)
    except Exception as err:
        print(f"❌ حدث خطأ أثناء التشغيل: {err}")
