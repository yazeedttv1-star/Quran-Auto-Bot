import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, ColorClip, CompositeVideoClip
import arabic_reshaper
from bidi.algorithm import get_display

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
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
    """جلب الصوت والبيانات من سيرفر mp3quran المستقر والمحمي من الحظر"""
    # قائمة القراء وروابطهم المباشرة السريعة والمستقرة
    reciters = [
        {"name": "الشيخ ياسر الدوسري", "url": "https://server11.mp3quran.net/yasser/"},
        {"name": "الشيخ ناصر القطامي", "url": "https://server11.mp3quran.net/qtm/"},
        {"name": "الشيخ ماهر المعيقلي", "url": "https://server12.mp3quran.net/maher/"}
    ]
    chosen = random.choice(reciters)
    reciter_name = chosen["name"]
    base_url = chosen["url"]
    
    # اختيار سورة عشوائية قصيرة أو متوسطة لضمان التحميل السريع والتناسق
    surah_num = random.randint(70, 114)
    surah_str = str(surah_num).zfill(3)
    audio_url = f"{base_url}{surah_str}.mp3"
    
    # جلب اسم السورة ونصها
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
        ayahs_data = meta_res['data']['ayahs']
    except:
        surah_name = "سورة من القرآن"
        ayahs_data = []

    # تحميل السورة كاملة من السيرفر المستقر
    audio_path = "temp_surah.mp3"
    r = requests.get(audio_url, timeout=20, verify=False)
    if r.status_code == 200:
        with open(audio_path, "wb") as f:
            f.write(r.content)
    else:
        raise Exception("فشل الاتصال بسيرفر الصوت الاحتياطي أيضاً، يرجى المحاولة لاحقاً.")

    # قص مقطع عشوائي مدته 15-20 ثانية لتجنب الفيديوهات الطويلة جداً في الريلز
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
        
    # استخراج النصوص المناسبة للمقطع المقصوص بشكل متتابع
    ayahs_timeline = []
    if ayahs_data:
        # توزيع تقريبي وعادل للآيات على مدة الفيديو لتعرض آية تلو الأخرى
        num_ayahs = min(3, len(ayahs_data))
        selected_ayahs = random.sample(ayahs_data, num_ayahs)
        # ترتيبهم حسب المصحف
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

def create_static_overlay(w, h, info_text, hook_text, cta_text):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_sub = ImageFont.truetype(font_path, int(w * 0.038))
        font_hook = ImageFont.truetype(font_path, int(w * 0.045))
    except:
        font_sub = font_hook = ImageFont.load_default()
        
    draw.rectangle([(0, 0), (w, h)], fill=(0, 0, 0, 45))
    draw.rectangle([(0, h - 180), (w, h)], fill=(0, 0, 0, 110))
    
    fixed_info = fix_arabic_text(info_text)
    w_info = draw.textlength(fixed_info, font=font_sub)
    draw.text(((w - w_info) // 2, h - 140), fixed_info, font=font_sub, fill="#E0E0E0")
    
    fixed_cta = fix_arabic_text(cta_text)
    w_cta = draw.textlength(fixed_cta, font=font_sub)
    draw.text(((w - w_cta) // 2, h - 70), fixed_cta, font=font_sub, fill="#00FFCC")
    
    fixed_hook = fix_arabic_text(hook_text)
    w_hook = draw.textlength(fixed_hook, font=font_hook)
    draw.text(((w - w_hook) // 2, int(h * 0.12)), fixed_hook, font=font_hook, fill="#FFD700")
    
    return np.array(img.convert('RGB'))

def create_ayah_frame(w, h, raw_text):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_quran = ImageFont.truetype(font_path, int(w * 0.052))
    except:
        font_quran = ImageFont.load_default()
        
    words = raw_text.split()
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
        draw.text(((w - w_line) // 2 + 1, y_offset + 1), fixed_line, font=font_quran, fill="#8B6508")
        draw.text(((w - w_line) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
        y_offset += int(h * 0.075)
        
    return img

def generate_video():
    hooks = ["رسالة لقلبك المتعب 🤍", "قبل أن تنام استمع لها 🌿", "إذا ضاقت بك الدنيا استمع 🏔️", "راحة لروحك المرهقة ✨"]
    ctas = ["اكتب (سبحان الله) وتؤجر ✍️", "شاركها لعلها تشفع لك يوم القيامة 🔄", "صلّ على النبي في التعليقات 🌸"]
    
    chosen_hook = random.choice(hooks)
    chosen_cta = random.choice(ctas)

    audio_path, total_duration, ayahs_timeline, info_text, reciter, surah = get_quran_data()
    
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': random.choice(['mountains', 'river', 'nature', 'rain']), 'per_page': 10, 'orientation': 'portrait'}
    v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15).json()
    video_url = random.choice(v_data['videos'])['video_files'][0]['link']
    
    with open("v_temp.mp4", "wb") as f: 
        f.write(requests.get(video_url).content)
    
    video_clip = VideoFileClip("v_temp.mp4")
    if video_clip.duration < total_duration:
        loops = int(total_duration // video_clip.duration) + 1
        from moviepy.editor import concatenate_videoclips
        video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, total_duration)
    else:
        video_clip = video_clip.subclip(0, total_duration)

    w, h = video_clip.size
    
    static_overlay_np = create_static_overlay(w, h, info_text, chosen_hook, chosen_cta)
    base_video = video_clip.fl_image(lambda frame: np.array(Image.blend(Image.fromarray(frame), Image.fromarray(static_overlay_np), 0.35).convert('RGB')))
    
    all_clips = [base_video]

    # دمج الآيات المتتالية بشكل سليم وآمن تماماً
    for item in ayahs_timeline:
        raw_text = item['text']
        ayah_img = create_ayah_frame(w, h, raw_text)
        
        ayah_clip = ColorClip(size=(w, h), color=(0, 0, 0), ismask=False)
        ayah_clip = ayah_clip.fl_image(lambda img: np.array(Image.alpha_composite(Image.fromarray(img).convert('RGBA'), ayah_img).convert('RGB')))
        
        ayah_clip = ayah_clip.set_start(item['start']).set_end(item['end']).set_duration(item['end'] - item['start']).set_pos(("center", "center"))
        all_clips.append(ayah_clip)

    final_clip = CompositeVideoClip(all_clips)
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    for clip_item in all_clips:
        clip_item.close()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = (
            f"📖 *تلاوة خاشعة يومية متزامنة* 📖\n\n"
            f"🎙️ القارئ: #{reciter.replace(' ', '_')}\n"
            f"🕌 سورة: #{surah.replace(' ', '_')}\n\n"
            f"◽ ◽ ◽ ◽ ◽ ◽ ◽\n"
            f"📣 {chosen_cta}\n\n"
            f"✨ مونتاج سينمائي آلي احترافي بدون أخطاء | خادم: {YOUR_NAME}"
        )
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': video_file})
        
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): 
            os.remove(file)

if __name__ == "__main__":
    generate_video()
