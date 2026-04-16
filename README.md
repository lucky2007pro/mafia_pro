# 🎭 Mafia Bot v3.0

**Python 3.11 + aiogram 3.x** asosida yaratilgan professional Telegram Mafia o'yin boti.
100+ parallel o'yin, 16 noyob rol, to'liq statistika.

---

## 📁 Loyiha tuzilmasi

```
mafia_v3/
│
├── 🚀 bot.py                  — Asosiy ishga tushirish
├── ⚙️  config.py               — Barcha sozlamalar
├── 🛡️  middlewares.py          — Anti-spam, Error, UserTracker
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📋 requirements.txt
├── 🔑 .env.example
│
├── handlers/
│   ├── common.py              — /start /help /rules
│   ├── game.py                — Lobby, join/leave, startgame
│   ├── actions.py             — Tun/Tong/Kun/Ovoz (asosiy engine)
│   ├── admin.py               — Admin buyruqlari
│   ├── stats.py               — Statistika
│   └── special.py             — /snipe /reveal
│
├── logic/
│   ├── roles.py               — 16 ta rol ta'rifi
│   ├── player.py              — Player model
│   ├── manager.py             — GameManager (o'yin qalbi)
│   └── registry.py            — Parallel o'yinlar registri
│
├── keyboards/
│   └── game_kb.py             — Barcha Inline tugmalar
│
├── utils/
│   └── texts.py               — Xabar shablonlari
│
└── database/
    └── db.py                  — SQLAlchemy + statistika
```

---

## 👥 16 ta Rol

### 🔴 Mafia guruhi (4 rol)

| Emoji | Rol | Qobiliyat |
|-------|-----|-----------|
| 🔫 | **Mafia** | Har tunda bittani o'ldiradi |
| 👑 | **Don** | O'ldiradi + detektivni aniqlaydi. Detektivga begunoh ko'rinadi |
| 🤵 | **Godfather** | Detektivga fuqaro ko'rinadi — eng xavfli yashirin kuch |
| ⚖️ | **Advokat** | Mafia a'zosini detektiv tekshiruvidan himoya qiladi |

### 🔵 Shahar guruhi (9 rol)

