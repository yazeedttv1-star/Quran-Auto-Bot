import os
import random
import requests
from moviepy.editor import VideoFileClip, AudioFileClip

# جلب البيانات من الـ Secrets الخاصة بـ GitHub
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_quran_data():
    """جلب رابط صوتي لآية عشوائية بصوت الشيخ العفاسي"""
    print("جاري اختيار آية عشوائية...")
    # توليد رقم سورة (001-114) ورقم آية (001-005 لضمان التواجد)
    surah = str(random.randint(1, 114)).zfill(3)
    ayah = str(random.randint(1, 5)).zfill(3) 
    
    # رابط مباشر ومستقر جداً
    audio_url = f"https://everyayah.com/data/Alafasy_128kbps/{surah}{ayah}.mp3"
    
    # التأكد من أن الرابط يعمل
    try:
        response = requests.head(audio_url, timeout=10)
        if response.status_code != 200:
            print("الآية المختارة غير موجودة، يتم جلب آية بديلة...")
            audio_url = "https://everyayah.com/data/Alafasy_128kbps/001001.mp3"
    except:
        audio_url = "https://everyayah.com/data/Alafasy_128kbps/001001.mp3"
        
    return audio_url

def get_pexels_video():
    """سحب رابط فيديو طبيعي عشوائي من Pexels"""
    print("جاري البحث عن فيديو طبيعي من Pexels...")
    headers = {'Authorization': PEXELS_API_KEY}
    topics = ['nature', 'mountains', 'sea', 'stars', 'forest']
    params = {
        'query': random.choice(topics),
        'per_page': 1,
        'page': random.randint(1, 100)
    }
    res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    return res['videos'][0]['video_files'][0]['link']

def make_video():
    """عملية المونتاج: دمج الصوت مع الفيديو وقصه"""
    audio_url = get_quran_data()
    video_url = get_pexels_video()

    print("جاري تحميل الملفات المؤقتة...")
    with open("temp_audio.mp3", "wb") as f: 
        f.write(requests.get(audio_url).content)
    with open("temp_video.mp4", "wb") as f: 
        f.write(requests.get(video_url).content)

    print("بدء عملية المونتاج (قد تستغرق دقيقة)...")
    audio_clip = AudioFileClip("temp_audio.mp3")
    
    # تحميل الفيديو وقصه فوراً ليكون بنفس طول الصوت لتوفير الوقت والرام
    full_video = VideoFileClip("temp_video.mp4")
    video_clip = full_video.subclip(0, audio_clip.duration)

    # دمج الصوت مع الفيديو
    final_clip = video_clip.set_audio(audio_clip)
    
    output_file = "quran_video.mp4"
    # الإعدادات لضمان جودة جيدة وحجم ملف صغير للتليجرام
    final_clip.write_videofile(
        output_file, 
        codec="libx264", 
        audio_codec="aac", 
        fps=24, 
        bitrate="2000k",
        threads=4 # استخدام قوة السيرفر كاملة
    )
    
    # إغلاق الملفات لتحرير الذاكرة
    audio_clip.close()
    full_video.close()
    
    return output_file

def send_to_telegram(file_path):
    """إرسال الفيديو النهائي إلى بوت التليجرام"""
    print("جاري إرسال الفيديو إلى تليجرام...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(file_path, "rb") as video:
        files = {"video": video}
        data = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "caption": "تم إنتاج فيديو قرآني جديد بنجاح! ✨"
        }
        res = requests.post(url, files=files, data=data)
    return res.json()

if __name__ == "__main__":
    try:
        generated_video = make_video()
        result = send_to_telegram(generated_video)
        if result.get("ok"):
            print("🚀 تمت العملية بنجاح! تحقق من تليجرام.")
        else:
            print(f"❌ فشل الإرسال: {result}")
    except Exception as e:
        print(f"⚠️ حدث خطأ فني: {e}")
