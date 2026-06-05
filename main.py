import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
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
    reciters = [
        {"name": "الشيخ ياسر الدوسري", "url": "https://server11.mp3quran.net/yasser/"},
        {"name": "الشيخ ناصر القطامي", "url": "https://server11.mp3quran.net/qtm/"},
        {"name": "الشيخ ماهر المعيقلي", "url": "https://server12.mp3quran.net/maher/"}
    ]
    chosen = random.choice(reciters)
    reciter_name = chosen["name"]
    base_url = chosen["url"]
    
    surah_num = random.randint(70, 114)
    surah_str = str(surah_num).zfill(3)
    audio_url = f"{base_url}{surah_str}.mp3"
    
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
        ayahs_data = meta_res['data']['ayahs']
    except:
        surah_name = "سورة من القرآن"
        ayahs_data = []

    audio_path = "temp_surah.mp3"
    r = requests.get(audio_url, timeout=20, verify=False)
    if r.status_code == 200:
        with open(audio_path, "wb") as f:
            f.write(r.content)
    else:
        raise Exception("فشل تحميل الصوت")

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

def process_video_frame(frame, t, ayahs_timeline, info_text, hook_text, cta_text):
    img = Image.fromarray(frame.astype('uint8')).convert('RGB')
    width, height = img.size
    
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_sub = ImageFont.truetype(font_path, int(width * 0.038))
        font_hook = ImageFont.truetype(font_path, int(width * 0.045))
        font_quran = ImageFont.truetype(font_path, int(width * 0.052))
    except:
        font_sub = font_hook = font_quran = ImageFont.load_default()
        
    draw.rectangle([(0, 0), (width, height)], fill=(0, 0, 0, 45))
    draw.rectangle([(0, height - 180), (width, height)], fill=(0, 0, 0, 110))
    
    fixed_hook = fix_arabic_text(hook_text)
    w_hook = draw.textlength(fixed_hook, font=font_hook)
    draw.text(((width - w_hook) // 2, int(height * 0.12)), fixed_hook, font=font_hook, fill="#FFD700")
    
    fixed_info = fix_arabic_text(info_text)
    w_info = draw.textlength(fixed_info, font=font_sub)
    draw.text(((width - w_info) // 2, height - 140), fixed_info, font=font_sub, fill="#E0E0E0")
    
    fixed_cta = fix_arabic_text(cta_text)
    w_cta = draw.textlength(fixed_cta, font=font_sub)
    draw.text(((width - w_cta) // 2, height - 70), fixed_cta, font=font_sub, fill="#00FFCC")
    
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
        
        y_offset = (height // 2) - (len(lines) * 30)
        for line in lines:
            fixed_line = fix_arabic_text(line)
            w_line = draw.textlength(fixed_line, font=font_quran)
            draw.text(((width - w_line) // 2 + 1, y_offset + 1), fixed_line, font=font_quran, fill="#8B6508")
            draw.text(((width - w_line) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
            y_offset += int(height * 0.075)

    img.paste(overlay, (0, 0), overlay)
    return np.array(img).astype('uint8')

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

    # التعديل الجذري: قمنا بتعريف دالة واضحة للـ fl بدون استخدام أقواس الـ lambda المعقدة
    def make_frame_at_t(get_frame, t):
        return process_video_frame(get_frame(t), t, ayahs_timeline, info_text, chosen_hook, chosen_cta)

    final_clip = video_clip.fl(make_frame_at_t)
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    video_clip.close()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = (
            f"📖 *تلاوة خاشعة يومية متزامنة* 📖\n\n"
            f"🎙️ القارئ: #{reciter.replace(' ', '_')}\n"
            f"🕌 سورة: #{surah.replace(' ', '_')}\n\n"
            f"◽ ◽ ◽ ◽ ◽ ◽ ◽\n"
            f"📣 {chosen_cta}\n\n"
            f"✨ مونتاج آلي سينمائي متزامن ومثالي | خادمكم: {YOUR_NAME}"
        )
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': video_file})
        
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): 
            os.remove(file)

if __name__ == "__main__":
    generate_video()
