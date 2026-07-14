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

# قائمة القراء والروابط الخاصة بهم (صوت الآيات المنفصلة التابع لـ Al Quran Cloud)
RECITERS = [
    {"name": "الشيخ مشاري العفاسي", "identifier": "ar.alafasy"},
    {"name": "الشيخ ماهر المعيقلي", "identifier": "ar.mahermuaiqly"},
    {"name": "الشيخ عبد الباسط عبد الصمد", "identifier": "ar.abdulsamad"},
    {"name": "الشيخ عبد الرحمن السديس", "identifier": "ar.as-sudais"},
    {"name": "الشيخ محمود خليل الحصري", "identifier": "ar.husary"},
    {"name": "الشيخ محمد صديق المنشاوي", "identifier": "ar.minshawi"}
]

HISTORY_FILE = "history.txt"

def get_viewed_history():
    """قراءة المقاطع التي تم عرضها سابقاً لمنع التكرار"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_history(entry):
    """حفظ المقطع الحالي في التاريخ لمنع تكراره لاحقاً"""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def download_arabic_font():
    """جلب الخط العربي لضمان سلامة رندرة النصوص على جيت هاب والتابلت"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"تعذر تحميل الخط المخصص: {e}")
    return font_path

def create_text_image(text, font_path, width=720, height=1280):
    """إنشاء فريم أسود بداخله الآية الحالية في المنتصف تماماً وتلقائياً"""
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, 42)
    except Exception:
        font = ImageFont.load_default()
        
    # قياس أبعاد النص وتوسيطه بدقة
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return np.array(img)

def get_quran_data():
    """جلب سورة عشوائية ومعالجة البيانات بناءً على حجمها وحفظ السجل"""
    reciter = random.choice(RECITERS)
    history = get_viewed_history()
    
    # اختيار سورة عشوائية من الـ 114 سورة
    surah_num = random.randint(1, 114)
    
    # جلب بيانات السورة نصاً وصوتاً من الـ API
    api_url = f"https://api.alquran.cloud/v1/surah/{surah_num}/{reciter['identifier']}"
    
    try:
        response = requests.get(api_url, timeout=20)
        if response.status_code == 200:
            data = response.json()['data']
            surah_name = data['name']
            ayahs_data = data['ayahs']
            total_ayahs = len(ayahs_data)
            
            # التحقق مما إذا كانت السورة "قصيرة" أو "طويلة"
            # إذا كان عدد الآيات أقل من 10 أو إجمالي مدتها قصير نعتبرها سورة قصيرة وتعرض كاملة
            if total_ayahs <= 8:
                # تشغيل السورة كاملة
                selected_ayahs = ayahs_data
                history_entry = f"{surah_num}_all"
                if history_entry in history:
                    # إذا تم عرضها بالكامل مسبقاً، نحاول جلب سورة أخرى عبر استدعاء تكراري بسيط
                    return get_quran_data()
                save_to_history(history_entry)
                is_full_surah = True
            else:
                # سورة كبيرة: نقتطع منها 6 آيات متتالية عشوائياً مع تجنب التكرار
                start_index = random.randint(0, total_ayahs - 6)
                selected_ayahs = ayahs_data[start_index : start_index + 6]
                
                history_entry = f"{surah_num}_{start_index}_{start_index+6}"
                if history_entry in history:
                    return get_quran_data()
                save_to_history(history_entry)
                is_full_surah = False
                
            return selected_ayahs, surah_name, reciter['name'], is_full_surah
    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        
    # خط دفاع احتياطي في حال توقف الـ API
    fallback_ayahs = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/1.mp3"},
        {"text": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5418.mp3"},
        {"text": "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5419.mp3"},
        {"text": "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ", "audio": "https://cdn.islamic.network/quran/audio/128/ar.alafasy/5420.mp3"}
    ]
    return fallback_ayahs, "سورة الكوثر", "الشيخ مشاري العفاسي", True

