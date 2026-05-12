import os
import random
import requests
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# الإعدادات من Secrets
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MIN_DURATION = 15 

def get_ordered_quran_audio():
    """جلب آيات مرتبة من سورة واحدة لضمان تواصل المعنى"""
    combined_audio_path = "final_audio.mp3"
    clips = []
    total_duration = 0
    
    # 1. اختيار سورة عشوائية
    surah_num = random.randint(1, 114)
    surah_str = str(surah_num).zfill(3)
    
    # 2. اختيار آية بداية عشوائية (بافتراض أن معظم السور فيها على الأقل 5-10 آيات)
    # للسور القصيرة جداً سنبدأ من الآية 1
    start_ayah = random.randint(1, 3) 
    
    print(f"جاري تجميع آيات مرتبة من السورة رقم {surah_num}...")
    
    current_ayah = start_ayah
    while total_duration < MIN_DURATION:
        ayah_str = str(current_ayah).zfill(3)
        url = f"https://everyayah.com/data/Alafasy_128kbps/{surah_str}{ayah_str}.mp3"
        
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"temp_{surah_str}_{ayah_str}.mp3"
            with open(temp_name, "wb") as f:
                f.write(r.content)
            clip = AudioFileClip(temp_name)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1 # الانتقال للآية التالية في نفس السورة
        else:
            # لو السورة خلصت قبل ما نوصل لـ 15 ثانية
            break
            
    if not clips: # احتياطي لو حصل مشكلة
        return None, 0

    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(combined_audio_path)
    return combined_audio_path, total_duration

def get_nature_video():
    """سحب فيديوهات طبيعية فقط بجودة عالية"""
    headers = {'Authorization': PEXELS_API_KEY}
    # كلمات بحث محددة للمناظر الطبيعية
    query = random.choice(['scenic nature', 'beautiful landscape', 'relaxing waterfall', 'mountain view', 'ocean waves'])
    params = {'query': query, 'per_page': 1, 'page': random.randint(1, 100), 'orientation': 'portrait'} # portrait عشان تيك توك
    
    try:
        res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
        return res['videos'][0]['video_files'][0]['link']
    except:
        # فيديو احتياطي لو الـ API علق
        return "https://player.vimeo.com/external/370331493.sd.mp4?s=330fb15e763f03ac6790937667d4e16d4e2a865a&profile_id=164&oauth2_token_id=57447761"

def make_video(index):
    audio_path, duration = get_ordered_quran_audio()
    if not audio_path: return None
    
    video_url = get_nature_video()
    
    print(f"جاري تجهيز الفيديو {index}...")
    with open("temp_v.mp4", "wb") as f:
        f.write(requests.get(video_url).content)
    
    audio_clip = AudioFileClip(audio_path)
    full_video = VideoFileClip("temp_v.mp4")
    
    # ضبط الفيديو على طول الصوت
    if full_video.duration < duration:
        video_clip = full_video.loop(duration=duration)
    else:
        video_clip = full_video.subclip(0, duration)

    final_clip = video_clip.set_audio(audio_clip)
    output_file = f"final_quran_{index}.mp4"
    
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24, bitrate="3000k")
    
    audio_clip.close()
    full_video.close()
    return output_file

def send_to_telegram(file_path, index):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption = f"فيديو قرآني مرتب رقم {index} ✨\n\n#قرآن #اسلام #راحة_نفسية"
    with open(file_path, "rb") as v:
        requests.post(url, files={"video": v}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption})

if __name__ == "__main__":
    for i in range(1, 4):
        try:
            video_file = make_video(i)
            if video_file:
                send_to_telegram(video_file, i)
                os.remove(video_file) # مسح الملف لتوفير مساحة
            
            if i < 3:
                print("انتظار 5 دقائق للبدء في الفيديو التالي...")
                time.sleep(300)
        except Exception as e:
            print(f"خطأ: {e}")
