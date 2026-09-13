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
TARGET_DURATION = 50.0  # مدة الفيديو 50 ثانية

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

# صورة اسم السورة والقارئ ثابته ومصممة بدقة لتناسب منطقة أمان تيك توك (TikTok Safe Zone)
def create_static_info_image(surah_name, reciter_name, font_path, width=720, height=1280):
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_sub = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    except Exception:
        font_sub = ImageFont.load_default()

    info_text = f"سورة {surah_name} ﴿ {reciter_name} ﴾"
    bbox_info = draw.textbbox((0, 0), info_text, font=font_sub, direction="rtl", language="ar")
    w_info = bbox_info[2] - bbox_info[0]
    x_info = (width - w_info) // 2
    
    # يوضع النص بارتفاع مناسب فوق أزرار التيك توك السفلى (تجنباً للتغطية)
    y_position = height - 220
    
    # إطار خفيف جمالي خلف اسم السورة والقارئ
    padding = 15
    draw.rounded_rectangle(
        [x_info - padding, y_position - 5, x_info + w_info + padding, y_position + 45],
        radius=10,
        fill=(20, 20, 20, 180),
        outline=(255, 255, 255, 50),
        width=1
    )
    
    draw.text((x_info, y_position), info_text, fill=(230, 230, 230, 255), font=font_sub, direction="rtl", language="ar")

    return np.array(img)

# صورة الآية القرآنية مصممة بخط أوضح ومجهزة للتيك توك
def create_ayah_text_image(ayah_text, font_path, width=720, height=1280):
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_ayah = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
    except Exception:
        font_ayah = ImageFont.load_default()

    words = ayah_text.split()
    lines = []
    current_line = []
    
    # تقسيم النص تلقائياً لكي لا يخرج عن حدود الشاشة في التيك توك
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_ayah, direction="rtl", language="ar")
        if (bbox[2] - bbox[0]) < (width - 120):
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    line_height = 65
    y_start = (height // 2) - ((len(lines) * line_height) // 2) - 40 # رفع للوسط قليلاً
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_ayah, direction="rtl", language="ar")
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        
        # إضافة ظلال خفيفة وراء الكلام لسهولة القراءة
        draw.text((x+2, y_start+2), line, fill=(0, 0, 0, 200), font=font_ayah, direction="rtl", language="ar")
        draw.text((x, y_start), line, fill=(255, 255, 255, 255), font=font_ayah, direction="rtl", language="ar")
        y_start += line_height

    return np.array(img)

def fetch_quran_data():
    history = load_history()
    reciter = random.choice(RECITERS)

    for _ in range(25):
        surah = random.randint(1, 114)
        try:
            url = f"https://api.alquran.cloud/v1/surah/{surah}/{reciter['id']}"
            res = requests.get(url, timeout=10).json()
            ayahs = res["data"]["ayahs"]

            start = random.randint(0, max(0, len(ayahs) - 3))
            selected = ayahs[start:]
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

def generate_tiktok_script(surah_name, reciter_name, duration_sec):
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{seconds} ثانية" if minutes == 0 else f"{minutes}:{seconds:02d} دقيقة"

    caption = (
        f"سورة {surah_name} | {duration_str}\n"
        f"القارئ {reciter_name}"
    )
    return caption

def build_batch():
    for _ in range(5):
        ayahs, surah_name, reciter_name, surah_num, reciter = fetch_quran_data()
        downloaded = []
        current_duration = 0.0

        for i, ayah in enumerate(ayahs):
            file_path = f"temp_{i}.mp3"
            audio_url = ayah.get("audio")

            if audio_url and download_audio(audio_url, file_path):
                clip = AudioFileClip(file_path)
                downloaded.append((ayah, file_path, clip))
                current_duration += clip.duration

                if current_duration >= TARGET_DURATION:
                    break
            else:
                break

        if len(downloaded) > 0:
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

    for idx, (ayah, file_path, clip) in enumerate(downloaded):
        audio_clips.append(clip)

        ayah_img = create_ayah_text_image(ayah['text'], font_path)
        ayah_clip = ImageClip(ayah_img).with_duration(clip.duration)
        
        # إضافة تأثير انتقالي ناعم لكل آية
        if clip.duration > 0.6:
            ayah_clip = ayah_clip.with_effects([
                vfx.FadeIn(0.3),
                vfx.FadeOut(0.3)
            ])
            
        ayah_clips.append(ayah_clip)

    final_audio = concatenate_audioclips(audio_clips)
    total_duration = final_audio.duration

    static_info_img = create_static_info_image(surah_name, reciter_name, font_path)
    background_clip = ImageClip(static_info_img).with_duration(total_duration)

    concat_ayahs = concatenate_videoclips(ayah_clips, method="compose")
    final_video = CompositeVideoClip([background_clip, concat_ayahs]).with_audio(final_audio)

    output_path = "quran_video.mp4"
    
    # التصدير بأبعاد وسرعة مثالية للسيرفر والتيك توك (720x1280 HD)
    final_video.write_videofile(
        output_path, 
        fps=24, 
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
        print("🚀 بدء إنشاء فيديو القرآن المتناسق مع تيك توك...")
        output_video, caption_text = generate_video()
        print(f"✅ تم الانتهاء بنجاح: {output_video}")
        send_to_telegram(output_video, caption_text)
    except Exception as err:
        print(f"❌ حدث خطأ أثناء التشغيل: {err}")
