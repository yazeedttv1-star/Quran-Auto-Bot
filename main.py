import os
import random
import requests
import time
from moviepy.editor import AudioFileClip, ColorClip

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def get_quran_audio():
    """جلب تلاوة عشوائية سريعة وخفيفة لضمان عمل البوت فوراً"""
    surah_num = random.randint(100, 114) # اختيار سور قصيرة جداً لضمان السرعة
    surah_str = str(surah_num).zfill(3)
    
    url = f"https://server12.mp3quran.net/maher/{surah_str}.mp3"
    audio_path = "temp_surah.mp3"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, timeout=20, headers=headers, verify=False)
    if r.status_code == 200:
        with open(audio_path, "wb") as f:
            f.write(r.content)
    else:
        raise Exception("فشل تحميل الصوت")
        
    return audio_path

def generate_video():
    # 1. تحميل الصوت
    audio_path = get_quran_audio()
    audio_clip = AudioFileClip(audio_path)
    duration = min(audio_clip.duration, 15) # تحديد المدة بـ 15 ثانية كحد أقصى للسرعة
    
    # 2. إنشاء خلفية سوداء بسيطة جداً
    final_clip = ColorClip(size=(720, 1280), color=(0, 0, 0), duration=duration)
    final_clip = final_clip.set_audio(audio_clip.subclip(0, duration))
    
    output_filename = "quran_chroma.mp4"
    
    # كتابة الفيديو بأقل إعدادات لضمان السرعة الاستثنائية
    final_clip.write_videofile(
        output_filename, 
        fps=10, 
        codec="libx264", 
        audio_codec="aac", 
        logger=None
    )
    
    final_clip.close()
    audio_clip.close()
    
    # 3. إرسال الفيديو فوراً لتليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = f"✨ تلاوة خاشعة قصيرة (كروما سوداء) | خادمكم: {YOUR_NAME}"
        response = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}, files={'video': video_file})
        
    # تنظيف الملفات المؤقتة
    for file in [audio_path, output_filename]:
        if os.path.exists(file): 
            os.remove(file)
            
    # الجملة المريحة اللي طلبتها عشان تظهر لك في الـ Logs مباشرة وتفرح بالنجاح
    if response.status_code == 200:
        print("====================================")
        print("تم الارسال بنجاح ✅")
        print("================
