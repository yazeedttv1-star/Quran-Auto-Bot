import os
import random
import requests
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MIN_DURATION = 30 

def get_clean_audio():
    """جلب آيات مرتبة ومعالجة الصوت ليكون نقياً وبدون تقطيع"""
    clips = []
    total_duration = 0
    reciters = ["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"]
    chosen_reciter = random.choice(reciters)
    
    surah_num = random.randint(1, 114)
    surah_str = str(surah_num).zfill(3)
    current_ayah = random.randint(1, 5) 
    
    print(f"جاري تحضير صوت نقي للسورة {surah_num}...")
    
    while total_duration < MIN_DURATION:
        url = f"https://everyayah.com/data/{chosen_reciter}/{surah_str}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"ayah_{current_ayah}.mp3"
            with open(temp_name, "wb") as f: f.write(r.content)
            
            # تحميل المقطع وضبط جودته (44100Hz) لمنع التقطيع
            clip = AudioFileClip(temp_name).set_fps(44100)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1
        else: break

    # دمج الأصوات مع عمل Crossfade (تداخل بسيط) لمنع "الفجوات" بين الآيات
    # padding=-0.1 بيخلي الآيات تدخل في بعضها بمقدار جزء من الثانية عشان الصوت يبقى متصل
    final_audio = concatenate_audioclips(clips)
    
    final_audio_path = "final_clean_audio.mp3"
    # تصدير الصوت بجودة عالية جداً
    final_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k")
    return final_audio_path, total_duration

def make_video(index):
    audio_path, duration = get_clean_audio()
    
    # جلب الفيديو (نفس الدالة السابقة مع Portrait)
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': 'nature', 'per_page': 1, 'page': random.randint(1, 150), 'orientation': 'portrait'}
    video_url = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()['videos'][0]['video_files'][0]['link']
    
    with open("temp_v.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip("temp_v.mp4")
    
    # تكرار الفيديو لو قصير (Loop)
    if video_clip.duration < duration:
        video_clip = video_clip.loop(duration=duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    final = video_clip.set_audio(audio_clip).fadein(1).fadeout(1)
    
    output = f"video_{index}.mp4"
    final.write_videofile(output, codec="libx264", audio_codec="aac", fps=30, bitrate="4000k", threads=4)
    
    return output

if __name__ == "__main__":
    for i in range(1, 4):
        try:
            video_file = make_video(i)
            # إرسال لتليجرام
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
            with open(video_file, "rb") as v:
                requests.post(url, files={"video": v}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"فيديو رقم {i} بجودة عالية ⚡"})
            
            # تنظيف ومسح الملفات لعدم ضغط السيرفر
            os.remove(video_file)
            
            if i < 3:
                print("انتظار 5 دقائق...")
                time.sleep(300)
        except Exception as e:
            print(f"Error: {e}")
