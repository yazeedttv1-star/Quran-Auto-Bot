import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

# قائمة القراء المعتمدين في نظام الآيات المزامنة عبر سرفرات التوزيع العالمية
RECITERS = [
    {"name": "الشيخ مشاري العفاسي", "id": "ar.alafasy"},
    {"name": "الشيخ ماهر المعيقلي", "id": "ar.mahermuaiqly"},
    {"name": "الشيخ عبد الباسط عبد الصمد", "id": "ar.abdulsamad"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary"},
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi"}
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

def get_precise_quran_data():
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
                    return get_precise_quran_data()
                save_to_history(history_entry)
                is_full = True
            else:
                start_ayah_idx = random.randint(0, total_ayahs - 6)
                selected_ayahs = ayahs[start_ayah_idx : start_ayah_idx + 6]
                history_entry = f"{surah_num}_{start_ayah_idx}_{start_ayah_idx+6}"
                if history_entry in history:
                    return get_precise_quran_data()
                save_to_history(history_entry)
                is_full = False
                
            return selected_ayahs, surah_name, reciter['name'], is_full
    except Exception as e:
        print(f"خطأ الـ API: {e}")
        
    fallback_ayahs = [
        {"text": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5418.mp3"},
        {"text": "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5419.mp3"},
        {"text": "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5420.mp3"}
    ]
    return fallback_ayahs, "سورة الكوثر", "الشيخ مشاري العفاسي", True

def generate_video():
    ayahs, surah_name, reciter_name, is_full = get_precise_quran_data()
    font_path = download_arabic_font()
    
    video_clips_pool = []
    temp_files_to_delete = []
    
    print(f"جاري معالجة ومزامنة الآيات لـ {surah_name} بصوت {reciter_name}...")
    
    fps = 10
    
    for idx, ayah in enumerate(ayahs):
        text = ayah['text']
        # تنظيف البسملة الملتصقة في بداية السور لكي لا تخرب التنسيق
        if idx == 0 and text.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") and len(text) > 40:
            text = text.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
            
        audio_url = ayah['audio']
        temp_audio_name = f"precise_ayah_{idx}.mp3"
        
        # تحميل الملف الصوتي المستقل للآية الحالية
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(audio_url, timeout=15, headers=headers, verify=False)
        with open(temp_audio_name, "wb") as f:
            f.write(r.content)
        temp_files_to_delete.append(temp_audio_name)
        
        # فتح ملف الصوت لحساب الطول الفعلي الدقيق للآية الحالية بالثانية
        audio_clip = AudioFileClip(temp_audio_name)
        duration = audio_clip.duration
        
        # توليد فريمات مخصصة لهذه الآية بناءً على طول صوتها الحقيقي والظهور بدون تداخل
        num_frames = int(duration * fps)
        frames = [create_text_image(text, font_path) for _ in range(num_frames)]
        
        # دمج الصوت والصورة للآية الواحدة ككليب مستقل تماماً ومحكم المزامنة
        sub_video_clip = ImageSequenceClip(frames, fps=fps)
        sub_video_clip = sub_video_clip.set_audio(audio_clip)
        
        video_clips_pool.append(sub_video_clip)
        
    if not video_clips_pool:
        print("خطأ: لم يتم تحميل كليبات صالحة.")
        return
        
    print("جاري ربط الكليبات الفردية بسلسلة متصلة لا تقبل التداخل...")
    # ربط الكليبات المستقلة تلو الأخرى برمجياً وبشكل تتابعي تام
    final_video_clip = concatenate_videoclips(video_clips_pool, method="compose")
    
    output_filename = "quran_chroma.mp4"
    final_video_clip.write_videofile(
        output_filename,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    # تحرير وإغلاق كافة قنوات الذاكرة لمنع تعليق النظام (Exit code 1)
    final_video_clip.close()
    for clip in video_clips_pool:
        clip.close()
        
    # إرسال النتيجة إلى تيليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    type_text = "سورة كاملة بالاتساق الفعلي" if is_full else "٦ آيات متزامنة بالملي ثانية بدون تداخل"
    caption_text = (
        f"📖 {surah_name} ({type_text})\n"
        f"🎙️ بصوت {reciter_name}\n"
        f"✨ كروما سوداء بمزامنة صوتية حقيقية ومطلقة للآيات\n\n"
        f"بواسطة المطور: {YOUR_NAME}"
    )
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url,
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
            files={'video': video_file}
        )
        
    # حذف وتنظيف آمن لجميع الملفات المؤقتة والخطوط
    temp_files_to_delete.append(output_filename)
    temp_files_to_delete.append(font_path)
    
    for file in temp_files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"تخطي حذف الملف {file}: {e}")
            
    if response.status_code == 200:
        print("====================================")
        print(f"تمت المزامنة المطلقة ونشر مقطع {surah_name} بنجاح! ✅")
        print("====================================")
    else:
        print(f"فشل إرسال المقطع لتيليجرام، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
