import os
import random
import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, TextClip, CompositeVideoClip
import arabic_reshaper
from bidi.algorithm import get_display

# تعطيل تنبيهات الحماية غير الضرورية في السيرفر
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
        # الدمج الصحيح لإصلاح الحروف المقلوبة في أنظمة لينكس وسيرفرات جيت هاب
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def get_quran_data():
    # اختيار عشوائي بين كبار القراء لضمان التنوع اليومي
    reciter_options = [
        {"id": "Yasser_Ad-Dussary_128kbps", "name": "الشيخ ياسر الدوسري"},
        {"id": "Nasser_Alqatami_128kbps", "name": "الشيخ ناصر القطامي"},
        {"id": "Maher_AlMuaiqly_64kbps", "name": "الشيخ ماهر المعيقلي"}
    ]
    chosen = random.choice(reciter_options)
    reciter_id = chosen["id"]
    reciter_name = chosen["name"]
    
    surah_num = random.randint(1, 114)
    start_ayah = random.randint(1, 15)
    
    try:
        meta_res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}", timeout=15).json()
        surah_name = meta_res['data']['name']
    except:
        surah_name = "سورة من القرآن"
    
    clips = []
    temp_files = []
    ayahs_timeline = [] # مصفوفة لحساب توقيت كل آية بدقة
    
    current_ayah = start_ayah
    current_start_time = 0.0
    
    # جلب 3 آيات متتالية لإنشاء فيديو متناسق ومستمر
    for _ in range(3):
        audio_url = f"https://everyayah.com/data/{reciter_id}/{str(surah_num).zfill(3)}{str(current_ayah).zfill(3)}.mp3"
        try:
            r = requests.get(audio_url, timeout=15, verify=False)
            if r.status_code == 200:
                t_name = f"a_{current_ayah}.mp3"
                with open(t_name, "wb") as f: 
                    f.write(r.content)
                temp_files.append(t_name)
                
                clip = AudioFileClip(t_name).set_fps(44100)
                duration = clip.duration
                clips.append(clip)
                
                # جلب نص الآية الحالية فقط
                try:
                    text_res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{current_ayah}", timeout=15).json()
                    ayah_text = text_res['data']['text']
                except:
                    ayah_text = ""
                
                # تخزين توقيت بداية ونهاية الآية لعرضها في وقتها الصحيح تماماً
                if ayah_text:
                    ayahs_timeline.append({
                        'text': f" ﴿ {ayah_text} ﴾ ",
                        'start': current_start_time,
                        'end': current_start_time + duration
                    })
                
                current_start_time += duration
                current_ayah += 1
                time.sleep(0.5)
            else:
                break
        except:
            break

    if not clips:
        raise Exception("فشل تحميل الصوت من السيرفر الرئيسي")
    
    final_audio_path = "final.mp3"
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(final_audio_path, fps=44100, bitrate="192k", logger=None)
    
    final_audio.close()
    for c in clips: 
        c.close()
    for f in temp_files: 
        if os.path.exists(f): 
            os.remove(f)
        
    info_text = f"🎙️ {reciter_name}  |   mosques {surah_name}"
    return final_audio_path, final_audio.duration, ayahs_timeline, info_text, reciter_name, surah_name

