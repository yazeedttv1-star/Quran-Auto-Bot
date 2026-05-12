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

def get_clean_audio(index):
    """جلب آيات مرتبة ومعالجتها لمنع التقطيع تماماً"""
    clips = []
    total_duration = 0
    # اختيار عشوائي للقراء ذوي الرتم السريع
    reciter = random.choice(["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"])
    
    surah_num = random.randint(1, 114)
    surah_str = str(surah_num).zfill(3)
    current_ayah = random.randint(1, 10) # نقطة بداية عشوائية
    
    print(f"جاري تحضير صوت الفيديو {index}...")
    
    while total_duration < MIN_DURATION:
        url = f"https://everyayah.com/data/{reciter}/{surah_str}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            temp_name = f"v{index}_a{current_ayah}.mp3"
            with open(temp_name, "wb") as f: f.write(r.content)
            
            # تحميل المقطع ومعالجته
            # fadein/out بمقدار بسيط بيمنع التقطيع المفاجئ بين الآيات
            clip = AudioFileClip(temp_name).set_fps(44100).audio_fadein(0.1).audio_fadeout(0.1)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1
        else: break

    # دمج الأصوات
    # استخدام method='compose' لضمان استقرار الترددات
    final_audio = concatenate_audioclips(clips)
    audio_file = f"final_audio_{index}.mp3"
    final_audio.write_audiofile(audio_file, fps=44100, bitrate="192k", verbose=False, logger=None)
    
    # تنظيف الكليبات الصغيرة من الرام
    for c in clips: c.close()
    
    return audio_file, total_duration

def make_video(index):
    # 1. تجهيز الصوت النظيف أولاً
    audio_path, duration = get_clean_audio(index)
    
    # 2. جلب الفيديو (Portrait)
    headers = {'Authorization': PEXELS_API_KEY}
    topics = ['nature', 'forest', 'rain', 'galaxy', 'landscape']
    params = {'query': random.choice(topics), 'per_page': 1, 'page': random.randint(1, 200), 'orientation': 'portrait'}
    v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    video_url = v_data['videos'][0]['video_files'][0]['link']
    
    video_temp = f"temp_v_{index}.mp4"
    with open(video_temp, "wb") as f: f.write(requests.get(video_url).content)
    
    # 3. المونتاج
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip(video_temp)
    
    # تكرار الفيديو لو قصير عن 30 ثانية
    if video_clip.duration < duration:
        video_clip = video_clip.loop(duration=duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    # دمج وتنعيم البداية والنهاية
    final = video_clip.set_audio(audio_clip).fadein(1).fadeout(1)
    
    output = f"quran_final_{index}.mp4"
    final.write_videofile(output, codec="libx264", audio_codec="aac", fps=24, bitrate="3500k", threads=4, logger=None)
    
    # إغلاق الملفات لتحرير السيرفر
    audio_clip.close()
    video_clip.close()
    
    return output

if __name__ == "__main__":
    for i in range(1, 4):
        try:
            video_file = make_video(i)
            
            # إرسال لتليجرام
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
            with open(video_file, "rb") as v:
                requests.post(url, files={"video": v}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"فيديو احترافي رقم {i} 🎥\n#قرآن #تلاوة #اسلام"})
            
            # مسح الملفات فوراً لتوفير مساحة السيرفر
            for f in os.listdir():
                if f.endswith(".mp4") or f.endswith(".mp3"):
                    if f.startswith("quran_final"): continue # سيبه عشان ميمسحش الفيديو قبل ما يترفع
                    os.remove(f)
            os.remove(video_file)

            if i < 3:
                print(f"تم الفيديو {i}.. انتظار 5 دقائق للفيديو القادم...")
                time.sleep(300)
        except Exception as e:
            print(f"خطأ في الفيديو {i}: {e}")
