import os
import random
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# جلب البيانات من الـ Secrets الخاصة بـ GitHub
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_quran_data():
    # اختيار آية عشوائية (سورة : آية)
    surah = random.randint(1, 114)
    # لتبسيط الأمر سنجلب أول آية من سورة عشوائية أو يمكنك تطويرها لجلب آية محددة
    res = requests.get(f"https://api.quran.com/api/v4/recitations/7/by_ayah/{surah}:1").json()
    audio_url = res['audio_files'][0]['url']
    if not audio_url.startswith('http'):
        audio_url = "https://audio.quran.com/" + audio_url
    return audio_url

def get_pexels_video():
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': 'nature', 'per_page': 1, 'page': random.randint(1, 50)}
    res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    return res['videos'][0]['video_files'][0]['link']

def make_video():
    print("جاري تجهيز المصادر...")
    audio_url = get_quran_data()
    video_url = get_pexels_video()

    # تحميل الملفات مؤقتاً
    with open("temp_audio.mp3", "wb") as f: f.write(requests.get(audio_url).content)
    with open("temp_video.mp4", "wb") as f: f.write(requests.get(video_url).content)

    print("جاري المونتاج...")
    video_clip = VideoFileClip("temp_video.mp4")
    audio_clip = AudioFileClip("temp_audio.mp3")

    # جعل مدة الفيديو مطابقة للصوت
    final_clip = video_clip.set_audio(audio_clip).set_duration(audio_clip.duration)
    # تصغير حجم الفيديو ليكون مناسباً للتليجرام (اختياري)
    final_clip = final_clip.resize(height=720) 
    
    output_file = "quran_video.mp4"
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24)
    return output_file

def send_to_telegram(file_path):
    print("جاري الإرسال إلى تليجرام...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(file_path, "rb") as video:
        files = {"video": video}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "تم إنشاء فيديو جديد بنجاح! ❤️"}
        res = requests.post(url, files=files, data=data)
    return res.json()

if __name__ == "__main__":
    try:
        video_file = make_video()
        send_to_telegram(video_file)
        print("تمت العملية بنجاح!")
    except Exception as e:
        print(f"حدث خطأ: {e}")
