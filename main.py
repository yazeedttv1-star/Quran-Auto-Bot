import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

# قائمة القراء والروابط الخاصة بهم على خادم mp3quran
RECITERS = [
    {"name": "الشيخ ماهر المعيقلي", "server": "https://server12.mp3quran.net/maher/"},
    {"name": "الشيخ مشاري العفاسي", "server": "https://server8.mp3quran.net/afs/"},
    {"name": "الشيخ أحمد العجمي", "server": "https://server10.mp3quran.net/ajm/"},
    {"name": "الشيخ عبد الباسط عبد الصمد", "server": "https://server7.mp3quran.net/basit/"},
    {"name": "الشيخ عبد الرحمن السديس", "server": "https://server11.mp3quran.net/sds/"},
    {"name": "الشيخ سعود الشريم", "server": "https://server7.mp3quran.net/shur/"}
]

def get_random_surah_and_reciter():
    """اختيار سورة وقارئ عشوائيين وجلب البيانات والصوت من الإنترنت"""
    # اختيار سورة عشوائية قصيرة (من 100 العاديات إلى 114 الناس) لضمان سرعة معالجة الفيديو
    surah_num = random.randint(100, 114)
    reciter = random.choice(RECITERS)
    
    # 1. جلب آيات السورة من الـ API العام للقرآن الكريم
    api_url = f"https://api.alquran.cloud/v1/surah/{surah_num}"
    verses = []
    surah_name = "سورة"
    
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            surah_name = data['data']['name']
            verses = [ayah['text'] for ayah in data['data']['ayahs']]
            
            # ترتيب وعزل البسملة في البداية لتظهر مستقلة ومنسقة
            if surah_num not in [1, 9] and verses[0].startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"):
                verses[0] = verses[0].replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
                verses.insert(0, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
                
            print(f"تم اختيار وجلب {surah_name} بنجاح.")
    except Exception as e:
        print(f"حدث خطأ أثناء جلب آيات السورة: {e}")
        # خط دفاع احتياطي إذا فشل الاتصال بالـ API
        surah_name = "سورة الكوثر"
        verses = ["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ"]

    # 2. تحميل الملف الصوتي للسورة للقارئ الذي تم اختياره
    surah_str = str(surah_num).zfill(3)
    audio_url = f"{reciter['server']}{surah_str}.mp3"
    audio_path = "temp_surah.mp3"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        print(f"جاري تحميل صوت {surah_name} بصوت {reciter['name']}...")
        r = requests.get(audio_url, timeout=20, headers=headers, verify=False)
        if r.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(r.content)
        else:
            raise Exception("فشل في استجابة خادم الصوت")
    except Exception as e:
        print(f"تعذر تحميل صوت القارئ العشوائي ({e})، جاري استخدام الصوت الاحتياطي...")
        # صوت احتياطي ثابت لضمان عدم توقف المشروع أبداً
        emergency_url = "https://server12.mp3quran.net/maher/108.mp3"
        r = requests.get(emergency_url, timeout=20, verify=False)
        with open(audio_path, "wb") as f:
            f.write(r.content)
        reciter = {"name": "الشيخ ماهر المعيقلي"}
        surah_name = "سورة الكوثر"
        verses = ["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ"]

    return audio_path, verses, surah_name, reciter['name']

def download_arabic_font():
    """تحميل خط عربي تلقائي ليتم استخدامه في بيئات GitHub و لينكس للتابلت"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"خطأ أثناء تحميل الخط: {e}")
    return font_path

def create_text_image(text, font_path, width=720, height=1280):
    """توليد فريم فيديو أسود بداخله الآية أو الدعاء في المنتصف تماماً"""
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, 44)
    except Exception:
        font = ImageFont.load_default()
        
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return np.array(img)

def generate_video():
    # جلب البيانات تلقائياً وعشوائياً بالكامل
    audio_path, verses, surah_name, reciter_name = get_random_surah_and_reciter()
    font_path = download_arabic_font()
    
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    
    # الحفاظ التام على طول كروما 30 ثانية كما طلبت
    target_duration = 30 
    fps = 10 
    total_frames = target_duration * fps
    
    # حساب التوزيع الزمني التلقائي الدقيق للآيات بالتساوي على طول المقطع الصوتي الفعلي
    num_verses = len(verses)
    verse_duration = audio_duration / num_verses
    
    subtitles = []
    for i, verse in enumerate(verses):
        start_s = i * verse_duration
        end_s = (i + 1) * verse_duration
        subtitles.append({"text": verse, "start_s": start_s, "end_s": end_s})
        
    # ملء ما تبقى من الـ 30 ثانية بأدعية خاشعة تلقائية تظهر على الكروما السوداء بعد انتهاء الصوت
    extra_subtitles = [
        {"text": "صَدَقَ اللهُ العَظِيم", "start_s": audio_duration, "end_s": audio_duration + 4.0},
        {"text": "اللهم اجعل القرآن الكريم ربيع قلوبنا ونور صدورنا", "start_s": audio_duration + 4.0, "end_s": audio_duration + 8.5},
        {"text": "سبحان الله وبحمده ، سبحان الله العظيم", "start_s": audio_duration + 8.5, "end_s": 30.0}
    ]
    subtitles.extend(extra_subtitles)
    
    frames = []
    print("جاري تركيب الكروما السوداء والفريمات وكتابة الآيات ديناميكياً...")
    
    for frame_idx in range(total_frames):
        current_time = frame_idx / fps
        current_text = ""
        
        # البحث عن النص المطابق للتوقيت الحالي
        for sub in subtitles:
            if sub["start_s"] <= current_time < sub["end_s"]:
                current_text = sub["text"]
                break
        
        frame_img = create_text_image(current_text, font_path)
        frames.append(frame_img)
        
    # دمج وبناء الفيديو النهائي
    video_clip = ImageSequenceClip(frames, fps=fps)
    video_clip = video_clip.set_audio(audio_clip.set_duration(target_duration))
    
    output_filename = "quran_chroma.mp4"
    
    video_clip.write_videofile(
        output_filename, 
        fps=fps, 
        codec="libx264", 
        audio_codec="aac", 
        logger=None
    )
    
    video_clip.close()
    audio_clip.close()
    
    # إرسال الفيديو لتيليجرام وتوثيق البيانات في وصف الفيديو
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    caption_text = f"📖 {surah_name}\n🎙️ بصوت {reciter_name}\n✨ كروما سوداء للمونتاج والتصميم - ٣٠ ثانية\n\nخادمكم وصاحب المشروع: {YOUR_NAME}"
    
    with open(output_filename, 'rb') as video_file:
        response = requests.post(
            url, 
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}, 
            files={'video': video_file}
        )
        
    # تنظيف مجلد العمل وحذف الملفات المؤقتة لمنع تراكم المساحة على سيرفر جيت هاب
    cleanup_files = [audio_path, output_filename, font_path]
    for file in cleanup_files:
        if os.path.exists(file): 
            os.remove(file)
            
    if response.status_code == 200:
        print("====================================")
        print(f"تم النشر! السورة: {surah_name} | القارئ: {reciter_name} ✅")
        print("====================================")
    else:
        print(f"فشل إرسال الفيديو للبوت، كود الخطأ: {response.status_code}")

if __name__ == "__main__":
    generate_video()
