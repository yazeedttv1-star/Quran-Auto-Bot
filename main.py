import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import arabic_reshaper
from bidi.algorithm import get_display

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

def fix_arabic_text(text):
    try:
        return get_display(arabic_reshaper.reshape(text))
    except:
        return text

def get_quran_data():
    reciter_options = [
        {"id": "Yasser_Ad-Dussary_128kbps", "name": "الشيخ ياسر الدوسري"},
        {"id": "Nasser_Alqatami_128kbps", "name": "الشيخ ناصر القطامي"}
    ]
    chosen = random.choice(reciter_options)
    reciter_id = chosen["id"]
    reciter_name = chosen["name"]
    
    surah_num = random.randint(1, 114)
    start_ayah = random.randint(1, 10)
    
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
    except:
        surah_name = "سورة من القرآن"
    
    clips, temp_files, ayah_texts = [], [], []
    current_ayah = start_ayah
    
    # دمج آيتين لضمان الطول المناسب والتناسق
    for _ in range(2):
        audio_url = f"https://everyayah.com/data/{reciter_id}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        r = requests.get(audio_url, timeout=15)
        if r.status_code == 200:
            t_name = f"a_{current_ayah}.mp3"
            with open(t_name, "wb") as f: f.write(r.content)
            temp_files.append(t_name)
            clip = AudioFileClip(t_name).set_fps(44100).audio_fadein(0.2).audio_fadeout(0.2)
            clips.append(clip)
            
            try:
                text_res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{current_ayah}", timeout=15).json()
                ayah_texts.append(text_res['data']['text'])
            except:
                pass
            current_ayah += 1
        else:
            break

    if not clips: raise Exception("فشل تحميل الصوت")
    
    final_audio_path = "final.mp3"
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    final_audio.close()
    for c in clips: c.close()
    for f in temp_files: 
        if os.path.exists(f): os.remove(f)
        
    full_text = " ﴿ " + " ﴾ * ﴿ ".join([t for t in ayah_texts if t]) + " ﴾ " if ayah_texts else ""
    info_text = f"🎙️ {reciter_name}  |  📖 {surah_name}"
    return final_audio_path, final_audio.duration, full_text, info_text, reciter_name, surah_name

def make_frame(image_np, text_top, text_bottom, hook_text, cta_text):
    """دالة معالجة الصور المستقرة والسريعة جداً لمنع الـ Exit Code 1 نهائياً"""
    try:
        img = Image.fromarray(image_np)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        try:
            font_quran = ImageFont.truetype(font_path, int(width * 0.045))
            font_sub = ImageFont.truetype(font_path, int(width * 0.035))
            font_hook = ImageFont.truetype(font_path, int(width * 0.05))
        except:
            font_quran = font_sub = font_hook = ImageFont.load_default()
        
        # تأثير التعتيم والظلال الفخم لإبراز الكلمات كالفيديو المرفق
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, 0), (width, height)], fill=(0, 0, 0, 60))
        overlay_draw.rectangle([(0, height // 3), (width, height - 80)], fill=(0, 0, 0, 120))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        # 1. طباعة الـ Hook التسويقي في الثلث العلوي للشاشة لقوة الجذب
        fixed_hook = fix_arabic_text(hook_text)
        w_hook = draw.textlength(fixed_hook, font=font_hook)
        draw.text(((width - w_hook) // 2, int(height * 0.15)), fixed_hook, font=font_hook, fill="#FFD700")

        # 2. طباعة النص القرآني المنسق في المنتصف بدقة
        if text_top:
            words = text_top.split()
            lines, current_line = [], []
            for word in words:
                current_line.append(word)
                if len(" ".join(current_line)) > 24:
                    lines.append(" ".join(current_line[:-1]))
                    current_line = [word]
            lines.append(" ".join(current_line))
            
            y_offset = height // 2 - (len(lines) * 25)
            for line in lines:
                fixed_line = fix_arabic_text(line)
                w = draw.textlength(fixed_line, font=font_quran)
                # رسم تأثير توهج خلفي خفيف (Glow) بلون ذهبي غامق ومميز
                draw.text(((width - w) // 2 + 1, y_offset + 1), fixed_line, font=font_quran, fill="#B8860B")
                draw.text(((width - w) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
                y_offset += int(height * 0.07)

        # 3. شريط المعلومات والـ CTA السفلي الثابت
        fixed_info = fix_arabic_text(text_bottom)
        w_info = draw.textlength(fixed_info, font=font_sub)
        draw.text(((width - w_info) // 2, height - int(height * 0.22)), fixed_info, font=font_sub, fill="#E0E0E0")
        
        fixed_cta = fix_arabic_text(cta_text)
        w_cta = draw.textlength(fixed_cta, font=font_sub)
        draw.text(((width - w_cta) // 2, height - int(height * 0.14)), fixed_cta, font=font_sub, fill="#00FFCC")
        
        return np.array(img)
    except:
        return image_np

def generate_video():
    hooks = ["رسالة لقلبك المتعب 🤍", "قبل أن تنام استمع لها 🌿", "إذا ضاقت بك الدنيا استمع 🏔️", "راحة لروحك المرهقة ✨"]
    ctas = ["اكتب (سبحان الله) وتؤجر ✍️", "شاركها لعلها تشفع لك يوم القيامة 🔄", "صلّ على النبي في التعليقات 🌸"]
    
    chosen_hook = random.choice(hooks)
    chosen_cta = random.choice(ctas)

    audio_path, duration, quran_text, info_text, reciter, surah = get_quran_data()
    
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': random.choice(['mountains', 'river', 'nature']), 'per_page': 10, 'orientation': 'portrait'}
    v_data = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15).json()
    video_url = random.choice(v_data['videos'])['video_files'][0]['link']
    
    with open("v_temp.mp4", "wb") as f: f.write(requests.get(video_url).content)
    
    video_clip = VideoFileClip("v_temp.mp4")
    if video_clip.duration < duration:
        loops = int(duration // video_clip.duration) + 1
        from moviepy.editor import concatenate_videoclips
        video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
    else:
        video_clip = video_clip.subclip(0, duration)

    # التحديث البرمجي الآمن والمعتمد في النسخة الأخيرة لمعالجة مستقرة جداً لكل فريم
    final_clip = video_clip.fl_image(lambda frame: make_frame(frame, quran_text, info_text, chosen_hook, chosen_cta))
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    final_clip.close()
    video_clip.close()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = (
            f"📖 *تلاوة خاشعة يومية* 📖\n\n"
            f"🎙️ القارئ: #{reciter.replace(' ', '_')}\n"
            f"🕌 سورة: #{surah.replace(' ', '_')}\n\n"
            f"◽ ◽ ◽ ◽ ◽ ◽ ◽\n"
            f"📣 {chosen_cta}\n\n"
            f"✨ إنتاج ومونتاج تلقائي خاص بـ: {YOUR_NAME} | #راحة_نفسية #قرآن"
        )
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': video_file})
        
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): os.remove(file)

if __name__ == "__main__":
    generate_video()
