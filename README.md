# 📊 Haftalik Odatlar Kuzatuvchisi (Professional Habit Tracker)

Bu ochiq manbali loyiha - shaxsiy odatlarni va kunlik vazifalarni professional tarzda kuzatib borish uchun mo'ljallangan zamonaviy, tezkor va qulay Desktop ilovasi. 

## 🌟 Imkoniyatlar (Features)
- **Zamonaviy va Professional UI:** `CustomTkinter` yordamida yozilgan, yorug' (Light) va qorong'u (Dark) mavzularni qo'llab-quvvatlaydi.
- **Interaktiv Grafika:** `Matplotlib` orqali yaratilgan kunlik va haftalik umumiy o'sish ko'rsatkichlari (Donut va Bar chartlar).
- **Odatlar va Vazifalar:** Odatlarni va vazifalarni alohida kuzatish, tahrirlash (qayta nomlash) va o'chirish imkoniyati. Maxsus kunlar uchun individual vazifalar qo'shish xususiyati ham mavjud.
- **Avtomatik Saqlash:** Barcha ma'lumotlar lokal kompyuteringizda `tracker_data.json` faylida maxfiy va xavfsiz saqlanadi. 
- **Excel ga Eksport:** Birgina tugmani bosish orqali barcha haftalik hisobotlarni va jadvallarni avtomatik moslashuvchan ustunlari bo'lgan Excel faylga (`.xlsx`) yuklab olish imkoniyati.
- **Xatoliklarni Log qilish va Qutqaruvchi (Try-Except):** Dastur kutilmagan xatoliklarga (Exception) qarshi himoyalangan va ular haqida ma'lumotni darhol `tracker_errors.log` fayliga arxivlaydi.
- **Optimallashtirilgan arxitektura:** "Lazy loading" (grafiklarni asinxron/kechiktirib yuklash) hamda faqatgina "Clean Code" va "KISS" yondashuvi qo'llanilgan.

## 🛠 Texnologiyalar (Tech Stack)
- **Dasturlash tili:** Python 3.x
- **Grafik interfeys (GUI):** CustomTkinter 
- **Ma'lumotlar tahlili va formati:** Pandas, JSON
- **Dinamik Grafika:** Matplotlib, Pillow (PIL)
- **Fayllar generatsiyasi:** Openpyxl (Excel tahlili uchun)

## 🚀 O'rnatish va Ishga tushirish (Installation)

Kompyuteringizda Python 3 o'rnatilganiga ishonch hosil qiling.

1. Loyihani yuklab oling (Clone the repository):
```bash
git clone https://github.com/SizningUsername/odatlar-traker.git
cd odatlar-traker
```

2. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

3. Dasturni ishga tushiring:
```bash
python main.py
```

## ⚙️ Loyiha Strukturasi
```text
odatlar_traker/
│
├── main.py                # Asosiy dastur kodi (Controller, View, DataManager, ThemeManager)
├── requirements.txt       # Dastur ishlashi uchun kerakli barcha kutubxonalar ro'yxati
├── .gitignore             # Git ga yuklanmasligi kerak bo'lgan xavfsiz va shaxsiy fayllar kodi
│
├── tracker_data.json      # (Avtomatik yaratiladi) Foydalanuvchi ma'lumotlar bazasi
└── tracker_errors.log     # (Avtomatik yaratiladi) Dastur loglari, ishlab chiquvchilar uchun
```

## 💡 Dasturdan Qanday Foydalaniladi?
1. Ekranning pastki bo'limidagi "**➕ Yangi Qo'shish**" orqali istalgancha haftalik odat yoki vazifa na'munasini ro'yxatga kiriting.
2. Agar bitta maxsus kun uchun rejangiz bo'lsa (Masalan: *Ertaga soat 14:00 da majlis*), o'sha kun nomining yonidagi mitti `+` tugmasini bosing va shaxsiy vazifani yozing.
3. Vazifa va Odatlar ro'yxatida ptichkani (☑) belgilaganingiz sari, tepada joylashgan "Umumiy o'sish" grafikalari va "Kunlik ko'rsatkichlar" foizi vizual tarzda yangilanib boradi.
4. Mavzuni istalgancha "🌙 Mavzu" tugmasi orqali Tungi va Kunduzgi holatga o'tkazishingiz mumkin.
5. Barchasini arxivga kiritish va xulosalarni baholash uchun "**📥 Excel ga yuklash**" tugmasini bosib jadval generatsiya qiling.

## 🤝 Hissa Qo'shish (Contributing)
Ochiq manbali loyiha sifatida dasturchilar yordamini doim qadrlarimiz. Agar arxitekturani yanada takomillashtirish bo'yicha g'oyalaringiz bo'lsa:
1. Loyihani o'zingizga "Fork" qiling
2. Yangi branch (shox) yarating (`git checkout -b feature/YangiImkoniyat`)
3. O'zgarishlarni kiriting va "Commit" qiling (`git commit -m 'Yangi imkoniyat qo'shildi'`)
4. Branch ni "Push" qiling (`git push origin feature/YangiImkoniyat`)
5. Pull Request yuboring!

## 👨‍💻 Muallif (Author)
- **Dasturchi:** Valijon Ergashev

## 📜 Litsenziya (License)
Bu loyiha MIT Litsenziyasi ostida tarqatiladi - batafsil ma'lumot uchun LICENSE faylini ko'ring (erkin foydalanish huquqi).
