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
HISTORY_FILE = "used_videos.txt" # ملف لحفظ الفيديوهات المستخدمة لمنع التكرار

def load_used_videos():
    """تحميل روابط الفيديوهات التي تم استخدامها سابقاً"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_used_video(video_url):
    """حفظ رابط الفيديو الجديد في ملف التاريخ"""
    with open(HISTORY_FILE, "a") as f:
        f.write(video_url + "\n")

def get_quran_with_keywords():
    """جلب آيات مرتبة وتحديد نوع الخلفيات المطلوبة"""
    clips = []
    temp_files = []
    total_duration = 0
    reciter = random.choice(["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"])
    surah_num = random.randint(1, 114)
    current_ayah = random.randint(1, 15)
    
    # كلمات بحث مخصصة لأجمل مناظر الطبيعة والجبال والأنهار والسماء بطابع سينمائي
    search_keywords = [
        'aesthetic nature', 'cinematic mountains', 'beautiful river', 
        'epic sky', 'misty forest', 'scenic landscape', 'peaceful water'
    ]
    
    print(f"جاري اختيار السورة: {surah_num} والقارئ: {reciter}")
    
    while total_duration < MIN_DURATION:
        url = f"https://everyayah.com/data/{reciter}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(url)
        if r.status_code == 200:
            temp_name = f"a_{current_ayah}.mp3"
            with open(temp_name, "wb") as f: 
                f.write(r.content)
            temp_files.append(temp_name)
            
            clip = AudioFileClip(temp_name).set_fps(44100).audio_fadein(0.1).audio_fadeout(0.1)
            clips.append(clip)
            total_duration += clip.duration
            current_ayah += 1
        else: 
            break
            
    if not clips:
        raise Exception("فشل في تحميل آيات القرآن.")

    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile("final.mp3", fps=44100, bitrate="192k", logger=None)
    
    final_audio.close()
    for c in clips: c.close()
    for f in temp_files:
        if os.path.exists(f): os.remove(f)
        
    return "final.mp3", total_duration, random.choice(search_keywords)


def send_video_to_telegram(video_path):
    """إرسال الفيديو إلى تليجرام"""
    print("جاري إرسال الفيديو إلى تليجرام...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(video_path, 'rb') as video_file:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"فيديو قرآني يومي - مبرمج بواسطة {YOUR_NAME}"}
        files = {'video': video_file}
        response = requests.post(url, data=payload, files=files)
        
    if response.status_code == 200:
        print("تم إرسال الفيديو بنجاح!")
    else:
        print(f"فشل إرسال الفيديو: {response.text}")


def make_pro_video_for_yazeed():
    print("بدء عملية إنتاج الفيديو...")
    audio_path, duration, keyword = get_quran_with_keywords()
    used_videos = load_used_videos()
    
    headers = {'Authorization': PEXELS_API_KEY}
    video_url = None
    
    # محاولة البحث عن فيديو لم يتم استخدامه من قبل (حتى 5 محاولات بصفحات مختلفة)
    for attempt in range(5):
        print(f"جاري البحث عن فيديو مميز (محاولة {attempt+1}) باستخدام: {keyword}")
        params = {
            'query': keyword, 
            'per_page': 15, # نسحب 15 فيديو للمقارنة والاختيار منها لضمان عدم التكرار
            'page': random.randint(1, 20), 
            'orientation': 'portrait', 
            'size': 'large'
        }
        
        v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
        
        if v_data.get('videos'):
            # فحص الفيديوهات المتاحة في الصفحة واختيار أول واحد لم يتم استخدامه
            for v in v_data['videos']:
                current_url = v['video_files'][0]['link']
                if current_url not in used_videos:
                    video_url = current_url
                    break
        
        if video_url:
            break
            
    # إذا لم يجد فيديو جديد (وهذا نادر جداً)، سيأخذ أي فيديو متاح كخيار احتياطي
    if not video_url and v_data.get('videos'):
        video_url = v_data['videos'][0]['video_files'][0]['link']
        print("تنبيه: تم استخدام فيديو معاد لعدم توفر خيارات جديدة في هذه الصفحة.")
    elif not video_url:
        raise Exception("لم يتم العثور على فيديوهات في Pexels.")
        
    # حفظ الفيديو في الذاكرة لمنع تكراره مستقبلاً
    save_used_video(video_url)
    
    # تحميل الفيديو المؤقت للعمل عليه
    with open("v_temp.mp4", "wb") as f: 
        f.write(requests.get(video_url).content)
    
    video_clip = VideoFileClip("v_temp.mp4")
    
    # ضبط مدة الفيديو
    if video_clip.duration < duration:
        loops = int(duration // video_clip.duration) + 1
        from moviepy.editor import concatenate_videoclips
        video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)

    final_clip = video_clip
    try:
        txt_clip = TextClip(YOUR_NAME, fontsize=35, color='white', font='Arial-Bold', method='caption')
        txt_clip = txt_clip.set_position(('center', video_clip.h - 100)).set_duration(duration).set_opacity(0.5)
        final_clip = CompositeVideoClip([video_clip, txt_clip])
    except Exception as e:
        print(f"تنبيه: تم تخطي إضافة النص. الخطأ: {e}")

    output_filename = "quran_daily.mp4"
    print("جاري معالجة وتصدير الفيديو النهائي...")
    final_clip.write_videofile(
        output_filename, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        threads=4, 
        logger=None
    )
    
    final_clip.close()
    video_clip.close()
    audio_clip.close()
    
    send_video_to_telegram(output_filename)
    
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): os.remove(file)
            
    print("تمت العملية بنجاح!")

if __name__ == "__main__":
    make_pro_video_for_yazeed()
