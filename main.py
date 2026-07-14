import os
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def get_quran_audio():
    surah_url = "https://server12.mp3quran.net/maher/108.mp3"
    audio_path = "temp_surah.mp3"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(surah_url, timeout=20, headers=headers, verify=False)
        if r.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(r.content)
            return audio_path
    except Exception as e:
        print(f"خطأ في تحميل الصوت: {e}")
        return None

def download_arabic_font():
    """تحميل خط عربي مجاني ومضمون من جوجل لتفادي عدم وجود خطوط على السيرفر أو التابلت"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        print("جاري تحميل الخط العربي لضمان سلامة النص...")
        try:
            r = requests.get(font_url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"فشل تحميل الخط، سيتم استخدام الخط الافتراضي: {e}")
    return font_path

def create_text_image(text, font_path, width=720, height=1280):
    """توليد صورة سوداء وعليها النص العربي في المنتصف بدقة عالية"""
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # استخدام الخط العربي الذي تم تحميله
    try:
        font = ImageFont.truetype(font_path, 55)
    except Exception:
        font = ImageFont.load_default()
        
    # حساب أبعاد النص لتوسيطه
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # رسم النص باللون الأبيض
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return np.array(img)

def generate_video():
    audio_path = get_quran_audio()
    if not audio_path:
        print("تعذر تحميل الصوت.")
        return

    # تحميل الخط العربي قبل البدء
    font_path = download_arabic_font()

    audio_clip = AudioFileClip(audio_path)
    duration = int(min(audio_clip.duration, 30)) # مدة الفيديو 30 ثانية كحد أقصى
    fps = 10 
    total_frames = duration * fps
    
    # توقيت الآيات (بالفريمات)
    subtitles = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "start_f": 0 * fps, "end_f": 4 * fps},
        {"text": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "start_f": 4 * fps, "end_f": 8 * fps},
        {"text": "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "start_f": 8 * fps, "end_f": 12 * fps},
        {"text": "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ", "start_f": 12 * fps, "end_f": 17 * fps}
    ]
    
    frames = []
    print("جاري إنشاء فريمات الفيديو...")
    
    for frame_idx in range(total_frames):
        current_text = ""
        for sub in subtitles:
            if sub["start_f"] <= frame_idx < sub["end_f"]:
                current_text = sub["text"]
                break
        
        frame_img = create_text_image(current_text, font_path)
        frames.append(frame_img)
        
    # دمج الفريمات كفيديو
    video_clip = ImageSequenceClip(frames, fps=fps)
    video_clip = video_clip.set_audio(audio_clip.subclip(0, duration))
    
    output_filename = "quran_chroma.mp4"
    
    # إنتاج الملف النهائي
    video_clip.write_videofile(
        output_filename, 
        fps=fps, 
        codec="libx264", 
        audio_codec="aac", 
        logger=None
    )
    
    video_clip.close()
    audio_clip.close()
    
    # الإرسال لتيليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption_text = f"✨ تلاوة خاشعة مكتوبة (كروما سوداء) | خادمكم: {YOUR_NAME}"
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url, 
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}, 
            files={'video': video_file}
        )
        
    # تنظيف الملفات الموقتة والخطوط بعد الرفع
    cleanup_files = [audio_path, output_filename, font_path]
    for file in cleanup_files:
        if os.path.exists(file): 
            os.remove(file)
            
    if response.status_code == 200:
        print("====================================")
        print("تم التصميم والرفع بنجاح ومن GitHub ✅")
        print("====================================")
    else:
        print(f"فشل الإرسال، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
