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

Блок «ИИ-паттерны» идентичен во всех пяти клиниках. Не меняй его в одном
репозитории, не поменяв в остальных.
Только стандартная библиотека Python.
"""
import re, sys

VMIN, VMAX = 8500, 9500
BOLD_LIMIT = 3
PARA_LINES = 7

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

CHAT_ARTIFACTS = [
    "отличный вопрос", "хороший вопрос", "надеюсь это поможет", "надеюсь, это поможет",
    "давайте рассмотрим", "давайте разберём", "конечно!", "безусловно!",
]


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
            print(f"  !! {name}: ...{body[s:e].strip()}...{mark}")
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
    print(f"  стрелки: {body.count(chr(8594))}   точка с запятой: {body.count(';')}   двоеточия: {body.count(':')}")
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
    ca = [w for w in CHAT_ARTIFACTS if w in low]
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

    print("\n[ССЫЛКИ]")
    for l in sorted(set(re.findall(r'https?://[^\s)]+', raw))):
        print("  " + l)
    print(f"[КАРТИНКИ] найдено: {len(re.findall(r'!\[', raw))}")

    print("\n" + "=" * 64)
    print("ИТОГ: ГОТОВО К СДАЧЕ" if not problems else "ИТОГ: ЕСТЬ ЗАМЕЧАНИЯ - " + ", ".join(problems))
    print("=" * 64)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'article.md')
