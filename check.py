#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка статьи — Премиум Клиник (premium-clinic.com)
Запуск: python3 check.py article_N.md

Параметры этой клиники (должны совпадать с файлом стиля на Google Drive —
при изменении объёма или лимитов правь ОБА места):
  объём 8500-9500 знаков без пробелов
  жирных фрагментов: не больше 3
  абзац: не длиннее 7 строк
  в тексте запрещены таблицы, списки и восклицательные знаки;
  обязательны заголовки «Глоссарий» и «Источники»

Блок «ИИ-ЯДРО» и блок «ОБЩИЕ ПРАВКИ» идентичны во всех пяти клиниках.
Не меняй их в одном репозитории, не поменяв в остальных.
Только стандартная библиотека Python.
"""
import re, sys

VMIN, VMAX = 8500, 9500
BOLD_LIMIT = 3
PARA_LINES = 7
CHECK_EMERGENCY = True   # True — призыв в 103/112 требует ручного решения
IMG_COUNT = 3        # сколько изображений должно быть в статье

# ============================================================
# ЕДИНОЕ ИИ-ЯДРО — одинаковое для всех пяти клиник
# ============================================================

CRIT_PATTERNS = [
    (r'\bне\s+[^.!?\n]{1,60}?,\s+а\s+', 'не X, а Y'),
    (r',\s+а\s+не\s+', 'Y, а не X'),
    (r'\bэто\s+не\s+[^.!?\n]{1,50}?[,.]\s*это\s+', 'это не X, это Y'),
    (r'\bне\s+просто\s+[^.!?\n]{1,50}?,\s*а\s+', 'не просто X, а Y'),
    (r'\bне\s+только\s+[^.!?\n]{1,50}?,\s*но\s+и\s+', 'не только X, но и Y'),
    (r'\bдело\s+не\s+в\s+', 'дело не в X'),
]

ROWS = [
    (r'без\s+\w+[.,]\s*без\s+', 'ряд «без... без...»'),
    (r'через\s+\w+[.,]\s*через\s+', 'ряд «через... через...»'),
    (r'\bне\s+\w+,\s*не\s+\w+,\s*не\s+', 'ряд «не... не... не...»'),
]

STOP_WORDS = [
    "кроме того", "в контексте", "ключевой", "углубиться", "подчёркивая",
    "способствуя", "нюансы", "знаковый", "продемонстрировать", "акцентировать",
    "поистине", "по-настоящему", "в самом сердце", "ландшафт", "свидетельство",
    "в современном мире", "в наше время", "не секрет что", "как известно",
    "стоит отметить", "важно отметить", "важно понимать", "следует учитывать",
    "нельзя не упомянуть", "более того", "таким образом", "в свою очередь",
    "играет ключевую роль", "играет важную роль", "подводя итог", "в заключение",
    "можно сделать вывод", "комплексный подход", "идеально подходит для",
    "раскрыть потенциал", "выйти на новый уровень", "открывает новые горизонты",
    "инновационное решение", "и вот почему", "и вот тут начинается",
    "данный", "данная", "данное", "в рамках", "в целях", "на данный момент",
    "в настоящее время", "представляет собой", "может похвастаться",
]

FAKE_EMPATHY = [
    "вы не одиноки", "вы сильнее, чем думаете", "каждый шаг имеет значение",
    "позвольте себе быть уязвимой", "вы справитесь", "всё будет хорошо",
    "вы делаете всё правильно", "главное - не сдаваться",
]

GUARANTEES = ["излечим", "100%", "навсегда", "гарантируем излечение", "гарантированный результат"]

# Внимание: проверка артефактов чата идёт с хвостовым (?!\w). Это нужно, чтобы
# «давайте разберёмся» — рабочая конструкция канала «Гармония» — не ловилась
# на подстроку «давайте разберём».
CHAT_ARTIFACTS = [
    "отличный вопрос", "хороший вопрос", "надеюсь это поможет", "надеюсь, это поможет",
    "давайте рассмотрим", "давайте разберём", "конечно!", "безусловно!",
]

# ============================================================
# ОБЩИЕ ПРАВКИ — одинаковые для всех пяти клиник
# ============================================================

# города: ни один не должен попасть в текст статьи
CITIES = [
    "краснодар", "ростов", "петербург", "питер", "новосибирск", "москв",
    "екатеринбург", "воронеж", "самар", "нижний новгород", "сочи",
]

# служебные префиксы, которых не должно быть в заголовке
H1_PREFIXES = ["тема", "статья", "пост", "заголовок", "title", "topic"]

# повторяющиеся штампы канала «Гармония», выведенные из обращения
RETIRED_PHRASES = [
    "вы не преувеличиваете", "вы такая не одна", "вы не одна такая",
    "детали вызова я изменил", "имена и детали изменены",
]


def text_for_colons(raw):
    """Тело статьи без H1, URL, меток изображений и служебного слова «Подпись»."""
    t = re.sub(r'^#\s+.*$', '', raw, flags=re.M)
    t = re.sub(r'https?://\S+', '', t)
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', t)
    t = re.sub(r'\[\s*ИЗОБРАЖЕНИЕ[^\]]*\]', '', t, flags=re.I)
    t = re.sub(r'(?i)\bподпис[ьи]\s*:', '', t)
    t = re.sub(r'(?i)\balt\s*:', '', t)
    return t


def strip_markup(text):
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    return t


def main(path):
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    body = strip_markup(raw)
    low = body.lower()
    problems = []
    manual = []

    print("=" * 64)
    print("ПРОВЕРКА: Премиум Клиник (premium-clinic.com)  |  файл: " + path)
    print("=" * 64)

    # --- объём (параметр клиники) ---
    no_spaces = len(re.sub(r'\s', '', body))
    ok_vol = VMIN <= no_spaces <= VMAX
    print(f"\n[ОБЪЁМ] знаков без пробелов: {no_spaces} (норма {VMIN}-{VMAX})" + ("" if ok_vol else "  !!"))
    if not ok_vol:
        problems.append("объём вне диапазона")

    # ====== ИИ-ЯДРО ======
    print("\n[ИИ-ЯДРО] противопоставление через отрицание:")
    total_crit = 0
    for pat, name in CRIT_PATTERNS:
        for h in re.finditer(pat, low):
            s = max(0, h.start() - 35); e = min(len(body), h.end() + 35)
            mark = ""

            total_crit += 1
            print(f"  !! {name}: ...{body[s:e].replace(chr(10), ' ').strip()}...{mark}")
    if total_crit == 0:
        print("  0 - OK")
    else:
        print(f"  ВСЕГО: {total_crit} - должно быть 0")
        problems.append("конструкции-маркеры")

    print("\n[ИИ-ЯДРО] ряды отрицаний:")
    rows_found = 0
    for pat, name in ROWS:
        n = len(re.findall(pat, low))
        if n:
            rows_found += n
            print(f"  !! {name}: {n}")
    print("  0 - OK" if not rows_found else "")
    if rows_found:
        problems.append("ряды отрицаний")

    print("\n[ИИ-ЯДРО] символы:")
    dash_long = body.count(chr(8212)); dash_short = body.count(chr(8211))
    print(f"  длинное тире: {dash_long}" + ("  !!" if dash_long else " - OK"))
    print(f"  короткое тире: {dash_short}" + ("  !!" if dash_short else " - OK"))
    print(f"  стрелки: {body.count(chr(8594))}   точка с запятой: {body.count(';')}")
    if dash_long or dash_short:
        problems.append("тире")

    yol, straight = body.count('«'), body.count('"')
    if yol and straight:
        print(f"  !! кавычки смешаны: ёлочки {yol}, прямые {straight}")
        problems.append("смешаны кавычки")
    else:
        print(f"  кавычки: ёлочки {yol}, прямые {straight} - единообразно")

    print("\n[ИИ-ЯДРО] лексика:")
    sw = [(w, low.count(w)) for w in STOP_WORDS if w in low]
    print("  стоп-слова: " + (", ".join(f"{w} x{n}" for w, n in sw) + "  !!" if sw else "0 - OK"))
    fe = [w for w in FAKE_EMPATHY if w in low]
    print("  фальшивая эмпатия: " + (", ".join(fe) + "  !!" if fe else "0 - OK"))
    gu = [w for w in GUARANTEES if w in low]
    print("  гарантии: " + (", ".join(gu) + "  !!" if gu else "0 - OK"))
    ca = [w for w in CHAT_ARTIFACTS if re.search(re.escape(w) + r'(?!\w)', low)]
    print("  артефакты чата: " + (", ".join(ca) + "  !!" if ca else "0 - OK"))
    if sw or fe or gu or ca:
        problems.append("лексика")

    print("\n[ИИ-ЯДРО] частицы же/ведь/вот/-то, >2 на абзац:")
    bad_p = 0
    for i, p in enumerate(body.split('\n\n'), 1):
        n = len(re.findall(r'\b(же|ведь|вот)\b|\w+-то\b', p.lower()))
        if n > 2:
            bad_p += 1
            print(f"  !! абзац {i}: {n}")
    print("  OK" if not bad_p else "")
    if bad_p:
        problems.append("частицы")

    print("\n[ИИ-ЯДРО] смешение кириллицы и латиницы внутри слова:")
    mix = [w for w in re.findall(r'\b(?=\w*[а-яё])(?=\w*[a-z])\w+\b', body, re.I) if not w.startswith('http')]
    print("  " + (", ".join(sorted(set(mix))) + "  !!" if mix else "0 - OK"))
    if mix:
        problems.append("раскладка")

    # ====== ОБЩИЕ ПРАВКИ ======
    print("\n[ПРАВКИ] город в тексте:")
    nourl = re.sub(r'https?://\S+', '', low)
    found_city = sorted({c for c in CITIES if c in nourl})
    print("  " + (", ".join(found_city) + "  !! город из текста убирается полностью" if found_city else "0 - OK"))
    if found_city:
        problems.append("город в тексте")

    print("\n[ПРАВКИ] служебный префикс в заголовке:")
    h1m = re.search(r'^#\s+(.+)$', raw, re.M)
    h1t = h1m.group(1).strip() if h1m else ''
    pref = re.match(r'(?i)^\s*(' + '|'.join(H1_PREFIXES) + r')\s*[:\-—]', h1t)
    if not h1m:
        print("  !! H1 не найден")
        problems.append("нет H1")
    elif pref:
        print(f"  !! H1 начинается с «{pref.group(1)}:» — оставить только сам заголовок")
        problems.append("префикс в H1")
    else:
        print("  0 - OK")
    other_pref = [h for h in re.findall(r'^#{2,6}\s*(.+)$', raw, re.M)
                  if re.match(r'(?i)^\s*(' + '|'.join(H1_PREFIXES) + r')\s*[:\-—]', h)]
    if other_pref:
        print("  !! тот же префикс в подзаголовках: " + "; ".join(other_pref[:5]))
        problems.append("префикс в подзаголовке")

    print("\n[ПРАВКИ] двоеточия в теле (лимит 1, H1 не считается):")
    tc = text_for_colons(raw)
    cols = [m.start() for m in re.finditer(r':', tc)]
    for pos in cols:
        s = max(0, pos - 40); e = min(len(tc), pos + 40)
        print("  - ..." + tc[s:e].replace(chr(10), ' ').strip() + "...")
    print(f"  всего: {len(cols)} (лимит 1)" + ("  !!" if len(cols) > 1 else " - OK"))
    if len(cols) > 1:
        problems.append("двоеточий больше одного")

    print("\n[ПРАВКИ] выведенные из обращения фразы:")
    rp = [w for w in RETIRED_PHRASES if w in low]
    print("  " + (", ".join(rp) + "  !!" if rp else "0 - OK"))
    if rp:
        problems.append("штампованные фразы")

    print("\n[ПРАВКИ] призыв в 103/112:")
    emg = []
    for m in re.finditer(r'(?<!\d)(103|112)(?!\d)', body):
        s = max(0, m.start() - 60); e = min(len(body), m.end() + 60)
        emg.append(body[s:e].replace(chr(10), ' ').strip())
    if not emg:
        print("  0 - OK")
    elif CHECK_EMERGENCY:
        for c in emg:
            print("  ?  ..." + c + "...")
        print(f"  найдено {len(emg)} — допустимо ТОЛЬКО в абзаце про угрожающее жизни состояние.")
        print("     В CTA и в концовке — убрать. Решение ручное, скрипт за тебя его не примет.")
        manual.append("проверить 103/112 по месту")
    else:
        for c in emg:
            print("  i  ..." + c + "...")
        print(f"  найдено {len(emg)} — для этого канала номера допустимы, но только по месту, не концовкой.")
        manual.append("проверить, что 103/112 стоят по месту")

    print("\n[ПРАВКИ] распределение изображений:")
    _n = re.sub(r'!\[[^\]]*\]\([^)]*\)', '<IMG>', raw)
    _n = re.sub(r'\[\s*ИЗОБРАЖЕНИЕ[^\]]*\]', '<IMG>', _n, flags=re.I)
    img_marks = [m.start() for m in re.finditer(r'<IMG>', _n)]
    print(f"  изображений в тексте: {len(img_marks)}")
    if len(img_marks) >= 2:
        gaps = [img_marks[i + 1] - img_marks[i] for i in range(len(img_marks) - 1)]
        tight = [g for g in gaps if g < 400]
        print(f"  промежутки между картинками (знаков): {gaps}")
        if tight:
            print("  !! две картинки стоят почти подряд — изображения распределяются равномерно")
            problems.append("изображения не распределены")
        else:
            print("  распределены - OK")

    # ====== параметры клиники ======
    print("\n[ФОРМАТ]")
    bold = len(re.findall(r'\*\*[^*]+\*\*', raw))
    print(f"  жирных фрагментов: {bold} (лимит {BOLD_LIMIT})" + ("  !!" if bold > BOLD_LIMIT else " - OK"))
    if bold > BOLD_LIMIT:
        problems.append("жирного больше лимита")

    long_p = 0
    for i, p in enumerate(body.split('\n\n'), 1):
        p = p.strip()
        if p.startswith('#') or not p:
            continue
        if len(p) / 40 > PARA_LINES + 0.5:
            long_p += 1
            print(f"  !! абзац {i}: ~{round(len(p)/40)} строк (лимит {PARA_LINES})")
    if not long_p:
        print(f"  абзацы в пределах {PARA_LINES} строк - OK")
    else:
        problems.append("длинные абзацы")

    tables = len(re.findall(r'^\|.*\|\s*$', raw, re.M))
    print(f"  markdown-таблиц (строк): {tables}" + ("  !! в тексте запрещены" if tables else " - OK"))
    if tables:
        problems.append("таблицы в тексте")

    body_nohead = re.sub(r'^#.*$', '', raw, flags=re.M)
    lists = len(re.findall(r'^\s*(?:[-*+]\s|\d+[.)]\s)', body_nohead, re.M))
    print(f"  списков (строк): {lists}" + ("  !! в тексте запрещены" if lists else " - OK"))
    if lists:
        problems.append("списки в тексте")

    excl = body.count('!')
    print(f"  восклицательных знаков: {excl}" + ("  !! запрещены в этом формате" if excl else " - OK"))
    if excl:
        problems.append("восклицания")

    heads = [h.lower() for h in re.findall(r'^#{1,6}\s*(.+)$', raw, re.M)]
    has_gloss = any('глоссар' in h for h in heads)
    has_src = any('источник' in h for h in heads)
    print("\n[ОБЯЗАТЕЛЬНЫЕ БЛОКИ]")
    print("  глоссарий: " + ("есть - OK" if has_gloss else "!! НЕ НАЙДЕН"))
    print("  список источников: " + ("есть - OK" if has_src else "!! НЕ НАЙДЕН"))
    if not has_gloss:
        problems.append("нет глоссария")
    if not has_src:
        problems.append("нет источников")

    # ====== картинки: настоящий markdown, а не текстовая метка ======
    print("\n[КАРТИНКИ]")
    marks = re.findall(r'\[\s*ИЗОБРАЖЕНИЕ[^\]]*\]', raw, re.I)
    if marks:
        print(f"  !! осталось текстовых меток: {len(marks)} - Дзен покажет их текстом, а не картинкой")
        for m in marks[:6]:
            print("     " + m[:70])
        problems.append("остались текстовые метки изображений")

    imgs = re.findall(r'!\[([^\]]*)\]\(([^)]*)\)', raw)
    ok_cnt = len(imgs) == IMG_COUNT
    print(f"  markdown-картинок: {len(imgs)} (нужно {IMG_COUNT})" + ("" if ok_cnt else "  !!"))
    if not ok_cnt:
        problems.append(f"картинок {len(imgs)}, а нужно {IMG_COUNT}")

    bad = [u for _, u in imgs if not u.lower().startswith('http')]
    if bad:
        print(f"  !! вместо ссылки заглушка: {len(bad)} шт")
        for u in bad[:4]:
            print("     " + (u[:60] if u.strip() else "(пусто)"))
        problems.append("в картинке не настоящая ссылка")

    noalt = [u for a, u in imgs if not a.strip()]
    if noalt:
        print(f"  !! без описания в alt: {len(noalt)} шт")
        problems.append("у картинки пустой alt")

    nocap = []
    for m in re.finditer(r'!\[[^\]]*\]\([^)]*\)', raw):
        after = raw[m.end():m.end() + 400]
        if not re.match(r'[ \t]*\n[ \t]*\n[ \t]*(\*\*)?\s*Подпись', after):
            nocap.append(raw[m.start():m.start() + 50])
    if nocap:
        print(f"  !! без подписи отдельной строкой: {len(nocap)} шт")
        for s in nocap[:4]:
            print("     " + s.replace('\n', ' '))
        problems.append("у картинки нет подписи")
    elif imgs:
        print("  подписи на месте - OK")

    print("\n[ССЫЛКИ]")
    for l in sorted(set(re.findall(r'https?://[^\s)]+', raw))):
        print("  " + l)

    print("\n" + "=" * 64)
    print("ИТОГ: ГОТОВО К СДАЧЕ" if not problems else "ИТОГ: ЕСТЬ ЗАМЕЧАНИЯ - " + ", ".join(problems))
    if manual:
        print("РУЧНОЕ РЕШЕНИЕ: " + ", ".join(manual))
    print("=" * 64)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'article.md')
