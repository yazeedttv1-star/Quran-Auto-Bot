import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import arabic_reshaper
from bidi.algorithm import get_display

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def fix_arabic_text(text):
    try:
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def get_quran_data():
    reciters = [
        {"name": "الشيخ ياسر الدوسري", "url": "https://server11.mp3quran.net/yasser/"},
        {"name": "الشيخ ناصر القطامي", "url": "https://server11.mp3quran.net/qtm/"},
        {"name": "الشيخ ماهر المعيقلي", "url": "https://server12.mp3quran.net/maher/"}
    ]
    chosen = random.choice(reciters)
    reciter_name = chosen["name"]
    base_url = chosen["url"]
    
    surah_num = random.randint(70, 114)
    surah_str = str(surah_num).zfill(3)
    audio_url = f"{base_url}{surah_str}.mp3"
    
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
        ayahs_data = meta_res['data']['ayahs']
    except:
        surah_name = "سورة من القرآن"
        ayahs_data = []

    audio_path = "temp_surah.mp3"
    r = requests.get(audio_url, timeout=20, verify=False)
    if r.status_code == 200:
        with open(audio_path, "wb") as f:
            f.write(r.content)
    else:
        raise Exception("فشل تحميل الصوت")

    full_audio = AudioFileClip(audio_path).set_fps(44100)
    total_len = full_audio.duration
    
    start_time = random.uniform(0, max(0, total_len - 22))
    end_time = min(start_time + random.uniform(15, 20), total_len)
    
    final_audio_path = "final.mp3"
    sub_audio = full_audio.subclip(start_time, end_time).audio_fadein(0.5).audio_fadeout(0.5)
    sub_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    duration = sub_audio.duration
    full_audio.close()
    sub_audio.close()
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    ayahs_timeline = []
    if ayahs_data:
        num_ayahs = min(3, len(ayahs_data))
        selected_ayahs = random.sample(ayahs_data, num_ayahs)
        selected_ayahs.sort(key=lambda x: x['numberInSurah'])
        
        step = duration / num_ayahs
        for i, ayah in enumerate(selected_ayahs):
            ayahs_timeline.append({
                'text': f" ﴿ {ayah['text']} ﴾ ",
                'start': i * step,
                'end': (i + 1) * step
            })
            
    info_text = f"🎙️ {reciter_name}  |  📖 {surah_name}"
    return final_audio_path, duration, ayahs_timeline, info_text, reciter_name, surah_name

def process_video_frame(frame, t, ayahs_timeline, info_text, hook_text, cta_text):
    """تعديل الفريم بشكل لحظي بناءً على الوقت الحالي (t) لعرض آية تلو الأخرى بدقة متناهية"""
    # تحويل الفريم العادي لصورة بيلو القياسية والأكثر أماناً بنسبة 100%
    img = Image.fromarray(frame.astype('uint8')).
