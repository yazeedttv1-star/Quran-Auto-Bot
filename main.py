import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

RECITERS = [
    {"name": "الشيخ مشاري العفاسي", "id": "ar.alafasy", "server": "https://server8.mp3quran.net/afs/"},
    {"name": "الشيخ ماهر المعيقلي", "id": "ar.mahermuaiqly", "server": "https://server12.mp3quran.net/maher/"},
    {"name": "الشيخ عبد الباسط عبد الصمد", "id": "ar.abdulsamad", "server": "https://server7.mp3quran.net/basit/"},
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi", "server": "https://server11.mp3quran.net/minsh/"}
]

HISTORY_FILE = "history.txt"

def get_viewed_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_history(entry):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def download_arabic_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"فشل جلب الخط: {e}")
    return font_path

def create_text_image(text, font_path, width=720, height=1280):
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 42)
    except Exception:
        font = ImageFont.load_default()
        
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return np.array(img)

def get_quran_meta():
    reciter = random.choice(RECITERS)
    history = get_viewed_history()
    surah_num = random.randint(1, 114)
    
    api_url = f"https://api.alquran.cloud/v1/surah/{surah_num}/{reciter['id']}"
    
    try:
        r = requests.get(api_url, timeout=20)
        if r.status_code == 200:
            data = r.json()['data']
            surah_name = data['name']
            ayahs = data['ayahs']
            total_ayahs = len(ayahs)
            
            if total_ayahs <= 8:
                selected_ayahs = ayahs
                history_entry = f"{surah_num}_all"
                if history_entry in history:
                    return get_quran_meta()
                save_to_history(history_entry)
                is_full = True
                start_ayah_idx = 0
            else:
                start_ayah_idx = random.randint(0, total_ayahs - 6)
                selected_ayahs = ayahs[start_ayah_idx : start_ayah_idx + 6]
                history_entry = f"{surah_num}_{start_ayah_idx}_{start_ayah_idx+6}"
                if history_entry in history:
                    return get_quran_meta()
                save_to_history(history_entry)
                is_full = False
                
            return surah_num, selected_ayahs, surah_name, reciter, is_full, start_ayah_idx
    except Exception as e:
        print(f"خطأ الـ API: {e}")
        
    fallback_ayahs = [{"text": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ"}, {"text": "فَصَلِّ لِرَبِّكَ وَانْحَرْ"}, {"text": "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ"}]
    return 108, fallback_ayahs, "سورة الكوثر", RECITERS[0], True, 0

def generate_video():
    surah_num, ayahs, surah_name, reciter, is_full, start_idx = get_quran_meta()
    font_path = download_arabic_font()
    
    surah_str = str(surah_num).zfill(3)
    audio_url = f"{reciter['server']}{surah_str}.mp3"
    full_audio_path = "temp_full_surah.mp3"
    
    print(f"جاري تحميل تلاوة {surah_name} بصوت {reciter['name']}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(audio_url, timeout=25, headers=headers, verify=False)
    with open(full_audio_path, "wb") as f:
        f.write(r.content)
        
    full_audio = AudioFileClip(full_audio_path)
    audio_duration = full_audio.duration
    
    # حساب مرن وآمن للمدد لتجنب تجاوز طول ملف الـ mp3 الفعلي
    total_segments = len(ayahs) if is_full else (len(ayahs) + start_idx)
    single_duration = audio_duration / max(total_segments, 1)
    
    subtitles = []
    current_time = 0.0
    
    for i, ayah in enumerate(ayahs):
        text = ayah['text']
        if i == 0 and text.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") and surah_num not in [1, 9]:
            text = text.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
            
        duration = single_duration
        subtitles.append({
            "text": text,
            "start_s": current_time,
            "end_s": current_time + duration
        })
        current_time += duration
        
    video_duration = current_time
    fps = 10
    total_frames = int(video_duration * fps)
    
    frames = []
    for frame_idx in range(total_frames):
        frame_time = frame_idx / fps
        current_text = ""
        for sub in subtitles:
            if sub["start_s"] <= frame_time < sub["end_s"]:
                current_text = sub["text"]
                break
        frames.append(create_text_image(current_text, font_path))
        
    video_clip = ImageSequenceClip(frames, fps=fps)
    
    # قص الصوت بشكل آمن تماماً ليتطابق مع الفريمات
    if is_full:
        final_audio_clip = full_audio.subclip(0, min(video_duration, audio_duration))
    else:
        start_cut = start_idx * single_duration
        end_cut = start_cut + video_duration
        final_audio_clip = full_audio.subclip(start_cut, min(end_cut, audio_duration))
        
    video_clip = video_clip.set_audio(final_audio_clip)
    
    output_filename = "quran_chroma.mp4"
    video_clip.write_videofile(
        output_filename,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    # إغلاق كتل الصوت والفيديو بشكل سليم لتحرير الملفات قبل محاولة الحذف من النظام
    video_clip.close()
    final_audio_clip.close()
    full_audio.close()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    type_text = "سورة كاملة" if is_full else "مقطع خاشع (٦ آيات متتالية)"
    caption_text = (
        f"📖 {surah_name} ({type_text})\n"
        f"🎙️ بصوت {reciter['name']}\n"
        f"✨ كروما سوداء جاهزة للتصميم والمونتاج\n\n"
        f"بواسطة المطور: {YOUR_NAME}"
    )
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url,
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
            files={'video': video_file}
        )
        
    # حذف آمن للملفات المؤقتة بعد تحريرها بالكامل
    cleanup_files = [full_audio_path, output_filename, font_path]
    for file in cleanup_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"فشل حذف الملف {file}: {e}")
            
    if response.status_code == 200:
        print("====================================")
        print(f"تم الإرسال بنجاح! السورة: {surah_name} ✅")
        print("====================================")
    else:
        print(f"فشل الإرسال، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
