import os
import random
import requests
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, vfx

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MIN_DURATION = 30  # المدة المطلوبة 30 ثانية

def get_fast_quran_audio():
    """جلب آيات مرتبة بصوت شيوخ أسرع (الدوسري أو القطامي)"""
    combined_audio_path = "final_audio.mp3"
    clips = []
    total_duration = 0
    
    # قائمة القراء (الدوسري: Yasser_Ad-Dussary، القطامي: Nasser_Alqatami)
    reciters = ["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"]
    chosen_reciter = random.choice(reciters)
    
    surah_num = random.randint(1, 114)
    surah_str = str(surah_num).zfill(3)
    start_ayah = random.randint(1, 5) 
    
    print(f"جاري جلب تلاوة سريعة من سورة {surah_num} بصوت {chosen_reciter.split('_')[0]}...")
    
    current_ayah = start_ayah
    while total_duration < MIN_DURATION:
        ayah_str = str(current_ayah).zfill(3)
        url = f"https://everyayah.com/data/{chosen_reciter}/{surah_str}{ayah_str}.mp3"
        
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"temp_{current_ayah}.mp3"
            with open(temp_name, "wb") as f: f.write(r.content)
            clip = AudioFileClip(temp_name)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1
        else: break
            
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(combined_audio_path)
    return combined_audio_path, total_duration

def get_high_quality_video():
    """جلب فيديو طبيعي Portrait بجودة عالية جداً"""
    headers = {'Authorization': PEXELS_API_KEY}
    queries = ['dark nature', 'aerial clouds', 'starry night', 'deep forest', 'dramatic ocean']
    params = {
        'query': random.choice(queries),
        'per_page': 1,
        'page': random.randint(1, 150),
        'orientation': 'portrait',
        'size': 'large'
    }
    res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    return res['videos'][0]['video_files'][0]['link']

def make_pro_video(index):
    audio_path, duration = get_fast_quran_audio()
    video_url = get_high_quality_video()
    
    print(f"جاري مونتاج الفيديو رقم {index}...")
    with open("temp_v.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    audio_clip = AudioFileClip(audio_path)
    # إضافة تأثير Fade Out خفيف للصوت في النهاية
    audio_clip = audio_clip.audio_fadeout(2)
    
    full_video = VideoFileClip("temp_v.mp4")
    
    # ضبط طول الفيديو مع تكرار ناعم لو قصير
    if full_video.duration < duration:
        video_clip = full_video.loop(duration=duration)
    else:
        video_clip = full_video.subclip(0, duration)

    # تحسينات المونتاج: إضافة Fade in/out للفيديو
    final_clip = video_clip.fadein(1).fadeout(1).set_audio(audio_clip)
    
    output_file = f"pro_quran_{index}.mp4"
    
    # إعدادات تصدير احترافية (High Profile)
    final_clip.write_videofile(
        output_file, 
        codec="libx264", 
        audio_codec="aac", 
        fps=30, # زيادة عدد الفريمات لنعومة الحركة
        bitrate="5000k", # جودة صورة أعلى
        preset="slow", # معالجة أعمق لجودة الفيديو
        threads=4
    )
    
    audio_clip.close()
    full_video.close()
    return output_file

def send_to_telegram(file_path, index):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption = f"🎥 فيديو احترافي رقم {index} (30 ثانية)\n✨ تلاوة حاشعة وسريعة\n📍 جاهز للنشر على TikTok/Reels"
    with open(file_path, "rb") as v:
        requests.post(url, files={"video": v}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption})

if __name__ == "__main__":
    for i in range(1, 4):
        try:
            video_file = make_pro_video(i)
            send_to_telegram(video_file, i)
            if os.path.exists(video_file): os.remove(video_file)
            
            if i < 3:
                print("استراحة 5 دقائق قبل إنتاج الفيديو التالي...")
                time.sleep(300)
        except Exception as e:
            print(f"حدث خطأ: {e}")
