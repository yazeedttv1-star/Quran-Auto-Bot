import os
import requests
from moviepy.editor import AudioFileClip, ColorClip, TextClip, CompositeVideoClip

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def get_quran_audio():
    # نختار سورة الكوثر (108) لتسهيل مزامنة الكلمات بدقة مع الصوت
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

def generate_video():
    audio_path = get_quran_audio()
    if not audio_path:
        print("تعذر تحميل الصوت.")
        return

    audio_clip = AudioFileClip(audio_path)
    
    # تحديد المدة بحد أقصى 30 ثانية أو طول الملف الصوتي أيهما أقل
    duration = min(audio_clip.duration, 30) 
    
    # 1. إنشاء الخلفية السوداء (720x1280)
    background = ColorClip(size=(720, 1280), color=(0, 0, 0), duration=duration)
    
    # 2. إعداد النصوص وتوقيت ظهورها (مزامنة تقريبية لسورة الكوثر بصوت الشيخ ماهر)
    # يمكنك تعديل النصوص والتوقيت (البداية والنهاية بالثواني) حسب الرغبة
    subtitles = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "start": 0, "end": 4},
        {"text": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "start": 4, "end": 8},
        {"text": "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "start": 8, "end": 12},
        {"text": "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ", "start": 12, "end": 17}
    ]
    
    clips = [background]
    
    # 3. دمج النصوص فوق الخلفية
    for sub in subtitles:
        if sub["start"] < duration:
            end_time = min(sub["end"], duration)
            # إنشاء كليب النص
            # ملاحظة: قد تحتاج إلى تثبيت برنامج ImageMagick على جهازك لكي تعمل TextClip بنجاح
            txt_clip = (TextClip(sub["text"], fontsize=40, color='white', font='Arial-Bold')
                        .set_position('center')
                        .set_start(sub["start"])
                        .set_duration(end_time - sub["start"]))
            clips.append(txt_clip)
            
    # دمج كليب الخلفية والنصوص معاً
    final_clip = CompositeVideoClip(clips)
    final_clip = final_clip.set_audio(audio_clip.subclip(0, duration))
    
    output_filename = "quran_chroma.mp4"
    
    # كتابة الفيديو النهائي بجودة ممتازة
    final_clip.write_videofile(
        output_filename, 
        fps=24, # تم رفع الفريمات لـ 24 ليكون النص سلساً غير متقطع
        codec="libx264", 
        audio_codec="aac", 
        logger=None
    )
    
    # إغلاق الملفات لتحرير الذاكرة
    final_clip.close()
    audio_clip.close()
    
    # 4. الإرسال إلى تيليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption_text = f"✨ تلاوة خاشعة مكتوبة (كروما سوداء) | خادمكم: {YOUR_NAME}"
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url, 
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}, 
            files={'video': video_file}
        )
        
    # تنظيف الملفات المؤقتة
    for file in [audio_path, output_filename]:
        if os.path.exists(file): 
            os.remove(file)
            
    if response.status_code == 200:
        print("====================================")
        print("تم التصميم والإرسال بنجاح ✅")
        print("====================================")
    else:
        print(f"فشل الإرسال، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
