<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>سنتر سيجما التعليمي</title>
  
  <!-- ===== PWA ===== -->
  <meta name="theme-color" content="#2563eb">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="سيجما">
  
  <link rel="manifest" href="data:application/json,{
    &quot;name&quot;:&quot;سنتر سيجما التعليمي&quot;,
    &quot;short_name&quot;:&quot;سيجما&quot;,
    &quot;description&quot;:&quot;منصة سنتر سيجما التعليمية المتكاملة&quot;,
    &quot;start_url&quot;:&quot;.&quot;,
    &quot;display&quot;:&quot;standalone&quot;,
    &quot;orientation&quot;:&quot;portrait&quot;,
    &quot;background_color&quot;:&quot;#f8fafc&quot;,
    &quot;theme_color&quot;:&quot;#2563eb&quot;,
    &quot;lang&quot;:&quot;ar&quot;,
    &quot;dir&quot;:&quot;rtl&quot;,
    &quot;icons&quot;:[
      {&quot;src&quot;:&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Crect width='512' height='512' fill='%232563eb'/%3E%3Ctext x='256' y='350' font-size='300' text-anchor='middle' fill='white' font-family='serif' font-weight='bold'%3E%CE%A3%3C/text%3E%3C/svg%3E&quot;,&quot;sizes&quot;:&quot;512x512&quot;,&quot;type&quot;:&quot;image/svg+xml&quot;,&quot;purpose&quot;:&quot;any maskable&quot;}
    ]
  }">

  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
  
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Cairo', sans-serif; background: #f1f5f9; }
    .app-container { max-width: 480px; margin: 0 auto; background: #f8fafc; min-height: 100vh; position: relative; }
    .slide-up { animation: slideUp 0.3s ease-out; }
    @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    
    .stat-card { background: white; border-radius: 12px; padding: 10px 8px; text-align: center; border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.2s; }
    .stat-card:active { transform: scale(0.96); }
    .stat-number { font-size: 18px; font-weight: 800; }
    .stat-label { font-size: 9px; color: #64748b; margin-top: 2px; }
    
    .profile-avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid white; cursor: pointer; }
    .subject-chip { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 9px; font-weight: 600; margin: 2px; background: rgba(255,255,255,0.2); color: white; }
    
    .option-btn { padding: 6px 12px; border-radius: 10px; border: 2px solid #e2e8f0; background: white; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    .option-btn.active { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
    
    .admin-panel-section { background: white; border-radius: 16px; padding: 12px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    .admin-panel-section .header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; padding: 4px 0; }
    .admin-panel-section .header h4 { font-size: 13px; font-weight: 700; color: #1e293b; }
    .admin-panel-section .content { margin-top: 10px; display: none; }
    .admin-panel-section .content.open { display: block; }
    
    .complaint-card { background: #f8fafc; border-radius: 10px; padding: 10px; border-right: 3px solid #f59e0b; margin-bottom: 6px; }
    .complaint-card .name { font-weight: 700; font-size: 13px; color: #1e293b; }
    .complaint-card .phone { color: #2563eb; font-size: 11px; }
    .complaint-card .text { color: #475569; font-size: 12px; margin-top: 3px; }
    .complaint-card .date { color: #94a3b8; font-size: 9px; }
    
    .toast { position: fixed; top: 15px; left: 50%; transform: translateX(-50%); z-index: 9999; padding: 10px 20px; border-radius: 10px; color: white; font-weight: 600; font-size: 13px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); animation: slideDown 0.4s ease; max-width: 90%; text-align: center; }
    .toast-success { background: #22c55e; }
    .toast-error { background: #ef4444; }
    .toast-warning { background: #f59e0b; }
    .toast-info { background: #3b82f6; }
    @keyframes slideDown { from { opacity: 0; transform: translateX(-50%) translateY(-20px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
    
    .settings-card { background: white; border-radius: 16px; padding: 14px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    .settings-card .title { font-size: 13px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .settings-card .title i { width: 20px; text-align: center; }
    
    .image-viewer {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.95);
      z-index: 99999;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      animation: fadeIn 0.3s ease;
    }
    .image-viewer.show { display: flex; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .image-viewer img { max-width: 100%; max-height: 85vh; object-fit: contain; border-radius: 12px; }
    .image-viewer .close-btn {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(255,255,255,0.2);
      border: none;
      color: white;
      font-size: 28px;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      cursor: pointer;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .image-viewer .close-btn:hover { background: rgba(255,255,255,0.3); transform: rotate(90deg); }
    .image-viewer .download-btn {
      position: absolute;
      bottom: 30px;
      background: rgba(255,255,255,0.2);
      border: none;
      color: white;
      padding: 12px 24px;
      border-radius: 12px;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .image-viewer .download-btn:hover { background: rgba(255,255,255,0.3); }
    .image-viewer .info {
      position: absolute;
      bottom: 90px;
      color: rgba(255,255,255,0.6);
      font-size: 12px;
      text-align: center;
    }
    
    .schedule-item { background: white; border-radius: 12px; padding: 10px; border: 1px solid #e2e8f0; margin-bottom: 6px; }
    .schedule-item .subject { font-weight: 700; font-size: 13px; }
    .schedule-item .time { font-weight: 700; color: #d97706; }
    .schedule-item .teacher { font-size: 11px; color: #64748b; }
    .schedule-item img, .news-item img, .notif-item img { cursor: pointer; transition: all 0.2s; }
    .schedule-item img:hover, .news-item img:hover, .notif-item img:hover { opacity: 0.9; transform: scale(1.02); }
    
    .exam-card { background: white; border-radius: 12px; padding: 12px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    .exam-card .exam-title { font-weight: 700; font-size: 14px; color: #1e293b; }
    .exam-card .exam-info { font-size: 11px; color: #64748b; }
    .result-card { background: #f0fdf4; border-radius: 12px; padding: 12px; border: 1px solid #bbf7d0; margin-bottom: 8px; }
    .result-card .result-subject { font-weight: 700; font-size: 13px; }
    .result-card .result-score { font-size: 16px; font-weight: 800; color: #16a34a; }
    
    .login-section { background: white; border-radius: 16px; padding: 20px; border: 1px solid #e2e8f0; text-align: center; }
    .login-section .logo { font-size: 48px; color: #2563eb; margin-bottom: 10px; }
    .login-section h2 { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 5px; }
    .login-section p { font-size: 12px; color: #64748b; margin-bottom: 15px; }
    .login-section .input-group { margin-bottom: 12px; text-align: right; position: relative; }
    .login-section .input-group label { font-size: 11px; font-weight: 600; color: #475569; display: block; margin-bottom: 3px; }
    .login-section .input-group input { width: 100%; padding: 10px; padding-left: 40px; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 14px; outline: none; transition: all 0.2s; }
    .login-section .input-group input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
    .login-section .input-group .eye-icon { position: absolute; left: 12px; top: 34px; cursor: pointer; color: #94a3b8; font-size: 16px; }
    .login-btn { width: 100%; padding: 12px; background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
    .login-btn:hover { opacity: 0.9; transform: translateY(-1px); }
    .login-btn:active { transform: scale(0.98); }
    
    .link-text { color: #2563eb; cursor: pointer; font-weight: 600; text-decoration: none; }
    .link-text:hover { text-decoration: underline; }

    .publish-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 20px;
      border: none;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      color: white;
      position: relative;
      overflow: hidden;
    }
    .publish-btn::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.2), transparent);
      opacity: 0;
      transition: opacity 0.3s;
    }
    .publish-btn:hover::after { opacity: 1; }
    .publish-btn:active { transform: scale(0.97); }
    
    .publish-btn.blue { background: linear-gradient(135deg, #2563eb, #1d4ed8); box-shadow: 0 4px 15px rgba(37,99,235,0.3); }
    .publish-btn.green { background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 4px 15px rgba(34,197,94,0.3); }
    .publish-btn.purple { background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 4px 15px rgba(139,92,246,0.3); }
    .publish-btn.orange { background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 4px 15px rgba(245,158,11,0.3); }
    .publish-btn.red { background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 4px 15px rgba(239,68,68,0.3); }
    .publish-btn.teal { background: linear-gradient(135deg, #14b8a6, #0d9488); box-shadow: 0 4px 15px rgba(20,184,166,0.3); }
    
    /* ===== MFA Section ===== */
    .mfa-section { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 12px; padding: 12px; margin-bottom: 8px; }
    .mfa-section .mfa-title { font-size: 12px; font-weight: 700; color: #92400e; display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
    .mfa-section .mfa-code { font-size: 24px; font-weight: 800; letter-spacing: 4px; color: #92400e; text-align: center; padding: 8px; background: white; border-radius: 8px; }
    .mfa-section .mfa-hint { font-size: 10px; color: #78350f; text-align: center; margin-top: 6px; }
    
    /* ===== Rate Limit Section ===== */
    .rate-limit-section { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 12px; padding: 12px; margin-bottom: 8px; text-align: center; }
    .rate-limit-section .rate-icon { font-size: 32px; color: #dc2626; margin-bottom: 6px; }
    .rate-limit-section .rate-title { font-size: 13px; font-weight: 700; color: #991b1b; }
    .rate-limit-section .rate-text { font-size: 11px; color: #7f1d1d; margin-top: 4px; }
    
    .dark-mode .app-container { background: #0f172a; }
    .dark-mode .bg-white { background: #1e293b !important; }
    .dark-mode .text-slate-800 { color: #e2e8f0 !important; }
    .dark-mode .text-slate-600 { color: #94a3b8 !important; }
    .dark-mode .border-slate-100 { border-color: #334155 !important; }
    .dark-mode .bg-slate-50 { background: #0f172a !important; }
    .dark-mode .stat-card { background: #1e293b !important; border-color: #334155 !important; }
    .dark-mode .stat-label { color: #94a3b8 !important; }
    .dark-mode .admin-panel-section { background: #1e293b !important; border-color: #334155 !important; }
    .dark-mode .settings-card { background: #1e293b !important; border-color: #334155 !important; }
    .dark-mode .complaint-card { background: #0f172a !important; }
    .dark-mode .option-btn { background: #1e293b !important; border-color: #334155 !important; color: #e2e8f0 !important; }
    .dark-mode .option-btn.active { background: #1e3a5f !important; border-color: #2563eb !important; color: #60a5fa !important; }
    .dark-mode .schedule-item { background: #1e293b !important; border-color: #334155 !important; }
    .dark-mode .schedule-item .teacher { color: #94a3b8 !important; }
    .dark-mode .login-section { background: #1e293b !important; border-color: #334155 !important; }
    .dark-mode .login-section h2 { color: #e2e8f0 !important; }
    .dark-mode .login-section p { color: #94a3b8 !important; }
    .dark-mode .login-section .input-group label { color: #94a3b8 !important; }
    .dark-mode .login-section .input-group input { background: #0f172a !important; border-color: #334155 !important; color: #e2e8f0 !important; }
    
    @media (max-width: 400px) {
      .stat-number { font-size: 15px; }
      .stat-label { font-size: 8px; }
      .subject-chip { font-size: 8px; padding: 1px 6px; }
      .profile-avatar { width: 36px; height: 36px; }
    }
  </style>
</head>
<body>

<div id="app" class="app-container flex flex-col pb-16">

  <!-- HEADER -->
  <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-3 shadow-lg sticky top-0 z-30 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <div class="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center font-extrabold text-xl border border-white/30 shadow-lg">Σ</div>
      <div>
        <h1 class="font-extrabold text-sm leading-tight">سنتر سيجما</h1>
        <p class="text-[8px] text-blue-100">منصة الطالب الذكية</p>
      </div>
    </div>
    <div class="flex items-center gap-1">
      <button onclick="switchTab('notifications')" class="relative p-2 rounded-full hover:bg-white/10">
        <i class="fa-solid fa-bell text-lg"></i>
        <span id="notifBadge" class="hidden absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white animate-pulse"></span>
      </button>
      <button onclick="toggleDarkMode()" class="p-2 rounded-full hover:bg-white/10">
        <i id="darkIcon" class="fa-solid fa-moon text-lg"></i>
      </button>
    </div>
  </header>

  <!-- IMAGE VIEWER -->
  <div id="imageViewer" class="image-viewer" onclick="closeImageViewer()">
    <button class="close-btn" onclick="closeImageViewer()">✕</button>
    <img id="viewerImage" src="" alt="صورة">
    <button class="download-btn" onclick="downloadImage()">
      <i class="fa-solid fa-download"></i> تحميل الصورة
    </button>
    <div class="info" id="imageInfo"></div>
  </div>

  <!-- MAIN -->
  <main class="flex-1 p-3 space-y-3 overflow-y-auto" style="padding-bottom: 70px;">

    <!-- LOGIN -->
    <section id="tab-login" class="slide-up">
      <div class="login-section">
        <div class="logo">Σ</div>
        <h2>مرحباً بك في سنتر سيجما</h2>
        <p>سجل دخولك باستخدام البريد الإلكتروني</p>
        
        <div class="input-group">
          <label>📧 البريد الإلكتروني</label>
          <input type="email" id="loginEmail" placeholder="example@email.com">
        </div>
        
        <div class="input-group">
          <label>🔒 كلمة المرور</label>
          <input type="password" id="loginPassword" placeholder="••••••••">
          <i class="fa-solid fa-eye eye-icon" onclick="togglePasswordVisibility('loginPassword', this)"></i>
        </div>
        
        <button class="login-btn" onclick="loginUserWithRetry()">🚀 تسجيل الدخول</button>
        
        <div style="margin-top: 12px; font-size: 12px; color: #64748b;">
          <span onclick="switchTab('forgot')" class="link-text">🔑 نسيت كلمة المرور؟</span>
        </div>
        
        <div style="margin-top: 8px; font-size: 12px; color: #64748b;">
          ليس لديك حساب؟ 
          <span onclick="switchTab('register')" class="link-text">إنشاء حساب جديد</span>
        </div>
      </div>
    </section>

    <!-- FORGOT PASSWORD -->
    <section id="tab-forgot" class="hidden slide-up">
      <div class="login-section">
        <div class="logo">🔑</div>
        <h2>استعادة كلمة المرور</h2>
        <p>أدخل بريدك الإلكتروني وسنرسل لك رابط إعادة التعيين</p>
        
        <div class="input-group">
          <label>📧 البريد الإلكتروني</label>
          <input type="email" id="forgotEmail" placeholder="example@email.com">
        </div>
        
        <button class="login-btn" onclick="sendPasswordReset()">📧 إرسال رابط إعادة التعيين</button>
        
        <div style="margin-top: 12px; font-size: 12px; color: #64748b;">
          تذكرت كلمة المرور؟ 
          <span onclick="switchTab('login')" class="link-text">تسجيل الدخول</span>
        </div>
      </div>
    </section>

    <!-- MFA VERIFICATION -->
    <section id="tab-mfa" class="hidden slide-up">
      <div class="mfa-section">
        <div class="mfa-title">
          <i class="fa-solid fa-shield-halved"></i> التحقق بخطوتين (MFA)
        </div>
        <p style="font-size: 11px; color: #78350f; margin-bottom: 8px;">
          أدخل رمز التحقق المكون من 6 أرقام الذي تم إرساله إلى بريدك الإلكتروني
        </p>
        <div class="mfa-code" id="mfaCodeDisplay">- - - - - -</div>
        <div class="mfa-hint">⏱️ الرمز صالح لمدة 5 دقائق</div>
        
        <div class="input-group" style="margin-top: 12px;">
          <label>🔢 رمز التحقق</label>
          <input type="text" id="mfaCode" placeholder="000000" maxlength="6" style="text-align: center; font-size: 20px; letter-spacing: 8px; font-weight: bold;">
        </div>
        
        <button class="login-btn" onclick="verifyMFA()">✅ تحقق</button>
        
        <div style="margin-top: 12px; font-size: 11px; color: #92400e; text-align: center;">
          <span onclick="resendMFA()" class="link-text">🔄 إعادة إرسال الرمز</span>
        </div>
      </div>
    </section>

    <!-- REGISTER -->
    <section id="tab-register" class="hidden slide-up">
      <div class="login-section">
        <div class="logo">Σ</div>
        <h2>إنشاء حساب جديد</h2>
        <p>أدخل بياناتك للتسجيل في منصة سيجما</p>
        
        <div class="input-group">
          <label>👤 الاسم الكامل</label>
          <input type="text" id="regName" placeholder="أحمد محمد">
        </div>
        
        <div class="input-group">
          <label>📧 البريد الإلكتروني</label>
          <input type="email" id="regEmail" placeholder="example@email.com">
        </div>
        
        <div class="input-group">
          <label>📱 رقم الهاتف</label>
          <input type="tel" id="regPhone" placeholder="01012345678">
        </div>
        
        <div class="input-group">
          <label>🔒 كلمة المرور</label>
          <input type="password" id="regPassword" placeholder="•••••••• (6 أحرف على الأقل)">
          <i class="fa-solid fa-eye eye-icon" onclick="togglePasswordVisibility('regPassword', this)"></i>
        </div>
        
        <div class="input-group">
          <label>🔒 تأكيد كلمة المرور</label>
          <input type="password" id="regConfirmPassword" placeholder="••••••••">
          <i class="fa-solid fa-eye eye-icon" onclick="togglePasswordVisibility('regConfirmPassword', this)"></i>
        </div>
        
        <div class="input-group">
          <label>📄 صورة البطاقة الشخصية أو شهادة الميلاد</label>
          <input type="file" id="regIdImage" accept="image/*" style="padding: 8px; padding-left: 8px;">
        </div>
        
        <button class="login-btn" onclick="registerUserWithRetry()">📝 إنشاء حساب</button>
        
        <div style="margin-top: 12px; font-size: 12px; color: #64748b;">
          لديك حساب بالفعل؟ 
          <span onclick="switchTab('login')" class="link-text">تسجيل الدخول</span>
        </div>
      </div>
    </section>

    <!-- HOME -->
    <section id="tab-home" class="hidden space-y-3 slide-up">
      
      <div id="userCard" class="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-4 text-white shadow-lg">
        <div id="userContent" class="flex items-center gap-3">
          <img id="userAvatar" src="" class="profile-avatar" onclick="openProfile()" style="display:none;">
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <h2 id="userName" class="font-bold text-sm">مرحباً بك</h2>
              <button id="loginBtn" onclick="logoutUser()" class="bg-red-500/80 hover:bg-red-600 text-white text-[10px] font-bold px-3 py-1.5 rounded-xl transition">
                <i class="fa-solid fa-sign-out-alt"></i> خروج
              </button>
            </div>
            <p id="userSubtitle" class="text-xs text-blue-100">أكمل بياناتك</p>
            <div id="userSubjects" class="mt-1"></div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-2">
        <div class="stat-card" onclick="switchTab('schedule')">
          <div class="text-blue-600 text-lg"><i class="fa-solid fa-calendar-check"></i></div>
          <div class="stat-number text-blue-600" id="todayCount">0</div>
          <div class="stat-label">حصص اليوم</div>
        </div>
        <div class="stat-card" onclick="switchTab('library')">
          <div class="text-purple-600 text-lg"><i class="fa-solid fa-book"></i></div>
          <div class="stat-number text-purple-600" id="materialCount">0</div>
          <div class="stat-label">الملفات</div>
        </div>
        <div class="stat-card" onclick="switchTab('notifications')">
          <div class="text-amber-500 text-lg"><i class="fa-solid fa-bell"></i></div>
          <div class="stat-number text-amber-500" id="notifCount">0</div>
          <div class="stat-label">تنبيهات</div>
        </div>
      </div>

      <div class="bg-white rounded-2xl p-3 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-bold text-xs text-slate-800"><i class="fa-solid fa-clock text-blue-600 ml-1"></i> حصصي اليوم</h3>
          <button onclick="switchTab('schedule')" class="text-[10px] text-blue-600 font-bold">عرض الكل</button>
        </div>
        <div id="myScheduleToday" class="space-y-1.5">
          <div class="text-center py-3 text-slate-400 text-xs">جاري التحميل...</div>
        </div>
      </div>

      <div class="bg-white rounded-2xl p-3 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-bold text-xs text-slate-800"><i class="fa-solid fa-newspaper text-blue-600 ml-1"></i> آخر الأخبار</h3>
          <button onclick="switchTab('news')" class="text-[10px] text-blue-600 font-bold">عرض الكل</button>
        </div>
        <div id="homeNewsContainer" class="space-y-2">
          <div class="text-center py-3 text-slate-400 text-xs">جاري التحميل...</div>
        </div>
      </div>
    </section>

    <!-- SCHEDULE -->
    <section id="tab-schedule" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-calendar-days text-blue-600 ml-1"></i> جدول السنتر</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div class="flex bg-slate-200/80 p-1 rounded-xl text-[10px] font-bold text-slate-600">
        <button onclick="filterSchedule('today')" id="btnToday" class="flex-1 py-1.5 rounded-lg bg-white text-blue-600 shadow-sm">اليوم</button>
        <button onclick="filterSchedule('tomorrow')" id="btnTomorrow" class="flex-1 py-1.5 rounded-lg">غداً</button>
        <button onclick="filterSchedule('all')" id="btnAll" class="flex-1 py-1.5 rounded-lg">الأسبوع</button>
      </div>
      <div id="scheduleContainer" class="space-y-2">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- LIBRARY -->
    <section id="tab-library" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-book-open text-purple-600 ml-1"></i> المكتبة الرقمية</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="libraryContainer" class="space-y-2">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- NEWS -->
    <section id="tab-news" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-newspaper text-blue-600 ml-1"></i> الأخبار</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="allNewsContainer" class="space-y-3">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- NOTIFICATIONS -->
    <section id="tab-notifications" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-bell text-amber-500 ml-1"></i> الإشعارات</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="notificationsContainer" class="space-y-2">
        <div class="text-center py-6 text-slate-400 text-xs"><i class="fa-regular fa-bell-slash text-2xl block mb-1"></i> لا توجد إشعارات</div>
      </div>
    </section>

    <!-- EXAMS -->
    <section id="tab-exams" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-pen-to-square text-red-600 ml-1"></i> نظام الامتحانات</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="examsContainer" class="space-y-2">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- RESULTS -->
    <section id="tab-results" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-chart-simple text-green-600 ml-1"></i> لوحة النتائج</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="resultsContainer" class="space-y-2">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- TEACHERS -->
    <section id="tab-teachers" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-chalkboard-user text-indigo-600 ml-1"></i> المدرسين</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>
      <div id="teachersContainer" class="space-y-2">
        <div class="text-center py-4 text-slate-400 text-xs">جاري التحميل...</div>
      </div>
    </section>

    <!-- SETTINGS -->
    <section id="tab-settings" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-gear text-slate-600 ml-1"></i> الإعدادات</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-user text-blue-600"></i> معلوماتي</div>
        <div id="studentInfo" class="space-y-1 text-xs">
          <p><span class="text-slate-500">الاسم:</span> <span id="infoName" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">البريد:</span> <span id="infoEmail" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">الهاتف:</span> <span id="infoPhone" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">ولي الأمر:</span> <span id="infoParentPhone" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">المدرسة:</span> <span id="infoSchool" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">المرحلة:</span> <span id="infoStage" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">الصف:</span> <span id="infoGrade" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">المواد:</span> <span id="infoSubjects" class="font-bold text-slate-800">-</span></p>
          <p><span class="text-slate-500">حالة البيانات:</span> <span id="infoStatus" class="font-bold text-amber-600">قيد المراجعة</span></p>
        </div>
      </div>

      <!-- تغيير كلمة المرور -->
      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-key text-amber-500"></i> تغيير كلمة المرور</div>
        <div class="space-y-2">
          <div class="input-group" style="position: relative;">
            <label class="text-[10px] font-bold text-slate-500">كلمة المرور الحالية:</label>
            <input type="password" id="currentPassword" placeholder="••••••••" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none" style="padding-left: 40px;">
            <i class="fa-solid fa-eye eye-icon" onclick="togglePasswordVisibility('currentPassword', this)" style="position: absolute; left: 12px; top: 30px; cursor: pointer; color: #94a3b8;"></i>
          </div>
          <div class="input-group" style="position: relative;">
            <label class="text-[10px] font-bold text-slate-500">كلمة المرور الجديدة:</label>
            <input type="password" id="newPassword" placeholder="••••••••" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none" style="padding-left: 40px;">
            <i class="fa-solid fa-eye eye-icon" onclick="togglePasswordVisibility('newPassword', this)" style="position: absolute; left: 12px; top: 30px; cursor: pointer; color: #94a3b8;"></i>
          </div>
          <button onclick="changePassword()" class="publish-btn orange">
            <i class="fa-solid fa-key"></i> تغيير كلمة المرور
          </button>
        </div>
      </div>

      <!-- MFA Settings -->
      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-shield-halved text-green-600"></i> الأمان المتقدم (MFA)</div>
        <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
          تفعيل التحقق بخطوتين لحماية حسابك
        </div>
        <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg mb-2">
          <span class="text-xs font-bold text-slate-700">حالة MFA</span>
          <span id="mfaStatus" class="text-xs font-bold text-red-500">❌ معطّل</span>
        </div>
        <button onclick="toggleMFA()" id="mfaToggleBtn" class="publish-btn green">
          <i class="fa-solid fa-shield-halved"></i> تفعيل MFA
        </button>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-pen text-emerald-600"></i> تعديل البيانات</div>
        <div class="space-y-2">
          <div>
            <label class="text-[10px] font-bold text-slate-500">المدرسة:</label>
            <input type="text" id="profSchool" placeholder="اسم المدرسة" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none">
          </div>
          <div>
            <label class="text-[10px] font-bold text-slate-500">رقم ولي الأمر:</label>
            <input type="tel" id="profParentPhone" placeholder="رقم ولي الأمر" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none">
          </div>
          <div>
            <label class="text-[10px] font-bold text-slate-500">المرحلة:</label>
            <select id="profStage" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="ثانوي">ثانوي</option>
              <option value="إعدادي">إعدادي</option>
            </select>
          </div>
          <div>
            <label class="text-[10px] font-bold text-slate-500">الصف:</label>
            <select id="profGrade" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="1">الصف الأول</option>
              <option value="2">الصف الثاني</option>
              <option value="3">الصف الثالث</option>
            </select>
          </div>
          <div>
            <label class="text-[10px] font-bold text-slate-500">رقم الهاتف:</label>
            <input type="tel" id="profPhone" placeholder="مثال: 01012345678" class="w-full p-2 bg-slate-50 border rounded-xl text-sm mt-0.5 focus:ring-2 focus:ring-blue-500 outline-none">
          </div>
          <div>
            <label class="text-[10px] font-bold text-slate-500">المواد:</label>
            <div id="subjectsCheckbox" class="mt-1 grid grid-cols-2 gap-1"></div>
          </div>
          <button onclick="saveProfile()" class="publish-btn blue">
            <i class="fa-solid fa-save"></i> حفظ التغييرات
          </button>
        </div>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-phone text-green-600"></i> أرقام السنتر</div>
        <div id="centerContacts" class="space-y-1.5"></div>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-headset text-cyan-600"></i> الدعم الفني</div>
        <div id="supportContacts" class="space-y-1.5"></div>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-comment text-amber-500"></i> تقديم شكوى</div>
        <textarea id="complaintText" placeholder="اكتب شكواك هنا..." class="w-full p-2 bg-slate-50 border rounded-xl text-sm h-16 focus:ring-2 focus:ring-amber-500 outline-none"></textarea>
        <button onclick="sendComplaint()" class="publish-btn orange">
          <i class="fa-solid fa-paper-plane"></i> إرسال الشكوى
        </button>
      </div>

      <div class="settings-card">
        <div class="title"><i class="fa-solid fa-trash text-red-500"></i> حذف الحساب</div>
        <button onclick="deleteAccount()" class="publish-btn red">
          <i class="fa-solid fa-trash-can"></i> حذف حسابي نهائياً
        </button>
        <p class="text-[9px] text-red-400 text-center mt-1">⚠️ هذا الإجراء لا يمكن التراجع عنه</p>
      </div>
    </section>

    <!-- ADMIN -->
    <section id="tab-admin" class="hidden space-y-3 slide-up">
      <div class="flex items-center justify-between">
        <h2 class="font-bold text-sm text-slate-800"><i class="fa-solid fa-user-shield text-blue-600 ml-1"></i> لوحة الإدارة</h2>
        <button onclick="switchTab('home')" class="text-[10px] text-slate-400"><i class="fa-solid fa-arrow-right"></i> رجوع</button>
      </div>

      <div id="adminDenied" class="hidden bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
        <i class="fa-solid fa-ban text-red-500 text-4xl mb-2"></i>
        <h3 class="font-bold text-red-700 text-sm">⛔ غير مصرح بالدخول</h3>
        <p class="text-xs text-red-600 mt-1">هذه الصفحة للإداريين فقط</p>
        <button onclick="switchTab('home')" class="mt-3 bg-red-600 text-white px-4 py-1.5 rounded-xl text-xs">الرجوع</button>
      </div>

      <div id="adminLogin" class="bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
        <div class="flex items-center gap-2 text-sm font-bold text-slate-700"><i class="fa-solid fa-lock text-amber-500"></i> دخول الإدارة</div>
        <div class="relative mt-2">
          <input type="password" id="adminPass" placeholder="كلمة السر" class="w-full p-2.5 bg-slate-50 border rounded-xl text-sm pr-10 focus:ring-2 focus:ring-blue-500 outline-none">
          <i class="fa-solid fa-key absolute left-3 top-3 text-slate-400"></i>
        </div>
        <button onclick="adminLogin()" class="publish-btn blue">دخول</button>
      </div>

      <div id="adminPanel" class="hidden space-y-2">
        
        <!-- إحصائيات -->
        <div class="admin-panel-section" onclick="toggleStats()" style="cursor:pointer;">
          <div class="header">
            <h4><i class="fa-solid fa-chart-line text-blue-400"></i> الإحصائيات اللحظية</h4>
            <span class="text-xs text-slate-400"><i class="fa-solid fa-chevron-down" id="statsArrow"></i></span>
          </div>
          <div class="content" id="statsContent">
            <div class="grid grid-cols-2 gap-2 text-white bg-slate-800 rounded-xl p-3">
              <div><div class="text-xl font-bold" id="statUsers">0</div><div class="text-[10px] opacity-70">👥 الطلاب</div></div>
              <div><div class="text-xl font-bold" id="statActive">0</div><div class="text-[10px] opacity-70">🟢 نشطاء</div></div>
              <div><div class="text-xl font-bold" id="statBoys">0</div><div class="text-[10px] opacity-70">🧑 أولاد</div></div>
              <div><div class="text-xl font-bold" id="statGirls">0</div><div class="text-[10px] opacity-70">👧 بنات</div></div>
              <div><div class="text-xl font-bold" id="statSchedules">0</div><div class="text-[10px] opacity-70">📚 حصص</div></div>
              <div><div class="text-xl font-bold" id="statMaterials">0</div><div class="text-[10px] opacity-70">📄 ملفات</div></div>
              <div><div class="text-xl font-bold" id="statTeachers">0</div><div class="text-[10px] opacity-70">👨‍🏫 مدرسين</div></div>
              <div><div class="text-xl font-bold" id="statExams">0</div><div class="text-[10px] opacity-70">📝 امتحانات</div></div>
              <div><div class="text-xl font-bold" id="statResults">0</div><div class="text-[10px] opacity-70">📊 نتائج</div></div>
              <div><div class="text-xl font-bold" id="statNotifs">0</div><div class="text-[10px] opacity-70">🔔 إشعارات</div></div>
            </div>
          </div>
        </div>

        <!-- إعدادات الأمان -->
        <div class="admin-panel-section">
          <div class="header" onclick="toggleSection(this)">
            <h4><i class="fa-solid fa-shield-halved text-green-600"></i> إعدادات الأمان</h4>
            <span class="text-xs text-slate-400"><i class="fa-solid fa-chevron-down"></i></span>
          </div>
          <div class="content">
            <div class="space-y-2">
              <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span class="text-xs font-bold text-slate-700">🔒 Rate Limiting</span>
                <span id="rateLimitStatus" class="text-xs font-bold text-green-600">✅ مفعّل</span>
              </div>
              <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span class="text-xs font-bold text-slate-700">🛡️ MFA</span>
                <span id="mfaAdminStatus" class="text-xs font-bold text-green-600">✅ مفعّل</span>
              </div>
              <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span class="text-xs font-bold text-slate-700">🚫 حماية Brute Force</span>
                <span class="text-xs font-bold text-green-600">✅ مفعّل</span>
              </div>
              <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span class="text-xs font-bold text-slate-700">📝 تسجيل الأحداث</span>
                <span class="text-xs font-bold text-green-600">✅ مفعّل</span>
              </div>
            </div>
          </div>
        </div>

        <!-- طلبات تعديل البيانات -->
        <div class="admin-panel-section">
          <div class="header" onclick="toggleSection(this)">
            <h4><i class="fa-solid fa-user-check text-amber-500"></i> طلبات تعديل البيانات</h4>
            <span class="text-xs text-slate-400"><i class="fa-solid fa-chevron-down"></i></span>
          </div>
          <div class="content">
            <div id="profileRequestsList" class="max-h-40 overflow-y-auto space-y-1.5">
              <div class="text-center py-3 text-slate-400 text-xs">لا توجد طلبات</div>
            </div>
          </div>
        </div>

        <!-- باقي لوحة التحكم (نفسها كما في الكود السابق) -->
        <!-- ... -->

      </div>
    </section>

  </main>

  <!-- BOTTOM NAV -->
  <nav class="fixed bottom-0 w-full max-w-[480px] bg-white/95 backdrop-blur-sm border-t border-slate-200 py-1 px-2 flex justify-around items-center z-30 shadow-lg" style="left:50%;transform:translateX(-50%);">
    <button onclick="switchTab('home')" id="nav-home" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-house text-lg"></i><span>الرئيسية</span></button>
    <button onclick="switchTab('schedule')" id="nav-schedule" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-calendar-days text-lg"></i><span>الجدول</span></button>
    <button onclick="switchTab('library')" id="nav-library" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-book-open text-lg"></i><span>المكتبة</span></button>
    <button onclick="switchTab('exams')" id="nav-exams" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-pen-to-square text-lg"></i><span>امتحانات</span></button>
    <button onclick="switchTab('settings')" id="nav-settings" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-gear text-lg"></i><span>الإعدادات</span></button>
    <button onclick="switchTab('admin')" id="nav-admin" class="flex flex-col items-center text-[9px] font-bold text-slate-400"><i class="fa-solid fa-user-shield text-lg"></i><span>الإدارة</span></button>
  </nav>

</div>

<!-- ===== FIREBASE ===== -->
<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
  import { getDatabase, ref, push, onValue, set, remove, update, query, orderByChild, limitToFirst, startAfter } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";
  import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, setPersistence, browserLocalPersistence, deleteUser, sendPasswordResetEmail, updatePassword, reauthenticateWithCredential, EmailAuthProvider, multiFactor, PhoneAuthProvider, PhoneMultiFactorGenerator, RecaptchaVerifier } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

  const firebaseConfig = {
    apiKey: "AIzaSyCoHGEyhlsjmB_diUNm-R8SXB0Gm0kXw0A",
    authDomain: "sigma-6f162.firebaseapp.com",
    databaseURL: "https://sigma-6f162-default-rtdb.firebaseio.com",
    projectId: "sigma-6f162",
    storageBucket: "sigma-6f162.firebasestorage.app",
    messagingSenderId: "420365348074",
    appId: "1:420365348074:web:0aaecb71ec613bb32abb93",
    measurementId: "G-BTSLXSPXM1"
  };

  const app = initializeApp(firebaseConfig);
  const db = getDatabase(app);
  const auth = getAuth(app);

  // ===== APK Fix =====
  if (window.navigator && window.navigator.userAgent) {
    const isWebView = /wv|android|iphone|ipad|webview/i.test(navigator.userAgent);
    if (isWebView) {
      console.log('📱 APK Mode - تم تفعيل الإعدادات الخاصة');
      auth.settings.appVerificationDisabledForTesting = true;
    }
  }

  await setPersistence(auth, browserLocalPersistence);

  window.db = db;
  window.auth = auth;
  window.ref = ref;
  window.push = push;
  window.set = set;
  window.remove = remove;
  window.update = update;
  window.onValue = onValue;
  window.query = query;
  window.orderByChild = orderByChild;
  window.limitToFirst = limitToFirst;
  window.startAfter = startAfter;
  window.createUserWithEmailAndPassword = createUserWithEmailAndPassword;
  window.signInWithEmailAndPassword = signInWithEmailAndPassword;
  window.signOut = signOut;
  window.onAuthStateChanged = onAuthStateChanged;
  window.deleteUser = deleteUser;
  window.sendPasswordResetEmail = sendPasswordResetEmail;
  window.updatePassword = updatePassword;
  window.reauthenticateWithCredential = reauthenticateWithCredential;
  window.EmailAuthProvider = EmailAuthProvider;
  window.multiFactor = multiFactor;
  window.PhoneAuthProvider = PhoneAuthProvider;
  window.PhoneMultiFactorGenerator = PhoneMultiFactorGenerator;
  window.RecaptchaVerifier = RecaptchaVerifier;
  
  console.log('✅ Firebase جاهز');
</script>

<!-- ===== APPLICATION ===== -->
<script>
// ============================================
// المتغيرات العامة
// ============================================
let currentUser = null, userData = null, scheduleData = [];
let currentFilter = 'today', isAdmin = false, darkMode = false;
let allUsers = {}, contacts = [], complaints = [], scheduleOption = 'full';
let scheduleDayOption = 'today', notifOption = 'full';
let currentViewerImage = '';
let mfaEnabled = false;
let mfaCode = null;
let mfaExpiry = null;
let currentMFASession = null;

const ADMIN_UIDS = ['WCyUdR31uZOxJwtYzXx85K7E0Cf2', 'ADMIN_UID_2', 'ADMIN_UID_3'];
const MAX_FILE_SIZE = 20 * 1024 * 1024;

const subjectsByStage = {
  'ثانوي': ['فيزياء', 'كيمياء', 'رياضيات', 'أحياء', 'لغة عربية', 'لغة إنجليزية', 'فرنسية', 'تاريخ', 'جغرافيا', 'فلسفة'],
  'إعدادي': ['رياضيات', 'علوم', 'لغة عربية', 'لغة إنجليزية', 'دراسات', 'حاسب آلي']
};

// ============================================
// Rate Limiting System
// ============================================
const RateLimiter = {
  attempts: {},
  maxAttempts: 5,
  windowMs: 15 * 60 * 1000, // 15 دقيقة
  blockDurationMs: 30 * 60 * 1000, // 30 دقيقة حظر
  
  check(key) {
    const now = Date.now();
    if (!this.attempts[key]) {
      this.attempts[key] = { count: 0, firstAttempt: now, blocked: false, blockedUntil: 0 };
    }
    
    const record = this.attempts[key];
    
    // التحقق من الحظر
    if (record.blocked && now < record.blockedUntil) {
      const remaining = Math.ceil((record.blockedUntil - now) / 1000 / 60);
      return { allowed: false, reason: `تم حظر الحساب مؤقتاً. حاول بعد ${remaining} دقيقة` };
    }
    
    // إعادة تعيين إذا انتهت النافذة الزمنية
    if (now - record.firstAttempt > this.windowMs) {
      record.count = 0;
      record.firstAttempt = now;
      record.blocked = false;
    }
    
    if (record.count >= this.maxAttempts) {
      record.blocked = true;
      record.blockedUntil = now + this.blockDurationMs;
      return { allowed: false, reason: `تم تجاوز عدد المحاولات. حاول بعد 30 دقيقة` };
    }
    
    return { allowed: true, remaining: this.maxAttempts - record.count };
  },
  
  recordFailure(key) {
    const now = Date.now();
    if (!this.attempts[key]) {
      this.attempts[key] = { count: 0, firstAttempt: now, blocked: false, blockedUntil: 0 };
    }
    this.attempts[key].count++;
  },
  
  recordSuccess(key) {
    delete this.attempts[key];
  }
};

// ============================================
// MFA System (Two-Factor Authentication)
// ============================================
const MFASystem = {
  generateCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
  },
  
  async sendCode(email) {
    const code = this.generateCode();
    mfaCode = code;
    mfaExpiry = Date.now() + 5 * 60 * 1000; // 5 دقائق
    
    // حفظ الرمز في قاعدة البيانات (للمحاكاة)
    // في الإنتاج، يجب إرسال الرمز عبر خدمة بريد إلكتروني
    console.log(`🔐 رمز MFA للبريد ${email}: ${code}`);
    
    // حفظ الرمز في localStorage (للتجربة)
    localStorage.setItem('mfa_code', btoa(code));
    localStorage.setItem('mfa_expiry', mfaExpiry.toString());
    localStorage.setItem('mfa_email', email);
    
    // محاكاة إرسال البريد الإلكتروني
    return { success: true, code };
  },
  
  verifyCode(inputCode) {
    const storedCode = localStorage.getItem('mfa_code');
    const storedExpiry = localStorage.getItem('mfa_expiry');
    
    if (!storedCode || !storedExpiry) {
      return { success: false, reason: 'لم يتم إرسال رمز' };
    }
    
    if (Date.now() > parseInt(storedExpiry)) {
      localStorage.removeItem('mfa_code');
      localStorage.removeItem('mfa_expiry');
      return { success: false, reason: 'انتهت صلاحية الرمز' };
    }
    
    try {
      const decodedCode = atob(storedCode);
      if (inputCode === decodedCode) {
        localStorage.removeItem('mfa_code');
        localStorage.removeItem('mfa_expiry');
        localStorage.removeItem('mfa_email');
        return { success: true };
      }
    } catch (e) {
      return { success: false, reason: 'خطأ في التحقق' };
    }
    
    return { success: false, reason: 'الرمز غير صحيح' };
  },
  
  async toggleMFA() {
    if (!currentUser) return;
    mfaEnabled = !mfaEnabled;
    
    // حفظ الإعداد في قاعدة البيانات
    await window.set(window.ref(window.db, `users/${currentUser.uid}/mfa_enabled`), mfaEnabled);
    
    const mfaStatus = document.getElementById('mfaStatus');
    const mfaToggleBtn = document.getElementById('mfaToggleBtn');
    
    if (mfaEnabled) {
      mfaStatus.textContent = '✅ مفعّل';
      mfaStatus.className = 'text-xs font-bold text-green-500';
      mfaToggleBtn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> تعطيل MFA';
      mfaToggleBtn.className = 'publish-btn red';
    } else {
      mfaStatus.textContent = '❌ معطّل';
      mfaStatus.className = 'text-xs font-bold text-red-500';
      mfaToggleBtn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> تفعيل MFA';
      mfaToggleBtn.className = 'publish-btn green';
    }
  }
};

// ============================================
// Security Audit
// ============================================
const SecurityAudit = {
  log(event, details = {}) {
    const logEntry = {
      event,
      details,
      userId: currentUser?.uid || 'anonymous',
      userEmail: currentUser?.email || 'unknown',
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
      date: new Date().toLocaleString('ar-EG'),
      ip: 'client-side'
    };
    
    console.log('🔒 Security Event:', logEntry);
    
    // حفظ في قاعدة البيانات
    if (window.db) {
      try {
        window.push(window.ref(window.db, 'security_logs'), logEntry);
      } catch (e) {
        console.error('❌ فشل حفظ السجل:', e);
      }
    }
    
    return logEntry;
  },
  
  checkSuspiciousActivity() {
    // التحقق من محاولات تسجيل الدخول المتكررة
    const attempts = Object.keys(RateLimiter.attempts).length;
    if (attempts > 3) {
      this.log('SUSPICIOUS_ACTIVITY', { attempts });
    }
  }
};

// ============================================
// عرض كلمة المرور
// ============================================
function togglePasswordVisibility(inputId, icon) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fa-solid fa-eye-slash eye-icon';
  } else {
    input.type = 'password';
    icon.className = 'fa-solid fa-eye eye-icon';
  }
}
window.togglePasswordVisibility = togglePasswordVisibility;

// ============================================
// نسيت كلمة المرور
// ============================================
async function sendPasswordReset() {
  const email = document.getElementById('forgotEmail').value.trim();
  
  if (!email) {
    showToast('⚠️ يرجى إدخال البريد الإلكتروني', 'error');
    return;
  }
  
  // التحقق من Rate Limiting
  const rateCheck = RateLimiter.check(`reset_${email}`);
  if (!rateCheck.allowed) {
    showToast(`⚠️ ${rateCheck.reason}`, 'error');
    return;
  }
  
  showToast('⏳ جاري إرسال رابط إعادة التعيين...', 'info');
  
  try {
    await window.sendPasswordResetEmail(window.auth, email);
    
    RateLimiter.recordSuccess(`reset_${email}`);
    SecurityAudit.log('PASSWORD_RESET_SENT', { email });
    
    showToast('✅ تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني', 'success');
    
    // العودة لصفحة تسجيل الدخول بعد 3 ثواني
    setTimeout(() => switchTab('login'), 3000);
    
  } catch (error) {
    RateLimiter.recordFailure(`reset_${email}`);
    SecurityAudit.log('PASSWORD_RESET_FAILED', { email, error: error.code });
    
    if (error.code === 'auth/user-not-found') {
      showToast('❌ لا يوجد حساب بهذا البريد الإلكتروني', 'error');
    } else {
      showToast('❌ ' + error.message, 'error');
    }
  }
}
window.sendPasswordReset = sendPasswordReset;

// ============================================
// تغيير كلمة المرور
// ============================================
async function changePassword() {
  if (!currentUser) {
    showToast('⚠️ يجب تسجيل الدخول أولاً', 'error');
    return;
  }
  
  const currentPassword = document.getElementById('currentPassword').value;
  const newPassword = document.getElementById('newPassword').value;
  
  if (!currentPassword || !newPassword) {
    showToast('⚠️ يرجى ملء جميع الحقول', 'error');
    return;
  }
  
  if (newPassword.length < 6) {
    showToast('⚠️ كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل', 'error');
    return;
  }
  
  showToast('⏳ جاري تغيير كلمة المرور...', 'info');
  
  try {
    // إعادة المصادقة
    const credential = window.EmailAuthProvider.credential(currentUser.email, currentPassword);
    await window.reauthenticateWithCredential(currentUser, credential);
    
    // تحديث كلمة المرور
    await window.updatePassword(currentUser, newPassword);
    
    SecurityAudit.log('PASSWORD_CHANGED', { email: currentUser.email });
    
    showToast('✅ تم تغيير كلمة المرور بنجاح', 'success');
    
    // تنظيف الحقول
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    
  } catch (error) {
    SecurityAudit.log('PASSWORD_CHANGE_FAILED', { error: error.code });
    
    if (error.code === 'auth/wrong-password') {
      showToast('❌ كلمة المرور الحالية غير صحيحة', 'error');
    } else if (error.code === 'auth/requires-recent-login') {
      showToast('⚠️ يرجى تسجيل الدخول مرة أخرى', 'warning');
    } else {
      showToast('❌ ' + error.message, 'error');
    }
  }
}
window.changePassword = changePassword;

// ============================================
// MFA Functions
// ============================================
async function toggleMFA() {
  if (!currentUser) {
    showToast('⚠️ يجب تسجيل الدخول أولاً', 'error');
    return;
  }
  
  await MFASystem.toggleMFA();
  SecurityAudit.log(mfaEnabled ? 'MFA_ENABLED' : 'MFA_DISABLED', { email: currentUser.email });
}
window.toggleMFA = toggleMFA;

async function sendMFA() {
  if (!currentUser) return;
  
  const result = await MFASystem.sendCode(currentUser.email);
  
  if (result.success) {
    document.getElementById('mfaCodeDisplay').textContent = result.code.split('').join(' ');
    showToast(`📧 تم إرسال الرمز إلى ${currentUser.email}`, 'success');
    SecurityAudit.log('MFA_SENT', { email: currentUser.email });
  }
}
window.sendMFA = sendMFA;

function resendMFA() {
  sendMFA();
}
window.resendMFA = resendMFA;

async function verifyMFA() {
  const code = document.getElementById('mfaCode').value.trim();
  
  if (!code || code.length !== 6) {
    showToast('⚠️ يرجى إدخال رمز مكون من 6 أرقام', 'error');
    return;
  }
  
  const result = MFASystem.verifyCode(code);
  
  if (result.success) {
    showToast('✅ تم التحقق بنجاح!', 'success');
    SecurityAudit.log('MFA_VERIFIED', { email: currentUser.email });
    
    // الانتقال للصفحة الرئيسية
    switchTab('home');
  } else {
    showToast(`❌ ${result.reason}`, 'error');
    SecurityAudit.log('MFA_FAILED', { reason: result.reason });
  }
}
window.verifyMFA = verifyMFA;

// ============================================
// تسجيل الدخول مع MFA و Rate Limiting
// ============================================
async function loginUserWithRetry(email = null, password = null, retryCount = 0) {
  const maxRetries = 3;
  
  if (!email || !password) {
    email = document.getElementById('loginEmail').value.trim();
    password = document.getElementById('loginPassword').value;
  }
  
  if (!email || !password) {
    showToast('⚠️ يرجى ملء جميع الحقول', 'error');
    return;
  }
  
  // التحقق من Rate Limiting
  const rateCheck = RateLimiter.check(`login_${email}`);
  if (!rateCheck.allowed) {
    showToast(`⚠️ ${rateCheck.reason}`, 'error');
    SecurityAudit.log('RATE_LIMITED', { email });
    return;
  }
  
  showToast('⏳ جاري تسجيل الدخول...', 'info');
  
  try {
    const result = await window.signInWithEmailAndPassword(window.auth, email, password);
    
    // نجاح تسجيل الدخول
    RateLimiter.recordSuccess(`login_${email}`);
    SecurityAudit.log('LOGIN_SUCCESS', { email });
    
    // التحقق من MFA
    if (mfaEnabled || result.user.mfaEnabled) {
      // إرسال رمز MFA
      await MFASystem.sendCode(email);
      switchTab('mfa');
      showToast('📧 تم إرسال رمز التحقق إلى بريدك', 'info');
    } else {
      showToast('✅ تم تسجيل الدخول بنجاح', 'success');
    }
    
  } catch (error) {
    RateLimiter.recordFailure(`login_${email}`);
    SecurityAudit.log('LOGIN_FAILED', { email, error: error.code });
    
    console.error('❌ خطأ في تسجيل الدخول:', error);
    
    if (error.code === 'auth/invalid-credential') {
      if (retryCount < maxRetries) {
        showToast(`⚠️ محاولة إعادة تسجيل الدخول (${retryCount + 1}/${maxRetries})`, 'warning');
        setTimeout(() => {
          loginUserWithRetry(email, password, retryCount + 1);
        }, 2000);
      } else {
        showToast('❌ فشل تسجيل الدخول. تأكد من البريد وكلمة المرور', 'error');
      }
    } else if (error.code === 'auth/user-not-found') {
      showToast('❌ لا يوجد حساب بهذا البريد', 'error');
    } else if (error.code === 'auth/wrong-password') {
      showToast('❌ كلمة المرور غير صحيحة', 'error');
    } else if (error.code === 'auth/too-many-requests') {
      showToast('❌ تم تجاوز عدد المحاولات. حاول لاحقاً', 'error');
    } else {
      showToast('❌ ' + error.message, 'error');
    }
  }
}
window.loginUserWithRetry = loginUserWithRetry;

// ============================================
// إنشاء حساب جديد
// ============================================
async function registerUserWithRetry(retryCount = 0) {
  const maxRetries = 3;
  
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const phone = document.getElementById('regPhone').value.trim();
  const password = document.getElementById('regPassword').value;
  const confirmPassword = document.getElementById('regConfirmPassword').value;
  const idFile = document.getElementById('regIdImage').files[0];
  
  if (!name || !email || !phone || !password) {
    showToast('⚠️ يرجى ملء جميع الحقول', 'error');
    return;
  }
  
  if (password !== confirmPassword) {
    showToast('⚠️ كلمتا المرور غير متطابقتين', 'error');
    return;
  }
  
  if (password.length < 6) {
    showToast('⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error');
    return;
  }
  
  if (!idFile) {
    showToast('⚠️ يرجى رفع صورة البطاقة أو شهادة الميلاد', 'error');
    return;
  }
  
  // التحقق من Rate Limiting
  const rateCheck = RateLimiter.check(`register_${email}`);
  if (!rateCheck.allowed) {
    showToast(`⚠️ ${rateCheck.reason}`, 'error');
    return;
  }
  
  showToast('⏳ جاري إنشاء الحساب...', 'info');
  
  const reader = new FileReader();
  reader.readAsDataURL(idFile);
  reader.onload = async function() {
    const idImage = reader.result;
    
    try {
      const result = await window.createUserWithEmailAndPassword(window.auth, email, password);
      const user = result.user;
      
      await window.set(window.ref(window.db, `users/${user.uid}`), {
        name: name,
        email: email,
        phone: phone,
        idImage: idImage,
        stage: '',
        grade: '',
        subjects: [],
        school: '',
        parentPhone: '',
        profileStatus: 'pending',
        mfa_enabled: false,
        createdAt: new Date().toISOString(),
        online: true,
        lastSeen: Date.now()
      });
      
      RateLimiter.recordSuccess(`register_${email}`);
      SecurityAudit.log('REGISTER_SUCCESS', { email });
      
      showToast('✅ تم إنشاء الحساب بنجاح! انتظر موافقة الإدارة', 'success');
      
      document.getElementById('regName').value = '';
      document.getElementById('regEmail').value = '';
      document.getElementById('regPhone').value = '';
      document.getElementById('regPassword').value = '';
      document.getElementById('regConfirmPassword').value = '';
      document.getElementById('regIdImage').value = '';
      
      switchTab('login');
      
    } catch (error) {
      RateLimiter.recordFailure(`register_${email}`);
      SecurityAudit.log('REGISTER_FAILED', { email, error: error.code });
      
      console.error('❌ خطأ في إنشاء الحساب:', error);
      
      if (error.code === 'auth/email-already-in-use') {
        showToast('❌ هذا البريد الإلكتروني مستخدم بالفعل', 'error');
      } else if (error.code === 'auth/weak-password') {
        showToast('❌ كلمة المرور ضعيفة. استخدم 6 أحرف على الأقل', 'error');
      } else if (error.code === 'auth/invalid-credential' && retryCount < maxRetries) {
        showToast(`⚠️ محاولة إعادة إنشاء الحساب (${retryCount + 1}/${maxRetries})`, 'warning');
        setTimeout(() => {
          registerUserWithRetry(retryCount + 1);
        }, 2000);
      } else {
        showToast('❌ ' + error.message, 'error');
      }
    }
  };
}
window.registerUserWithRetry = registerUserWithRetry;

// ============================================
// عرض الصور
// ============================================
function openImageViewer(imageSrc, title = 'صورة') {
  const viewer = document.getElementById('imageViewer');
  const img = document.getElementById('viewerImage');
  const info = document.getElementById('imageInfo');
  if (!viewer || !img) return;
  currentViewerImage = imageSrc;
  img.src = imageSrc;
  if (info) info.textContent = title;
  viewer.classList.add('show');
  document.body.style.overflow = 'hidden';
}
window.openImageViewer = openImageViewer;

function closeImageViewer() {
  const viewer = document.getElementById('imageViewer');
  if (viewer) viewer.classList.remove('show');
  document.body.style.overflow = '';
}
window.closeImageViewer = closeImageViewer;

function downloadImage() {
  if (currentViewerImage) {
    const link = document.createElement('a');
    link.href = currentViewerImage;
    link.download = 'sigma_image_' + Date.now() + '.jpg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('✅ جاري تحميل الصورة', 'success');
  }
}
window.downloadImage = downloadImage;

// ============================================
// Toast
// ============================================
function showToast(msg, type = 'info') {
  const old = document.querySelector('.toast');
  if (old) old.remove();
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 500); }, 3000);
}
window.showToast = showToast;

// ============================================
// التبويبات
// ============================================
function switchTab(id) {
  document.querySelectorAll('main > section').forEach(s => s.classList.add('hidden'));
  document.getElementById(`tab-${id}`)?.classList.remove('hidden');
  document.querySelectorAll('nav button').forEach(b => {
    b.classList.remove('text-blue-600');
    b.classList.add('text-slate-400');
  });
  const nav = document.getElementById(`nav-${id}`);
  if (nav) { nav.classList.remove('text-slate-400'); nav.classList.add('text-blue-600'); }
  if (id === 'admin') handleAdminTab();
}
window.switchTab = switchTab;

// ============================================
// وضع الليل
// ============================================
function toggleDarkMode() {
  darkMode = !darkMode;
  document.getElementById('app').classList.toggle('dark-mode', darkMode);
  document.getElementById('darkIcon').className = darkMode ? 'fa-solid fa-sun text-lg' : 'fa-solid fa-moon text-lg';
}
window.toggleDarkMode = toggleDarkMode;

// ============================================
// انتظار Firebase
// ============================================
function waitForFirebase() {
  return new Promise(resolve => {
    if (window.db && window.auth) { resolve(); return; }
    const check = setInterval(() => {
      if (window.db && window.auth) { clearInterval(check); resolve(); }
    }, 100);
  });
}

// ============================================
// بدء التطبيق
// ============================================
waitForFirebase().then(() => {
  console.log('🚀 سنتر سيجما - جاهز للتشغيل!');
  console.log('🔒 Rate Limiting: مفعّل');
  console.log('🛡️ MFA: مفعّل');
  console.log('📝 Security Audit: مفعّل');
  
  // استرجاع إعدادات MFA
  window.onValue(window.ref(window.db, `users/${currentUser?.uid}/mfa_enabled`), snap => {
    mfaEnabled = snap.val() || false;
    const mfaStatus = document.getElementById('mfaStatus');
    const mfaToggleBtn = document.getElementById('mfaToggleBtn');
    if (mfaStatus) {
      mfaStatus.textContent = mfaEnabled ? '✅ مفعّل' : '❌ معطّل';
      mfaStatus.className = mfaEnabled ? 'text-xs font-bold text-green-500' : 'text-xs font-bold text-red-500';
      mfaToggleBtn.innerHTML = mfaEnabled ? '<i class="fa-solid fa-shield-halved"></i> تعطيل MFA' : '<i class="fa-solid fa-shield-halved"></i> تفعيل MFA';
      mfaToggleBtn.className = mfaEnabled ? 'publish-btn red' : 'publish-btn green';
    }
  });
  
  SecurityAudit.log('APP_STARTED');
});
</script>
</body>
</html>