def generate_video():
    hooks = ["رسالة لقلبك المتعب 🤍", "قبل أن تنام استمع لها 🌿", "إذا ضاقت بك الدنيا استمع 🏔️", "راحة لروحك المرهقة ✨"]
    ctas = ["اكتب (سبحان الله) وتؤجر ✍️", "شاركها لعلها تشفع لك يوم القيامة 🔄", "صلّ على النبي في التعليقات 🌸"]
    
    chosen_hook = random.choice(hooks)
    chosen_cta = random.choice(ctas)

    audio_path, total_duration, ayahs_timeline, info_text, reciter, surah = get_quran_data()
    
    # جلب الفيديو الخلفي من Pexels بنقاء عالي وأبعاد طولية مناسبة للجوال
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
    
    # مصفوفة لتجميع طبقات المونتاج الثابتة والمتغيرة
    all_clips = [video_clip]
    
    # 1. تصميم شريط معلومات الشيخ والسورة (ثابت أسفل الشاشة بكتابة صحيحة)
    fixed_info_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw_info = ImageDraw.Draw(fixed_info_img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_sub = ImageFont.truetype(font_path, int(w * 0.038))
        font_hook = ImageFont.truetype(font_path, int(w * 0.045))
    except:
        font_sub = font_hook = ImageFont.load_default()
        
    # تعتيم خلفي خفيف وراقي سينمائي لإبراز الترجمة والنصوص
    draw_info.rectangle([(0, 0), (w, h)], fill=(0, 0, 0, 45))
    draw_info.rectangle([(0, h - 180), (w, h)], fill=(0, 0, 0, 110))
    
    # طباعة اسم الشيخ والسورة في الأسفل
    fixed_info_text = fix_arabic_text(info_text)
    w_info = draw_info.textlength(fixed_info_text, font=font_sub)
    draw_info.text(((w - w_info) // 2, h - 140), fixed_info_text, font=font_sub, fill="#E0E0E0")
    
    # طباعة التفاعل (CTA) في الأسفل تماماً
    fixed_cta_text = fix_arabic_text(chosen_cta)
    w_cta = draw_info.textlength(fixed_cta_text, font=font_sub)
    draw_info.text(((w - w_cta) // 2, h - 70), fixed_cta_text, font=font_sub, fill="#00FFCC")
    
    # طباعة العنوان التسويقي الجاذب (Hook) أعلى الشاشة
    fixed_hook_text = fix_arabic_text(chosen_hook)
    w_hook = draw_info.textlength(fixed_hook_text, font=font_hook)
    draw_info.text(((w - w_hook) // 2, int(h * 0.12)), fixed_hook_text, font=font_hook, fill="#FFD700")
    
    info_overlay = TextClip(txt="", size=(w, h), transparent=True)
    info_overlay_clip = info_overlay.fl_image(lambda image: np.array(Image.alpha_composite(Image.fromarray(image).convert('RGBA'), fixed_info_img).convert('RGB')))
    info_overlay_clip = info_overlay_clip.set_duration(total_duration)
    all_clips.append(info_overlay_clip)

    # 2. المونتاج الذكي: توليد وعرض الآيات تلو الأخرى بشكل متزامن ومنفصل تماماً
    for index, item in enumerate(ayahs_timeline):
        raw_text = item['text']
        
        # تقسيم النص لأسطر قصيرة إذا كانت الآية طويلة لكي لا تخرج عن الشاشة
        words = raw_text.split()
        lines, current_line = [], []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 22:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        # صناعة فريم مخصص للآية الحالية فقط كصورة لحمايتها بنسبة 100% من الانعكاس واللخبطة
        ayah_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw_ayah = ImageDraw.Draw(ayah_img)
        
        try:
            font_quran = ImageFont.truetype(font_path, int(w * 0.052))
        except:
            font_quran = ImageFont.load_default()
            
        y_offset = (h // 2) - (len(lines) * 30)
        for line in lines:
            fixed_line = fix_arabic_text(line)
            w_line = draw_ayah.textlength(fixed_line, font=font_quran)
            # رسم توهج خلفي (Glow) بلون نحاسي دافئ لجمالية الخط الفخم
            draw_ayah.text(((w - w_line) // 2 + 1, y_offset + 1), fixed_line, font=font_quran, fill="#8B6508")
            draw_ayah.text(((w - w_line) // 2, y_offset), fixed_line, font=font_quran, fill="#FFFFFF")
            y_offset += int(h * 0.075)
            
        # دمج الفريم المنفصل للآية وتحديد توقيت ظهوره واختفائه التلقائي مع الصوت
        ayah_base = TextClip(txt="", size=(w, h), transparent=True)
        ayah_clip = ayah_base.fl_image(lambda img: np.array(Image.alpha_composite(Image.fromarray(img).convert('RGBA'), ayah_img).convert('RGB')))
        ayah_clip = ayah_clip.set_start(item['start']).set_end(item['end']).set_pos(("center", "center"))
        all_clips.append(ayah_clip)

    # تركيب جميع الطبقات المتناسقة والآيات المتتابعة فوق بعضها البعض
    final_clip = CompositeVideoClip(all_clips)
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))

    output_filename = "quran_final_pro.mp4"
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    
    # إغلاق الكليبات لتحرير مساحة السيرفر فوراً
    final_clip.close()
    for clip_item in all_clips:
        clip_item.close()
    
    # إرسال الفيديو النهائي النظيف إلى تليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(output_filename, 'rb') as video_file:
        caption = (
            f"📖 *تلاوة خاشعة متزامنة احترافية* 📖\n\n"
            f"🎙️ القارئ: #{reciter.replace(' ', '_')}\n"
            f"🕌 سورة: #{surah.replace(' ', '_')}\n\n"
            f"◽ ◽ ◽ ◽ ◽ ◽ ◽\n"
            f"📣 {chosen_cta}\n\n"
            f"✨ إنتاج ومونتاج تلقائي بالكامل خالي من الأخطاء | #قرآن #راحة_نفسية"
        )
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': video_file})
        
    time.sleep(2)
    for file in ["v_temp.mp4", "final.mp3", output_filename]:
        if os.path.exists(file): 
            os.remove(file)

if __name__ == "__main__":
    generate_video()
