import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import arabic_reshaper
from bidi.algorithm import get_display

# الإعدادات
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def download_arabic_font():
    """تحميل خط عربي احترافي وفخم (Cairo) لضمان جمال المظهر على السيرفر"""
    font_path = "Cairo-Bold.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo%5Bwght%5D.ttf"
        r = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(r.content)
    return font_path

def fix_arabic_text(text):
    """إصلاح الحروف المقطوعة والمقلوبة لتظهر متصلة ومنسقة ومن اليمين لليسار"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def get_quran_data():
    """جلب بيانات السورة والصوت والنصوص"""
    reciter = random.choice(["Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps"])
    reciter_name = "الشيخ ياسر الدوسري" if "Yasser" in reciter else "الشيخ ناصر القطامي"
    
    surah_num = random.randint(1, 114)
    start_ayah = random.randint(1, 10)
    
    meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    surah_name = meta_res['data']['name']
    
    clips = []
    temp_files = []
    total_duration = 0
    ayah_texts = []
    current_ayah = start_ayah
    
    # جلب آيتين لضمان عدم تكدس الشاشة بالخطوط
    for _ in range(2):
        audio_url = f"https://everyayah.com/data/{reciter}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(audio_url)
        if r.status_code == 200:
            t_name = f"a_{current_ayah}.mp3"
            with open(t_name, "wb") as f: f.write(r.content)
            temp_files.append(t_name)
            
            clip = AudioFileClip(t_name).set_fps(44100).audio_fadein(0.3).audio_fadeout(0.3)
            clips.append(clip)
            total_duration += clip.duration
            
            text_res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{current_ayah}").json()
            ayah_texts.append(text_res['data']['text'])
            current_ayah += 1
        else:
            break

    final_audio_path = "final.mp3"
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    final_audio.close()
    for c in clips: c.close()
    for f in temp_files:
        if os.path.exists(f): os.remove(f)
        
    full_text = " ﴿ " + " ﴾ * ﴿ ".join(ayah_texts) + " ﴾ "
    info_text = f"🎙️ {reciter_name}  |  📖 {surah_name}"
    
    return final_audio_path, total_duration, full_text, info_text

def make_frame(image_np, text_top, text_bottom, font_path):
    """رسم المونتاج وتنسيق الخطوط بدقة متناهية"""
    img = Image.fromarray(image_np)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # تحديد أحجام الخطوط بناءً على حجم الفيديو
    font_quran = ImageFont.truetype(font_path, int(width * 0.045))
    font_sub = ImageFont.truetype(font_path, int(width * 0.035))
    
    # 1. عمل تأثير تعتيم ذكي (Dark Overlay) أسفل النص لمنع التداخل مع ألوان الفيديو
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # مستطيل خلفية النص القرآني
    overlay_draw.rectangle([(0, height // 3), (width, height - 100)], fill=(0, 0, 0, 80))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # 2. تقسيم وكتابة نص القرآن منسق ومصلح
    words = text_top.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 26:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    y_offset = height // 2 - (len(lines) * 25)
    for line in lines:
        fixed_line = fix_arabic_text(line)
        w = draw.textlength(fixed_line, font=font_quran)
        draw.text(((width - w) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
        y_offset += int(height * 0.07)

    # 3. كتابة بيانات الشيخ والسورة مصلحة
    fixed_info = fix_arabic_text(text_bottom)
    w_info = draw.textlength(fixed_info, font=font_sub)
    draw.text(((width - w_info) // 2, height - int(height * 0.18)), fixed_info, font=font_sub, fill="#FFD700") # لون ذهبي فخم
    
    # 4. كتابة عبارة "راحة نفسية 🌿"
    fixed_comfort = fix_arabic_text("راحة نفسية 🌿")
    w_comfort = draw.textlength(fixed_comfort, font=font_sub)
    draw.text(((width - w_comfort) // 2, height - int(height * 0.10)), fixed_comfort, font=font_sub, fill="#00FFCC") # لون مائي مريح
    
    return np.array(img)

def generate_video():
    font_path = download_arabic_font()
    audio_path, duration, quran_text, info_text = get_quran_data()
    
    # جلب فيديو طبيعة (جبال أو أنهار) بجودة عالية وطولي
    search_keywords = ['mountains', 'river', 'nature']
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': random.choice(search_keywords), 'per_page': 15, 'orientation': 'portrait'}
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

    # تشغيل معالجة الفريمات الذكية بالخط الجديد والتنسيق المصلح
    final_clip = video_clip.fl_image(lambda frame: make_frame(frame, quran_text, info_text, font_path))
    
    audio_clip = AudioFileClip(audio_path)
    final_clip = final_clip.set_audio(audio_clip)

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    video_clip.close()
    audio_clip.close()
    
    # إرسال الفيديو الاحترافي النهائي إلى تليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = f"🌸 {info_text}\n✨ تصميم ومونتاج تلقائي احترافي لقناتك."
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        files = {'video': video_file}
        requests.post(url, data=payload, files=files)
        
    # تنظيف
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): os.remove(file)

if __name__ == "__main__":
    generate_video()
