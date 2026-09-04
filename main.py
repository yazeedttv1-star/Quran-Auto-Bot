import os
import random
import requests
import numpy as np
import gc
import time
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# استيراد moviepy - محاولة متعددة للمتوافقية
try:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
    import moviepy.audio.fx.all as afx
except:
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, afx
    except:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.VideoClip import ImageClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips
        import moviepy.audio.fx.all as afx

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====== الإعدادات ======
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RECITERS = [
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi", "everyayah_folder": "Minshawy_Murattal_128kbps"},
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary", "everyayah_folder": "Yasser_Ad-Dussary_128kbps"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary", "everyayah_folder": "Husary_128kbps"},
]

HISTORY_FILE = "history.txt"
AYAHS_COUNT = 5
TARGET_DURATION = 30.0
SPEED_FACTOR_MIN = 0.8
SPEED_FACTOR_MAX = 1.35

# ====== دوال مساعدة ======
def log_error(context, exc):
    print(f"❌ خطأ في {context}: {exc}")

def get_viewed_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except:
            return set()
    return set()

def save_to_history(entry):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except:
        pass

def download_arabic_font():
    font_path = "Amiri-Regular.ttf"
    if os.path.exists(font_path):
        return font_path
    try:
        url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(font_path, "wb") as f:
            f.write(r.content)
        return font_path
    except:
        return None

def create_text_image(text, font_path, width=1080, height=1920):
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 60)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # تقسيم النص لأسطر متعددة إذا كان طويلاً
    lines = text.split('\n')
    y_offset = height // 2 - (len(lines) * 40)
    
    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((width - text_width) // 2, y_offset)
        draw.text(position, line, fill=(255, 255, 255), font=font)
        y_offset += text_height + 20
    
    return np.array(img)

def get_quran_data():
    history = get_viewed_history()
    random.shuffle(RECITERS)
    
    for reciter in RECITERS:
        for _ in range(20):
            surah_num = random.randint(1, 114)
            try:
                url = f"https://api.alquran.cloud/v1/surah/{surah_num}/{reciter['id']}"
                r = requests.get(url, timeout=20)
                if r.status_code != 200:
                    continue
                
                data = r.json()['data']
                ayahs = data['ayahs']
                
                if len(ayahs) < AYAHS_COUNT:
                    continue
                
                start = random.randint(0, len(ayahs) - AYAHS_COUNT)
                selected = ayahs[start:start + AYAHS_COUNT]
                
                entry = f"{surah_num}_{start}_{reciter['id']}"
                if entry in history:
                    continue
                
                save_to_history(entry)
                return selected, data['name'], reciter['name'], surah_num, reciter
                
            except Exception as e:
                log_error(f"جلب سورة {surah_num}", e)
                time.sleep(1)
    
    # الفاتحة كخيار احتياطي
    fallback = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "number": 1},
        {"text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "number": 2},
        {"text": "الرَّحْمَٰنِ الرَّحِيمِ", "number": 3},
        {"text": "مَالِكِ يَوْمِ الدِّينِ", "number": 4},
        {"text": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "number": 5},
    ]
    return fallback, "الفاتحة", "الحصري", 1, RECITERS[2]

def download_audio(urls, filename):
    for url in urls:
        if not url:
            continue
        try:
            r = requests.get(url, timeout=30, verify=False)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(filename, "wb") as f:
                    f.write(r.content)
                return True
        except:
            continue
    return False

def build_audio_urls(ayah, surah_num, reciter):
    urls = []
    if ayah.get('audio'):
        urls.append(ayah['audio'])
    
    num = ayah.get('number')
    if num:
        urls.append(f"https://cdn.islamic.network/quran/audio/128/{reciter['id']}/{num}.mp3")
    
    in_surah = ayah.get('numberInSurah')
    if in_surah and 'everyayah_folder' in reciter:
        s = str(surah_num).zfill(3)
        a = str(in_surah).zfill(3)
        urls.append(f"https://www.everyayah.com/data/{reciter['everyayah_folder']}/{s}{a}.mp3")
    
    return urls

def build_batch():
    for _ in range(6):
        ayahs, surah_name, reciter_name, surah_num, reciter = get_quran_data()
        downloaded = []
        total = 0.0
        success = True
        
        for i, ayah in enumerate(ayahs):
            filename = f"temp_{i}.mp3"
            urls = build_audio_urls(ayah, surah_num, reciter)
            
            if not download_audio(urls, filename):
                success = False
                break
            
            try:
                clip = AudioFileClip(filename)
                total += clip.duration
                downloaded.append((ayah, filename, clip))
            except:
                success = False
                break
        
        if success and 15.0 <= total <= 50.0:
            return downloaded, surah_name, reciter_name, total
        
        # تنظيف
        for _, f, c in downloaded:
            try:
                c.close()
                os.remove(f)
            except:
                pass
        gc.collect()
    
    raise Exception("فشل تحميل الآيات")

# ====== الوظيفة الرئيسية ======
def generate_video():
    print("📥 جاري تحميل الآيات...")
    font_path = download_arabic_font()
    downloaded, surah_name, reciter_name, total = build_batch()
    
    # حساب سرعة الصوت
    speed = total / TARGET_DURATION
    speed = max(SPEED_FACTOR_MIN, min(SPEED_FACTOR_MAX, speed))
    
    audio_clips = []
    video_data = []
    
    print(f"🎵 جاري معالجة {len(downloaded)} آيات...")
    
    for ayah, filename, clip in downloaded:
        # تعديل سرعة الصوت
        adjusted = afx.speedx(clip, factor=speed)
        audio_clips.append(adjusted)
        
        # إنشاء صورة النص
        text = f"{ayah['text']}\n\nسورة {surah_name}\n{reciter_name}"
        img = create_text_image(text, font_path)
        
        duration = adjusted.duration if adjusted.duration else 3.0
        video_data.append((img, duration))
    
    print("🎬 جاري دمج الملفات...")
    
    # دمج الصوت
    final_audio = concatenate_videoclips(audio_clips)
    
    # دمج الفيديو
    video_clips = []
    for img, duration in video_data:
        clip = ImageClip(img).with_duration(duration)
        video_clips.append(clip)
    
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video = final_video.with_audio(final_audio)
    
    # حفظ الفيديو
    output = "quran_video.mp4"
    final_video.write_videofile(
        output,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None
    )
    
    # تنظيف
    final_video.close()
    final_audio.close()
    for clip in video_clips:
        clip.close()
    for _, f, c in downloaded:
        try:
            c.close()
            os.remove(f)
        except:
            pass
    
    return output

# ====== التشغيل ======
if __name__ == "__main__":
    try:
        print("🚀 بدء تشغيل البوت...")
        video = generate_video()
        print(f"✅ تم إنشاء الفيديو: {video}")
        print(f"📊 الحجم: {os.path.getsize(video) / (1024*1024):.2f} MB")
        
        # إرسال للتيليجرام إذا كانت الإعدادات موجودة
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            print("📤 جاري الإرسال للتيليجرام...")
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
            with open(video, 'rb') as f:
                files = {'video': f}
                data = {'chat_id': TELEGRAM_CHAT_ID}
                requests.post(url, files=files, data=data, timeout=60)
            print("✅ تم الإرسال للتيليجرام")
        
        print("🎉 انتهى التنفيذ بنجاح!")
        
    except Exception as e:
        print(f"❌ فشل التنفيذ: {e}")
        print(traceback.format_exc())
        exit(1)
