# 🤖 بوت Odoo Jobs — يشتغل 24/7 على Railway

---

## الخطوة 1 — إنشاء البوت على تيليجرام

1. افتح تيليجرام → دور على **@BotFather**
2. ابعت: `/newbot`
3. اختار اسم → اختار username (ينتهي بـ bot)
4. **احتفظ بالتوكن** — هيبدو كده: `7123456789:AAFxxxxx`

---

## الخطوة 2 — جيب الـ Chat ID بتاعك

1. ابعت أي رسالة للبوت الجديد بتاعك
2. افتح في المتصفح:
```
https://api.telegram.org/botTOKEN_HENA/getUpdates
```
3. دور على: `"chat":{"id": 123456789}` — ده الـ Chat ID

---

## الخطوة 3 — رفع الملفات على Railway (مجاني)

### أ) عمل حساب على GitHub
1. روح [github.com](https://github.com) → Sign up (مجاني)
2. عمل Repository جديد اسمه `odoo-job-bot`
3. ارفع الملفات الأربعة:
   - `bot.py`
   - `requirements.txt`
   - `Procfile`
   - `railway.json`

### ب) ربط Railway بـ GitHub
1. روح [railway.app](https://railway.app) → **Start a New Project**
2. اختار **Deploy from GitHub repo**
3. اختار الـ repo بتاعك `odoo-job-bot`
4. اضغط **Deploy Now**

---

## الخطوة 4 — ضبط التوكن والـ Chat ID

في Railway بعد ما تعمل الـ Deploy:

1. اضغط على الـ Service بتاعك
2. روح على تبويب **Variables**
3. أضف المتغيرين دول:

| Variable Name | Value |
|---|---|
| `TELEGRAM_TOKEN` | التوكن بتاعك |
| `TELEGRAM_CHAT_ID` | الـ Chat ID بتاعك |

4. Railway هيعمل Redeploy تلقائي ✅

---

## ✅ خلاص! البوت شغال 24/7

- هتيجيلك رسالة ترحيب على تيليجرام فوراً
- هيتشيك كل **30 دقيقة** تلقائياً
- أي وظيفة Odoo جديدة — نوتيفيكيشن فوري 🔔

---

## 🌐 المواقع اللي بيراقبها

| الموقع | النوع |
|---|---|
| Wuzzuf 🇪🇬 | مصر |
| Indeed 🌍 | عالمي |
| Bayt 🌍 | الشرق الأوسط |
| LinkedIn 💼 | عالمي |
| Glassdoor 🔍 | عالمي |
| NaukriGulf 🌍 | الخليج |
| SimplyHired 🌐 | عالمي |

---

## ⚙️ تعديل وقت التشيك (اختياري)

في Railway Variables أضف:

| Variable | Value |
|---|---|
| `CHECK_INTERVAL` | `15` (دقيقة مثلاً) |

---

## ❓ مشاكل شائعة

**مجاش رسالة ترحيب؟**
→ تأكد إنك بعتت رسالة للبوت الأول

**البوت وقف؟**
→ في Railway → Deployments → شوف الـ Logs

**Railway بتطلب Credit Card؟**
→ استخدم Render.com بديل مجاني تاني:
روح [render.com](https://render.com) → New Web Service → اختار repo بتاعك → Environment: Python → Build: `pip install -r requirements.txt` → Start: `python bot.py`
