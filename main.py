import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ColorClip
import arabic_reshaper
from bidi.algorithm import get_display

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def fix_arabic_text(text):
    try:
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def get_quran_data():
    surah_num = random.randint(70, 114)
    surah_str = str(surah_num).zfill(3)
    
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
        ayahs_data = meta_res['data']['ayahs']
    except:
        surah_name = "سورة من القرآن"
        ayahs_data = []

    reciters = [
        {"name": "الشيخ ياسر الدوسري", "urls": [
            f"https://server11.mp3quran.net/yasser/{surah_str}.mp3",
            f"https://download.quranicaudio.com/quran/yasser_al-dosari/{surah_str}.mp3"
        ]},
        {"name": "الشيخ ماهر المعيقلي", "urls": [
            f"https://server12.mp3quran.net/maher/{surah_str}.mp3",
            f"https://download.quranicaudio.com/quran/maher_al_muaiqly/hq/{surah_str}.mp3"
        ]},
        {"name": "الشيخ ناصر القطامي", "urls": [
            f"https://server11.mp3quran.net/qtm/{surah_str}.mp3",
            f"https://download.quranicaudio.com/quran/nasser_alqatami/{surah_str}.mp3"
        ]}
    ]
    
    chosen = random.choice(reciters)
    reciter_name = chosen["name"]
    
    audio_path = "temp_surah.mp3"
    download_success = False
    
    for url in chosen["urls"]:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, timeout=30, headers=headers, verify=False)
            if r.status_code == 200 and len(r.content) > 100000:
                with open(audio_path, "wb") as f:
                    f.write(r.content)
                download_success = True
                break
        except:
            continue
            
    if not download_success:
        emergency_url = "https://server12.mp3quran.net/maher/001.mp3"
        r = requests.get(emergency_url, timeout=30, verify=False)
        with open(audio_path, "wb") as f:
            f.write(r.content)
        reciter_name = "الشيخ ماهر المعيقلي"
        surah_name = "سورة الفاتحة"
        meta_res = requests.get("https://api.alquran.cloud/v1/surah/1", timeout=15).json()
        ayahs_data = meta_res['data']['ayahs']

    full_audio = AudioFileClip(audio_path).set_fps(44100)
    total_len = full_audio.duration
    
    start_time = random.uniform(0, max(0, total_len - 22))
    end_time = min(start_time + random.uniform(15, 20), total_len)
    
    final_audio_path = "final.mp3"
    sub_audio = full_audio.subclip(start_time, end_time).audio_fadein(0.5).audio_fadeout(0.5)
    sub_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    duration = sub_audio.duration
    full_audio.close()
    sub_audio.close()
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    ayahs_timeline = []
    if ayahs_data:
        num_ayahs = min(3, len(ayahs_data))
        selected_ayahs = random.sample(ayahs_data, num_ayahs)
        selected_ayahs.sort(key=lambda x: x['numberInSurah'])
        
        step = duration / num_ayahs
        for i, ayah in enumerate(selected_ayahs):
            ayahs_timeline.append({
                'text': f" ﴿ {ayah['text']} ﴾ ",
                'start': i * step,
                'end': (i + 1) * step
            })
            
    info_text = f"🎙️ {reciter_name}  |  📖 {surah_name}"
    return final_audio_path, duration, ayahs_timeline, info_text, reciter_name, surah_name

def render_chroma_frame(t, ayahs_timeline, info_text, hook_text, cta_text, w, h):
    """إنشاء فريم كروما سوداء نقي ومستقر ومحقون بالنصوص مباشرة"""
    # إنشاء خلفية سوداء تماماً بأبعاد الطول (Reels) القياسية
    img = Image.new('RGB', (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_sub = ImageFont.truetype(font_path, int(w * 0.038))
        font_hook = ImageFont.truetype(font_path, int(w * 0.045))
        font_quran = ImageFont.truetype(font_path, int(w * 0.052))
    except:
        font_sub = font_hook = font_quran = ImageFont.load_default()
        
    # 1. رسم النصوص الثابتة والمؤثرة
    fixed_hook = fix_arabic_text(hook_text)
    w_hook = draw.textlength(fixed_hook, font=font_hook)
    draw.text(((w - w_hook) // 2, int(h * 0.12)), fixed_hook, font=font_hook, fill="#FFD700")
    
    fixed_info = fix_arabic_text(info_text)
    w_info = draw.textlength(fixed_info, font=font_sub)
    draw.text(((w - w_info) // 2, h - 140), fixed_info, font=font_sub, fill="#E0E0E0")
    
    fixed_cta = fix_arabic_text(cta_text)
    w_cta = draw.textlength(fixed_cta, font=font_sub)
    draw.text(((w - w_cta) // 2, h - 70), fixed_cta, font=font_sub, fill="#00FFCC")
    
    # 2. البحث عن الآية التي عليها الدور وعرضها منفردة
    current_ayah_text = ""
    for item in ayahs_timeline:
        if item['start'] <= t <= item['end']:
            current_ayah_text = item['text']
            break
            
    if current_ayah_text:
        words = current_ayah_text.split()
        lines, current_line = [], []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 22:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        y_offset = (h // 2) - (len(lines) * 30)
        for line in lines:
            fixed_line = fix_arabic_text(line)
            w_line = draw.textlength(fixed_line, font=font_quran)
            # رسم توهج نحاسي فخم لإعطاء مظهر جمالي على الخلفية السوداء
            draw.text(((w - w_line) // 2 + 1, y_offset + 1), fixed_line, font=font_quran, fill="#8B6508")
            draw.text(((w - w_line) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
            y_offset += int(h * 0.075)

    return np.array(img).astype('uint8')

def generate_video():
    hooks = ["رسالة لقلبك المتعب 🤍", "قبل أن تنام استمع لها 🌿", "إذا ضاقت بك الدنيا استمع 🏔️", "راحة لروحك المرهقة ✨"]
    ctas = ["اكتب (سبحان الله) وتؤجر ✍️", "شاركها لعلها تشفع لك يوم القيامة 🔄", "صلّ على النبي في التعليقات 🌸"]
    
    chosen_hook = random.choice(hooks)
    chosen_cta = random.choice(ctas)

    audio_path, total_duration, ayahs_timeline, info_text, reciter, surah = get_quran_data()
    
    # تحديد مقاسات الفيديو الطولي القياسي (720x1280)
    w, h = 720, 1280
    
    # صناعة الكليب برمجياً بالكامل من دالة الفريمات لضمان أقصى درجات الاستقرار والسرعة
    final_clip = ColorClip(size=(w, h), color=(0, 0, 0), duration=total_duration)
    final_clip = final_clip.fl(lambda gf, t: render_chroma_frame(t, ayahs_timeline, info_text, chosen_hook, chosen_cta, w, h))
    
    # دمج كليب الصوت الذي تم تحميله بنجاح
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    
    # إرسال كود المونتاج الاحترافي الصافي إلى التليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = (
            f"📖 *تلاوة خاشعة - كروما سوداء سينمائية* 📖\n\n"
            f"🎙️ القارئ: #{reciter.replace(' ', '_')}\n"
            f"🕌 سورة: #{surah.replace(' ', '_')}\n\n"
            f"◽ ◽ ◽ ◽ ◽ ◽ ◽\n"
            f"📣 {chosen_cta}\n\n"
            f"✨ تصميم كروما أسود فاخر وخالي من الأخطاء | خادمكم: {YOUR_NAME}"
        )
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': video_file})
        
    time.sleep(2)
    for file in ["final.mp3", output_filename]:
        if os.path.exists(file): 
            os.remove(file)

if __name__ == "__main__":
    generate_video()
