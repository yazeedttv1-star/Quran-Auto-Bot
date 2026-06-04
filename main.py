import os
import random
import requests
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, TextClip, CompositeVideoClip

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"
MIN_DURATION = 30 

def get_quran_with_keywords():
    """جلب آيات مرتبة واستخراج كلمات مفتاحية للخلفية"""
    clips = []
    total_duration = 0
    reciter = random.choice(["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"])
    surah_num = random.randint(1, 114)
    current_ayah = random.randint(1, 15)
    
    # الكلمات المفتاحية التي حددتها أنت فقط
    search_keywords = ['mountains', 'river', 'nature']
    
    while total_duration < MIN_DURATION:
        url = f"https://everyayah.com/data/{reciter}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"a_{current_ayah}.mp3"
            with open(temp_name, "wb") as f: f.write(r.content)
            clip = AudioFileClip(temp_name).set_fps(44100).audio_fadein(0.1).audio_fadeout(0.1)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1
        else: break
            
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile("final.mp3", fps=44100, bitrate="192k", logger=None)
    return "final.mp3", total_duration, random.choice(search_keywords)

def make_pro_video_for_yazeed(index):
    audio_path, duration, keyword = get_quran_with_keywords()
    
    # جلب فيديو 4K بناءً على الكلمة المفتاحية
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': keyword, 'per_page': 1, 'page': random.randint(1, 100), 'orientation': 'portrait', 'size': 'large'}
    v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    video_url = v_data['videos'][0]['video_files'][0]['link']
    
    with open("v_temp.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    video_clip = VideoFileClip("v_temp.mp4")
    if video_clip.duration < duration:
        video_clip = video_clip.loop(duration=duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    # دمج الصوت مع الفيديو أولاً
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)

    # إضافة اسم "yazeed" في الأسفل بطريقة متوافقة مع السيرفر الافتراضي
    final_clip = video_clip
    try:
        # تم إزالة الشروط المعقدة واستخدام طريقة الـ Caption الأساسية المدعومة في نظام التشغيل مباشرة
        txt_clip = TextClip(YOUR_NAME, fontsize=40, color='white', font='Liberation-Sans', method='caption', size=(video_clip.w, 100))
        txt_clip = txt_clip.set_position(('center', video_clip.h - 150)).set_duration(duration).set_opacity(0.6)
        final_clip = CompositeVideoClip([video_clip, txt_clip])
    except Exception as e:
        print(f"تنبيه: تم إرسال الفيديو بدون نص بسبب قيود السيرفر. الخطأ: {e}")

    # تصدير وإرسال الفيديو
    output_filename = "quran_daily.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    # دالة الإرسال مدمجة تلقائياً لتوصيل الفيديو لهاتفك
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"فيديو قرآني خاشع 🌸\n✨ مبرمج بواسطة {YOUR_NAME}"}
        files = {'video': video_file}
        requests.post(url, data=payload, files=files)

    # تنظيف السيرفر
    final_clip.close()
    video_clip.close()
    audio_clip.close()
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): os.remove(file)

if __name__ == "__main__":
    make_pro