def generate_video():
    # 1. جلب الآيات والبيانات التلقائية
    ayahs, surah_name, reciter_name, is_full_surah = get_quran_data()
    font_path = download_arabic_font()
    
    temp_audio_files = []
    audio_clips = []
    subtitles = []
    current_time = 0.0
    
    print(f"جاري معالجة: {surah_name} بصوت {reciter_name}...")
    
    # 2. تحميل ملفات الصوت الخاصة بكل آية منفصلة ودمجها لحساب الوقت الفعلي بدقة
    for idx, ayah in enumerate(ayahs):
        audio_url = ayah['audio']
        temp_file = f"temp_ayah_{idx}.mp3"
        
        try:
            r = requests.get(audio_url, timeout=15)
            if r.status_code == 200:
                with open(temp_file, "wb") as f:
                    f.write(r.content)
                temp_audio_files.append(temp_file)
                
                # إنشاء كليب صوت للآية وحساب مدتها
                clip = AudioFileClip(temp_file)
                audio_clips.append(clip)
                
                # تسجيل النص وتوقيت البدء والانتهاء الحقيقي للآية
                duration = clip.duration
                text_to_show = ayah['text']
                
                # إزالة البسملة الملتصقة في بداية الآيات إذا لم تكن الفاتحة
                if idx == 0 and text_to_show.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") and len(text_to_show) > 40:
                    text_to_show = text_to_show.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
                
                subtitles.append({
                    "text": text_to_show,
                    "start_s": current_time,
                    "end_s": current_time + duration
                })
                current_time += duration
        except Exception as e:
            print(f"خطأ في تحميل آية: {e}")
            
    if not audio_clips:
        print("تعذر تحميل أي ملفات صوتية.")
        return

    # تحديد طول الفيديو النهائي بناءً على مجموع مدد الصوت للآيات
    total_duration = current_time
    fps = 10
    total_frames = int(total_duration * fps)
    
    frames = []
    print("جاري دمج الفريمات وبناء الفيديو التفاعلي...")
    
    for frame_idx in range(total_frames):
        frame_time = frame_idx / fps
        current_text = ""
        
        # مطابقة الفريم مع الآية المناسبة له صوتياً بدقة تامة
        for sub in subtitles:
            if sub["start_s"] <= frame_time < sub["end_s"]:
                current_text = sub["text"]
                break
                
        frame_img = create_text_image(current_text, font_path)
        frames.append(frame_img)
        
    # 3. تجميع الفيديو النهائي
    video_clip = ImageSequenceClip(frames, fps=fps)
    
    # دمج كليبات الصوت المنفصلة لتكوين تلاوة كاملة مستمرة
    from moviepy.editor import concatenate_audioclips
    final_audio = concatenate_audioclips(audio_clips)
    video_clip = video_clip.set_audio(final_audio)
    
    output_filename = "quran_chroma.mp4"
    video_clip.write_videofile(
        output_filename,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    # إغلاق الكليبات
    video_clip.close()
    final_audio.close()
    for clip in audio_clips:
        clip.close()
        
    # 4. رفع الفيديو النهائي لتيليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    
    type_text = "كاملة" if is_full_surah else "تلاوة مقتطعة (٦ آيات دون تكرار)"
    caption_text = (
        f"📖 {surah_name} ({type_text})\n"
        f"🎙️ بصوت {reciter_name}\n"
        f"✨ كروما سوداء للمونتاج والتصميم بدقة متناهية\n\n"
        f"خادمكم وصاحب المشروع: {YOUR_NAME}"
    )
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url,
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
            files={'video': video_file}
        )
        
    # 5. تنظيف مجلد العمل وحذف الملفات المؤقتة
    for file in temp_audio_files:
        if os.path.exists(file):
            os.remove(file)
            
    cleanup_files = [output_filename, font_path]
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            
    if response.status_code == 200:
        print("====================================")
        print(f"تم تصميم فيديو {surah_name} بنجاح وإرساله دون أي تكرار! ✅")
        print("====================================")
    else:
        print(f"خطأ في الإرسال لتيليجرام: {response.status_code}")

if __name__ == "__main__":
    generate_video()
