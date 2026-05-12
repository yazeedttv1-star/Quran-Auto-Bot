import os
import random
import requests
import time # ضروري للفاصل الزمني
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MIN_DURATION = 15 

def get_quran_audio_list():
    combined_audio_path = "final_audio.mp3"
    clips = []
    total_duration = 0
    print("جاري تجميع آيات...")
    while total_duration < MIN_DURATION:
        surah = str(random.randint(1, 114)).zfill(3)
        ayah = str(random.randint(1, 15)).zfill(3) # وسعنا نطاق الآيات شوية
        url = f"https://everyayah.com/data/Alafasy_128kbps/{surah}{ayah}.mp3"
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"temp_{total_duration}.mp3"
            with open(temp_name, "wb") as f: f.write(r.content)
            clip = AudioFileClip(temp_name)
            clips.append(clip)
            total_duration += clip.duration
        else: continue
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(combined_audio_path)
    return combined_audio_path, total_duration

def get_pexels_video():
    headers = {'Authorization': PEXELS_API_KEY}
    topics = ['nature', 'mountains', 'sea', 'galaxy', 'forest', 'rain']
    params = {'query': random.choice(topics), 'per_page': 1, 'page': random.randint(1, 200)}
    res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    return res['videos'][0]['video_files'][0]['link']

def make_video(index):
    print(f"\n--- جاري إنشاء الفيديو رقم {index} ---")
    audio_path, duration = get_quran_audio_list()
    video_url = get_pexels_video()
    
    with open("temp_v.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    audio_clip = AudioFileClip(audio_path)
    full_video = VideoFileClip("temp_v.mp4")
    
    # تكرار الفيديو لو قصير
    if full_video.duration < duration:
        video_clip = full_video.loop(duration=duration)
    else:
        video_clip = full_video.subclip(0, duration)

    final_clip = video_clip.set_audio(audio_clip)
    output_file = f"quran_video_{index}.mp4"
    
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24, bitrate="2500k", threads=4)
    
    audio_clip.close()
    full_video.close()
    return output_file

def send_to_telegram(file_path, index):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(file_path, "rb") as video:
        requests.post(url, files={"video": video}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"فيديو رقم {index} جاهز للنشر! ✅"})

# الدالة الأساسية لتشغيل الحلقة
if __name__ == "__main__":
    for i in range(1, 4): # هيعمل 3 فيديوهات
        try:
            video_file = make_video(i)
            send_to_telegram(video_file, i)
            
            # تنظيف الملفات لعدم ملء المساحة
            if os.path.exists(video_file): os.remove(video_file)
            
            if i < 3: # لو مش آخر فيديو، استنى 5 دقائق
                print(f"تم إرسال الفيديو {i}.. انتظار 5 دقائق قبل الفيديو القادم...")
                time.sleep(300) # 300 ثانية = 5 دقائق
        except Exception as e:
            print(f"خطأ في الدورة {i}: {e}")
