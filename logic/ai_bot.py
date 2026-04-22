import asyncio
import logging
import random
import aiohttp
import json
import re
from typing import Optional
from logic.manager import GameManager
from logic.player import Player
from logic.roles import RoleType, MAFIA_ROLES

log = logging.getLogger(__name__)

async def get_gemini_decision(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        log.error(f"Gemini API error: {e}")
    return ""

def extract_target_id(text: str, fallback_candidates: list[int]) -> int:
    """Extracts target_id from JSON or regex, returns a random fallback if parsing fails."""
    if not fallback_candidates:
        return 0
        
    try:
        clean_text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        if "target_id" in data:
            target = int(data["target_id"])
            if target in fallback_candidates:
                return target
    except Exception:
        pass
        
    # Regex fallback
    match = re.search(r"\"?target_id\"?\s*:\s*(\d+)", text, re.IGNORECASE)
    if match:
        target = int(match.group(1))
        if target in fallback_candidates:
            return target
            
    return random.choice(fallback_candidates)

async def bot_night_action(game: GameManager, p: Player):
    if not p.is_bot or not p.is_alive or not p.bot_api_key:
        return
    if p.night_action_done:
        return

    alive_others = [x for x in game.alive() if x.user_id != p.user_id]
    if not alive_others:
        return

    log_text = "\n".join(game.log[-15:]) if game.log else "O'yin endi boshlandi. Voqealar hali yo'q."
    
    # Prompt tayyorlash
    trait_desc = {
        "tajovuzkor": "Siz juda tajovuzkor o'ynaysiz, tezda shubha qilasiz va boshqalarni ayblaysiz.",
        "jim o'tiruvchi": "Siz ehtiyotkorsiz, ko'p gapirmaysiz, faqat muhim vaqtda harakat qilasiz.",
        "shubhachi": "Siz hamma narsadan shubhalanasiz, hatto eng kichik xatoni ham payqaysiz.",
        "mantiqiy": "Siz faqat faktlar va mantiq asosida qaror qabul qilasiz.",
        "aldamchi": "Siz juda yaxshi aldaysiz, agar mafiya bo'lsangiz o'zingizni ideal fuqarodek ko'rsatasiz."
    }.get(p.bot_trait or "mantiqiy", "")

    lying_strategy = ""
    if p.role in MAFIA_ROLES:
        lying_strategy = "Siz mafiyasiz! Maqsadingiz - o'zingizni fuqarodek ko'rsatish va boshqa fuqarolarni ayblab o'yindan chiqarish. Hech qachon mafiya ekanligingizni tan olmang!"

    prompt = (
        f"Sen Mafia o'yinida botsan. Isming: {p.full_name}.\n"
        f"Sening roling: {p.cfg.name_uz if p.cfg else 'Noma`lum'}.\n"
        f"Sening xaraktering: {p.bot_trait}. {trait_desc}\n"
        f"{lying_strategy}\n"
        f"Hozir tun bosqichi. Tirik o'yinchilar: {', '.join([f'{x.full_name} (ID: {x.user_id})' for x in alive_others])}.\n"
        f"Tungi harakating uchun bitta o'yinchining ID sini tanla.\n"
        f"Faqat ID raqamini qaytar, boshqa matn kerak emas."
    )

    valid_candidates = [x.user_id for x in alive_others]

    if p.role == RoleType.DON:
        prompt += "Siz Don sifatida bir kishini o'ldirish nishoniga olishingiz yoki detektivligini tekshirishingiz mumkin. " \
                  "Qaysi birini qilasiz? Agar tekshirsangiz, o'ylash jarayonida 'check' so'zini qo'shing."
    elif p.role == RoleType.DETECTIVE:
        prompt += "Siz Komissar sifatida tekshirishingiz yoki o'q otishingiz mumkin. " \
                  "Agar o'q otsangiz 'shot', tekshirsangiz 'check' deb o'ylash jarayonida ta'kidlang."
    elif p.role == RoleType.WITCH:
        dead = game.dead()
        dead_text = ", ".join([f"{x.full_name} (ID: {x.user_id})" for x in dead]) if dead else "Hech kim"
        prompt += f"Siz Jodugarsiz. Kimga zahar berasiz yoki kimni tiklaysiz? O'liklar: {dead_text}. " \
                  "Agar davolasangiz 'heal', zaharlasangiz 'poison' deb o'ylab target_id kiritasiz."
        if dead:
            valid_candidates.extend([x.user_id for x in dead])
    elif p.role == RoleType.LAWYER:
        mafia = [x for x in game.alive_mafia() if x.user_id != p.user_id]
        if not mafia:
            return game.set_lawyer_target(p.user_id, p.user_id)
        prompt += f"Siz Advokatsiz. Mafia a'zolarini himoya qilasiz: {', '.join([f'{x.full_name} (ID: {x.user_id})' for x in mafia])}. " \
                  "Faqat mafia a'zosining ID sini tanlang."
        valid_candidates = [x.user_id for x in mafia]
    elif p.cfg and p.cfg.night_action:
        prompt += "Qobiliyatingizni kimga ishlatasiz? Mantiqan kelib chiqib, rolingiz bo'yicha to'g'ri odamni tanlang."
    else:
        # Passiv rol
        return

    prompt += "\n\nQATTIQ TALAB: Javobingiz faqatgina quyidagi JSON formatida bo'lsin. Hech qanday boshqa so'zlar qo'shmang:\n" \
              "{\n" \
              "  \"thought\": \"Bu yerda nima uchun shu o'yinchini tanlaganingizni o'yin tarixi va qoidalarga tayanib mantiqiy tushuntirasiz...\",\n" \
              "  \"target_id\": <tanlangan o'yinchi ID raqami>\n" \
              "}"

    decision = await get_gemini_decision(p.bot_api_key, prompt)
    
    target_id = extract_target_id(decision, valid_candidates)
    
    # Debug info
    log.info(f"[Bot Night Action] Bot {p.user_id} ({p.role.name}) choice -> target_id: {target_id}, AI reply: {decision}")
    
    # Process the choice
    try:
        if p.role == RoleType.DON:
            if "check" in decision.lower() and "check" in decision.lower()[:150]:
                game.set_don_check(p.user_id, target_id)
            else:
                game.set_night_target(p.user_id, target_id)
        elif p.role == RoleType.DETECTIVE:
            if "shot" in decision.lower() and "shot" in decision.lower()[:150]:
                game.set_detective_shot(p.user_id, target_id)
            else:
                game.set_detective_check(p.user_id, target_id)
        elif p.role == RoleType.WITCH:
            if "heal" in decision.lower() and "heal" in decision.lower()[:150]:
                game.set_witch_action(p.user_id, "heal", target_id)
            elif "poison" in decision.lower() and "poison" in decision.lower()[:150]:
                game.set_witch_action(p.user_id, "poison", target_id)
            else:
                p.night_action_done = True
                game.na.acted.add(p.user_id)
        elif p.role == RoleType.LAWYER:
            game.set_lawyer_target(p.user_id, target_id)
        else:
            game.set_night_target(p.user_id, target_id)
    except Exception as e:
        log.error(f"Error setting bot night target: {e}")


async def bot_vote_action(game: GameManager, p: Player):
    if not p.is_bot or not p.is_alive or not p.bot_api_key:
        return
        
    alive_others = [x for x in game.alive() if x.user_id != p.user_id]
    if not alive_others:
        return
        
    log_text = "\n".join(game.log[-15:]) if game.log else "Hali hech narsa bo'lmadi."
        
    # Prompt tayyorlash
    trait_desc = {
        "tajovuzkor": "Siz juda tajovuzkor o'ynaysiz, tezda shubha qilasiz va boshqalarni ayblaysiz.",
        "jim o'tiruvchi": "Siz ehtiyotkorsiz, ko'p gapirmaysiz, faqat muhim vaqtda harakat qilasiz.",
        "shubhachi": "Siz hamma narsadan shubhalanasiz, hatto eng kichik xatoni ham payqaysiz.",
        "mantiqiy": "Siz faqat faktlar va mantiq asosida qaror qabul qilasiz.",
        "aldamchi": "Siz juda yaxshi aldaysiz, agar mafiya bo'lsangiz o'zingizni ideal fuqarodek ko'rsatasiz."
    }.get(p.bot_trait or "mantiqiy", "")

    lying_strategy = ""
    if p.role in MAFIA_ROLES:
        lying_strategy = "Siz mafiyasiz! O'zingizni asrab qolish uchun boshqa fuqarolarga ovoz bering va ularni ayblang. Mafiya a'zolariga (agar bilsangiz) ovoz bermaslikka harakat qiling."

    prompt = (
        f"Sen Mafia o'yinida botsan. Isming: {p.full_name}.\n"
        f"Sening roling: {p.cfg.name_uz if p.cfg else 'Noma`lum'}.\n"
        f"Sening xaraktering: {p.bot_trait}. {trait_desc}\n"
        f"{lying_strategy}\n"
        f"Hozir ovoz berish bosqichi. Tirik o'yinchilar: {', '.join([f'{x.full_name} (ID: {x.user_id})' for x in alive_others])}.\n"
        f"O'yin tarixi (oxirgi voqealar):\n{log_text}\n\n"
        f"Kimga ovoz bermoqchisiz? Faqat o'yinchining ID sini qaytaring.\n"
        f"\nQATTIQ TALAB: Javob faqat quyidagi JSON formatida bo'lishi kerak:\n"
        "{\n"
        "  \"thought\": \"Mana bu o'yinchi shubhali ko'rinyapti, chunki... Mantiqiy qarorim...\",\n"
        "  \"target_id\": <tanlangan o'yinchi ID raqami>\n"
        "}"
    )

    decision = await get_gemini_decision(p.bot_api_key, prompt)
    
    valid_candidates = [x.user_id for x in alive_others]
    target_id = extract_target_id(decision, valid_candidates)
    
    log.info(f"[Bot Vote Action] Bot {p.user_id} voted -> target_id: {target_id}, AI reply: {decision}")
    
    try:
        game.cast_vote(p.user_id, target_id)
    except Exception as e:
        log.error(f"Error casting vote for bot: {e}")


async def process_bots_night(game: GameManager, bot, group_id: int):
    from handlers.actions import process_dawn
    bots = [p for p in game.alive() if p.is_bot]
    for p in bots:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        await bot_night_action(game, p)
        if game.all_night_done():
            await process_dawn(game.chat_id, bot, group_id)
            break

async def process_bots_vote(game: GameManager, bot, group_id: int):
    from handlers.actions import process_vote
    bots = [p for p in game.alive() if p.is_bot]
    for p in bots:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        await bot_vote_action(game, p)
        if game.vote and game.vote.total() >= len(game.alive()):
            await process_vote(game.chat_id, bot, group_id)
            break