| Emoji | Rol | Qobiliyat |
|-------|-----|-----------|
| 👤 | **Fuqaro** | Kunduz ovoz beradi |
| 💊 | **Shifokor** | Tunda saqlay oladi (o'zini 1x) |
| 🔍 | **Detektiv** | Tunda rol tekshiradi (Don/Godfather begunoh ko'rinadi!) |
| 🛡️ | **Qo'riqchi** | Himoya qiladi, o'zi o'ladi |
| 🎯 | **Snayper** | Kunduz 1 o'q — xato bo'lsa o'zi o'ladi |
| 🎩 | **Mer** | 2 ovoz (oshkor qilsa 3 ovoz) |
| 🗡️ | **Qonunchi** | Tunda 1x o'ldiradi (begunoh o'lsa vijdon azobi) |
| 📰 | **Jurnalist** | Kimningdir rolini hammaga oshkor qiladi (1x) |
| 🕵️ | **Agent** | Passiv — mafia nishonini biladi |

### ⚪ Neytral (3 rol)

| Emoji | Rol | Qobiliyat |
|-------|-----|-----------|
| 🔪 | **Manyak** | Tunda o'ldiradi, yolg'iz g'alaba qiladi |
| 💣 | **Suitsid** | Ovoz bilan o'lsa — kimnidir olib ketadi |
| 💃 | **Faoliyatchi** | Kimningdir tun harakatini bloklaydi |
| 🧙 | **Jodugar** | Zahar (1x o'ldirish) + Davo (1x tiklash) |

---

## 🏆 G'alaba shartlari

```
🏙️ Shahar   →  Barcha mafia + manyak yo'q qilinsa
🔫 Mafia    →  Tirik mafia ≥ tirik shahar bo'lsa
🔪 Manyak   →  Yolg'iz oxirgi tirik qolsa
🧙 Jodugar  →  Oxirgi 3 o'yinchi ichida bo'lsa
```

---

## 🎮 O'yin oqimi

```
/newgame
   ↓
[🔵 LOBBY] — O'yinchilar qo'shiladi (120s)
   ↓
[🎭 START] — Rollar taqsimlanadi, DM yuboriladi
   ↓
[🌙 TUN] ──────────────────────────────────┐
  • Mafia/Don/Godfather: nishon tanlaydi   │
  • Advokat: mafia a'zosini himoya qiladi  │
  • Shifokor: kimni davolaydi?             │  Takrorlandi
  • Detektiv: kimni tekshiradi?            │
  • Qo'riqchi: kimni himoya qiladi?        │
  • Qonunchi: (ixtiyoriy) o'ldirish        │
  • Faoliyatchi: kimni bloklaydi?          │
  • Manyak: o'z nishonini tanlaydi        │
  • Jodugar: zahar yoki davo?             │
   ↓                                       │
[☀️ TONG] — Natijalar e'lon qilinadi       │
   ↓         Agent → mafia nishonini bildi │
[💬 KUN] — 90s muhokama                   │
   • /snipe  — Snayper otishi             │
   • /reveal — Mer oshkor qilish          │
   ↓                                       │
[🗳️ OVOZ BERISH] — Kim chiqarilsin?       │
   • Mer 2x (oshkor qilsa 3x) ovoz        │
   • Suitsid o'lsa → kimnidir olib ketadi │
   ↓                                       │
[G'ALABA TEKSHIRUVI] ─── yo'q ────────────┘
   ↓ ha
[🏆 O'YIN TUGADI]
```

---

## ⌨️ Buyruqlar ro'yxati

### 👤 Foydalanuvchi

| Buyruq | Joy | Tavsif |
|--------|-----|--------|
| `/newgame` | Guruh | Lobby ochish |
| `/startgame` | Guruh | O'yinni boshlash |
| `/endgame` | Guruh | O'yinni to'xtatish |
| `/players` | Guruh | O'yinchilar ro'yxati |
| `/rules` | Har joyda | Qoidalar |
| `/stats` | Guruh | Guruh statistikasi |
| `/top` | Har joyda | Top 10 |
| `/mystats` | Shaxsiy | Profilim |
| `/snipe` | Shaxsiy | Snayper otishi (kunduz) |
| `/reveal` | Shaxsiy | Mer oshkor qilish |

### 🔧 Admin

| Buyruq | Tavsif |
|--------|--------|
| `/skipnight` | Tunni majburan o'tkazish |
| `/skipday` | Kunduzni o'tkazish |
| `/skipvote` | Ovozni yakunlash |
| `/gamestatus` | O'yin debug holati |
| `/kick` | O'yinchini chiqarish (reply) |
| `/settime night 30` | Vaqtlarni o'zgartirish |
| `/serverstats` | Server holati (super admin) |

---

## 🚀 O'rnatish

### Oddiy usul (Python)

```bash
git clone <repo>
cd mafia_v3

pip install -r requirements.txt

cp .env.example .env
# .env ichida BOT_TOKEN ni o'zingiznikiga almashtiring

python bot.py
```

### Docker bilan (tavsiya etiladi)

```bash
cp .env.example .env
# BOT_TOKEN ni kiriting

docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f bot
```

---

## 🤖 Guruhni sozlash

1. [@BotFather](https://t.me/BotFather) → `/newbot` → Token oling
2. `@BotFather` → `/setprivacy` → **Disable** (guruh xabarlarini o'qishi uchun)
3. Botni guruhga qo'shing
4. Botga **Admin huquqi** bering:
   - ✅ Xabar yuborish
   - ✅ A'zolarni cheklash (Tun uchun guruh mute)
5. Har bir o'yinchi avval botga `/start` yuborsin

> ⚠️ `/start` yuborilmasa — shaxsiy (DM) xabarlar yetib bormaydi!

---

## 📊 Rol taqsimlanishi

| O'yinchilar | Mafia | Don | Godfather | Advokat | Shifokor | Detektiv | Qo'riqchi | Snayper | Mer | Qonunchi | Jurnalist | Agent | Manyak | Suitsid | Faoliyatchi | Fuqaro |
|:-----------:|:-----:|:---:|:---------:|:-------:|:--------:|:--------:|:---------:|:-------:|:---:|:--------:|:---------:|:-----:|:------:|:-------:|:-----------:|:------:|
| 4 | 1 | — | — | — | 1 | — | — | — | — | — | — | — | — | — | — | 2 |
| 6 | 1 | 1 | — | — | 1 | 1 | — | — | — | — | — | — | — | — | — | 2 |
| 8 | 2 | 1 | — | — | 1 | 1 | — | — | — | — | — | — | 1 | — | — | 2 |
| 10 | 2 | 1 | — | — | 1 | 1 | 1 | 1 | 1 | — | — | — | 1 | — | — | 1 |
| 12 | 2 | 1 | 1 | — | 1 | 1 | 1 | 1 | 1 | — | 1 | — | 1 | 1 | — | — |
| 15 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | — |

---

## ⚡ 100+ Parallel o'yin

Bot har bir guruh uchun mustaqil `GameManager` obyekti yaratadi.
Barcha o'yinlar `asyncio` orqali bir-birini bloklasiz ishlaydi.

```
Guruh A o'yini ──┐
Guruh B o'yini ──┤──► asyncio event loop ──► Bir xil bot instance
Guruh C o'yini ──┘
```

**Scaling uchun tavsiyalar:**
- 100 ta o'yin uchun: 1 GB RAM, 2 vCPU yetarli
- 500+ o'yin uchun: Redis session storage + horizontal scaling
- 1000+ uchun: aiogram webhook + load balancer

---

## 🔮 Kelajakdagi yangiliklar

- [ ] 🗺️ **Mayor ovoz tartibi** — ko'pchilik ovoz bersa e'lon qilinadi
- [ ] 📜 **Vasiyat tizimi** — o'lganda xabar qoldirish
- [ ] 🔊 **Mafia chat** — tunda mafia a'zolari uchun maxsus guruh yaratish
- [ ] 🏅 **ELO rating** — G'alaba/yutqizishga qarab ball tizimi
- [ ] 🌐 **Mini WebApp** — statistika uchun Telegram WebApp
- [ ] 🎲 **Custom rollar** — admin o'z rollar to'plamini belgilaydi
- [ ] ⏰ **Scheduled games** — kun/soatda avtomatik o'yin e'loni

---

## 📝 Litsenziya

MIT — erkin foydalaning, takomillashtiring!
#   m a f i a _ p r o  
 