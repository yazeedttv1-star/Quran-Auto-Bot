import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def get_quran_data():
    """جلب الآيات، ملفات الصوت، النص العربي، وبيانات السورة"""
    reciter = random.choice(["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"])
    reciter_name = "الشيخ ياسر الدوسري" if "Yasser" in reciter else "الشيخ ناصر القطامي"
    
    # اختيار سورة وآية عشوائية (تجنب السور الطويلة جداً لضمان التناسق)
    surah_num = random.randint(1, 114)
    start_ayah = random.randint(1, 5)
    
    # جلب معلومات السورة من API القرآن
    meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    surah_name = meta_res['data']['name']
    
    clips = []
    temp_files = []
    total_duration = 0
    ayah_texts = []
    current_ayah = start_ayah
    
    # جلب 3 آيات متتالية لعمل مقطع مناسب
    for _ in range(3):
        # تحميل الصوت
        audio_url = f"https://everyayah.com/data/{reciter}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(audio_url)
        if r.status_code == 200:
            t_name = f"a_{current_ayah}.mp3"
            with open(t_name, "wb") as f: f.write(r.content)
            temp_files.append(t_name)
            
            clip = AudioFileClip(t_name).set_fps(44100).audio_fadein(0.2).audio_fadeout(0.2)
            clips.append(clip)
            total_duration += clip.duration
            
            # جلب نص الآية المكتوب
            text_res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{current_ayah}").json()
            ayah_texts.append(text_res['data']['text'])
            
            current_ayah += 1
        else:
            break

    final_audio_path = "final.mp3"
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    # تنظيف
    final_audio.close()
    for c in clips: c.close()
    for f in temp_files:
        if os.path.exists(f): os.remove(f)
        
    full_text = " * ".join(ayah_texts)
    info_text = f"🎙️ {reciter_name} | 📖 {surah_name} (الآيات: {start_ayah}-{current_ayah-1})"
    
    return final_audio_path, total_duration, full_text, info_text

def make_frame(image_np, text_top, text_bottom):
    """دالة ذكية لرسم النصوص الاحترافية على الفيديوهات باستخدام Pillow لضمان استقرار السيرفر"""
    img = Image.fromarray(image_np)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # محاولة استخدام خط النظام الافتراضي
    try:
        font_top = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(width * 0.04))
        font_bottom = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(width * 0.03))
    except:
        font_top = font_bottom = ImageFont.load_default()

    # 1. رسم نص القرآن الكريم في المنتصف (مع خلفية ظل سوداء خفيفة لتبرز الكلمات)
    words = text_top.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 30:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    y_offset = height // 2 - (len(lines) * 20)
    for line in lines:
        w = draw.textlength(line, font=font_top)
        # الظل
        draw.text(((width - w) // 2 + 2, y_offset + 2), line, font=font_top, fill="black")
        # النص الأساسي
        draw.text(((width - w) // 2, y_offset), line, font=font_top, fill="white")
        y_offset += int(height * 0.06)

    # 2. رسم الحقوق واسم القارئ والسورة في الأسفل
    w_info = draw.textlength(text_bottom, font=font_bottom)
    draw.text(((width - w_info) // 2, height - int(height * 0.15)), text_bottom, font=font_bottom, fill="#E0E0E0")
    
    # 3. رسم عبارة "راحة نفسية 🌿"
    comfort_text = "راحة نفسية 🌿"
    w_comfort = draw.textlength(comfort_text, font=font_bottom)
    draw.text(((width - w_comfort) // 2, height - int(height * 0.08)), comfort_text, font=font_bottom, fill="#00FFCC")
    
    return np.array(img)

def generate_video():
    audio_path, duration, quran_text, info_text = get_quran_data()
    
    # جلب فيديو طبيعة متجدد من Pexels
    search_keywords = ['mountains', 'river', 'nature']
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': random.choice(search_keywords), 'per_page': 10, 'orientation': 'portrait'}
    v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params).json()
    video_url = random.choice(v_data['videos'])['video_files'][0]['link']
    
    with open("v_temp.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    video_clip = VideoFileClip("v_temp.mp4")
    if video_clip.duration < duration:
        loops = int(duration // video_clip.duration) + 1
        from moviepy.editor import concatenate_videoclips
        video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    # تطبيق دالة الرسم الاحترافية على كل فريم في الفيديو
    final_clip = video_clip.fl_image(lambda frame: make_frame(frame, quran_text, info_text))
    
    audio_clip = AudioFileClip(audio_path)
    final_clip = final_clip.set_audio(audio_clip)

    output_filename = "quran_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    video_clip.close()
    audio_clip.close()
    
    # إرسال الفيديو الاحترافي إلى تليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = f"🌸 {info_text}\n✨ تصميم ومونتاج تلقائي بواسطة برمجية: {YOUR_NAME}"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        files = {'video': video_file}
        requests.post(url, data=payload, files=files)
        
    # تنظيف السيرفر
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): os.remove(file)

if __name__ == "__main__":
    generate_video()
