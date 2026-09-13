import gc
import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

# استيرادات MoviePy 2.x
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import moviepy.video.fx as vfx

# --- الإعدادات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.txt"
TARGET_DURATION = 50.0
TIKTOK_USERNAME = "@a.m_4.4"

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
            r = requests.get(url, timeout=10)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception:
            return None
    return font_path

def create_static_info_image(surah_name, reciter_name, font_path, width=720, height=1280):
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_sub = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        font_user = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
    except Exception:
        font_sub = ImageFont.load_default()
        font_user = ImageFont.load_default()

    bbox_user = draw.textbbox((0, 0), TIKTOK_USERNAME, font=font_user)
    w_user = bbox_user[2] - bbox_user[0]
    draw.text(((width - w_user) // 2, 120), TIKTOK_USERNAME, fill=(180, 180, 180, 180), font=font_user)

    info_text = f"سورة {surah_name} ﴿ {reciter_name} ﴾"
    bbox_info = draw.textbbox((0, 0), info_text, font=font_sub, direction="rtl", language="ar")
    w_info = bbox_info[2] - bbox_info[0]
    x_info = (width - w_info) // 2
    
    y_position = height - 220
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
    y_start = (height // 2) - ((len(lines) * line_height) // 2) - 40
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_ayah, direction="rtl", language="ar")
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        
        draw.text((x+2, y_start+2), line, fill=(0, 0, 0, 200), font=font_ayah, direction="rtl", language="ar")
        draw.text((x, y_start), line, fill=(255, 255, 255, 255), font=font_ayah, direction="rtl", language="ar")
        y_start += line_height

    return np.array(img)

def fetch_quran_data():
    history = load_history()
    reciter = random.choice(RECITERS)

    for _ in range(30):
        surah = random.randint(1, 114)
        try:
            url = f"https://api.alquran.cloud/v1/surah/{surah}/{reciter['id']}"
            res = requests.get(url, timeout=5).json()
            ayahs = res["data"]["ayahs"]

            start = random.randint(0, max(0, len(ayahs) - 3))
            selected = ayahs[start:]
            entry = f"{surah}_{start}_{reciter['id']}"

            if entry not in history:
                save_history(entry)
                return selected, res["data"]["name"], reciter["name"]
        except Exception:
            continue

    fallback_ayahs = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/1.mp3"},
        {"text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/2.mp3"},
    ]
    return fallback_ayahs, "الفاتحة", RECITERS[0]["name"]

def download_single_audio(args):
    index, url = args
    filename = f"temp_{index}.mp3"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filename, "wb") as f:
                f.write(r.content)
            return index, filename
    except Exception:
        pass
    return index, None

def build_batch():
    # محاولة جلب فيديو ناجح حتى 10 مرات؛ إذا فشلت سورة يتم الانتقال لأخرى تلقائياً
    for _ in range(10):
        ayahs, surah_name, reciter_name = fetch_quran_data()
        
        selected_ayahs = []
        urls_to_download = []
        
        for i, ayah in enumerate(ayahs):
            if ayah.get("audio"):
                selected_ayahs.append(ayah)
                urls_to_download.append((i, ayah["audio"]))
            if len(selected_ayahs) >= 12:
                break

        downloaded_files = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(download_single_audio, urls_to_download)
            for idx, filepath in results:
                if filepath:
                    downloaded_files[idx] = filepath

        downloaded = []
        current_duration = 0.0
        success = True

        for i, ayah in enumerate(selected_ayahs):
            if i in downloaded_files:
                file_path = downloaded_files[i]
                try:
                    clip = AudioFileClip(file_path)
                    downloaded.append((ayah, file_path, clip))
                    current_duration += clip.duration

                    if current_duration >= TARGET_DURATION:
                        break
                except Exception:
                    success = False
                    break
            else:
                success = False
                break

        # إذا نجح تحميل المقاطع الصوتية كاملة للآيات، يتم إرجاعها
        if success and len(downloaded) > 0:
            return downloaded, surah_name, reciter_name

        # في حال وجود أي خطأ في التحميل، يتم تنظيف الملفات المؤقتة وإعادة المحاولة بسورة أخرى
        for _, f, c in downloaded:
            try:
                c.close()
            except Exception:
                pass
            if os.path.exists(f):
                os.remove(f)

    raise Exception("تعذر جلب مقطع صالح، تم تجاوز المحاولات.")

def generate_tiktok_script(surah_name, reciter_name, duration_sec):
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{seconds} ثانية" if minutes == 0 else f"{minutes}:{seconds:02d} دقيقة"

    return f"سورة {surah_name} | {duration_str}\nالقارئ {reciter_name}"

def generate_video():
    font_path = get_font()
    downloaded, surah_name, reciter_name = build_batch()

    audio_clips = []
    ayah_clips = []

    for idx, (ayah, file_path, clip) in enumerate(downloaded):
        audio_clips.append(clip)

        ayah_img = create_ayah_text_image(ayah['text'], font_path)
        ayah_clip = ImageClip(ayah_img).with_duration(clip.duration)
        
        if clip.duration > 0.6:
            ayah_clip = ayah_clip.with_effects([
                vfx.FadeIn(0.2),
                vfx.FadeOut(0.2)
            ])
            
        ayah_clips.append(ayah_clip)

    final_audio = concatenate_audioclips(audio_clips)
    total_duration = final_audio.duration

    static_info_img = create_static_info_image(surah_name, reciter_name, font_path)
    background_clip = ImageClip(static_info_img).with_duration(total_duration)

    concat_ayahs = concatenate_videoclips(ayah_clips, method="compose")
    final_video = CompositeVideoClip([background_clip, concat_ayahs]).with_audio(final_audio)

    output_path = "quran_video.mp4"
    
    final_video.write_videofile(
        output_path, 
        fps=20, 
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
                requests.post(
                    url,
                    files={"video": video_file},
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                    timeout=120,
                )

if __name__ == "__main__":
    try:
        print("🚀 بدء إنشاء المقطع واختيار سورة جديدة تلقائياً...")
        output_video, caption_text = generate_video()
        print(f"✅ تم الإنشاء والتصدير بنجاح: {output_video}")
        send_to_telegram(output_video, caption_text)
    except Exception as err:
        print(f"❌ حدث خطأ أثناء التشغيل: {err}")
