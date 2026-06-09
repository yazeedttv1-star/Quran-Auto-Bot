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
    # اختيار سور قصيرة جداً لضمان سرعة التحميل والتشغيل
    surah_num = random.randint(108, 114) 
    surah_str = str(surah_num).zfill(3)
    
    url = f"https://server12.mp3quran.net/maher/{surah_str}.mp3"
    audio_path = "temp_surah.mp3"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, timeout=20, headers=headers, verify=False)
        if r.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(r.content)
            return audio_path
    except:
        pass
        
    # خط دفاع احتياطي لو السيرفر الرئيسي علق
    emergency_url = "https://server12.mp3quran.net/maher/108.mp3"
    r = requests.get(emergency_url, timeout=20, verify=False)
    with open(audio_path, "wb") as f:
        f.write(r.content)
    return audio_path

def generate_video():
    audio_path = get_quran_audio()
    audio_clip = AudioFileClip(audio_path)
    duration = min(audio_clip.duration, 15) 
    
    final_clip = ColorClip(size=(720, 1280), color=(0, 0, 0), duration=duration)
    final_clip = final_clip.set_audio(audio_clip.subclip(0, duration))
    
    output_filename = "quran_chroma.mp4"
    
    final_clip.write_videofile(
        output_filename, 
        fps=10, 
        codec="libx264", 
        audio_codec="aac", 
        logger=None
    )
    
    final_clip.close()
    audio_clip.close()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption_text = f"✨ تلاوة خاشعة قصيرة (كروما سوداء) | خادمكم: {YOUR_NAME}"
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url, 
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}, 
            files={'video': video_file}
        )
        
    for file in [audio_path, output_filename]:
        if os.path.exists(file): 
            os.remove(file)
            
    if response.status_code == 200:
        print("====================================")
        print("تم الارسال بنجاح ✅")
        print("====================================")
    else:
        print(f"فشل الإرسال، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
