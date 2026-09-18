#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка статьи Премиум Клиник (premium-clinic.com). Запуск: python3 check.py article_N.md
Только стандартная библиотека, без внешних зависимостей.
Выводит все метрики разом одним прогоном.
"""
import re, sys

STOP_WORDS = [
    "кроме того", "в контексте", "ключевой", "углубиться", "подчёркивая",
    "способствуя", "нюансы", "знаковый", "продемонстрировать", "акцентировать",
    "поистине", "по-настоящему", "в самом сердце", "в современном мире",
    "стоит отметить", "важно понимать", "важно отметить", "играет ключевую роль",
    "играет важную роль", "подводя итог", "таким образом", "комплексный подход",
    "идеально подходит для", "раскрыть потенциал", "выйти на новый уровень",
    "открывает новые горизонты", "и вот почему", "и вот тут начинается",
]

FAKE_EMPATHY = [
    "вы не одиноки", "вы сильнее, чем думаете", "каждый шаг имеет значение",
    "вы справитесь", "всё будет хорошо",
]

GUARANTEES = ["излечим", "100%", "навсегда", "гарантируем излечение"]


def strip_markup(text):
    """Убирает картинки, ссылки и подписи для честного подсчёта объёма тела статьи."""
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)      # картинки
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)      # ссылки -> текст
    return t


def main(path):
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    body = strip_markup(raw)
    low = body.lower()

    print("=" * 60)
    print(f"ПРОВЕРКА: {path}")
    print("=" * 60)

    # --- объём ---
    no_spaces = len(re.sub(r'\s', '', body))
    status = "OK" if 8500 <= no_spaces <= 9500 else "ВНЕ ДИАПАЗОНА 8500-9500"
    print(f"\n[ОБЪЁМ] знаков без пробелов: {no_spaces} - {status}")

    # --- КРИТИЧЕСКОЕ: конструкция "не X, а Y" и обратная ---
    print("\n[КРИТИЧНО] противопоставление через отрицание:")
    pats = [
        (r'\bне\s+[^.!?\n]{1,60}?,\s+а\s+', 'не X, а Y'),
        (r',\s+а\s+не\s+', 'Y, а не X'),
        (r'\bэто\s+не\s+[^.!?\n]{1,50}?[,.]\s*это\s+', 'это не X, это Y'),
        (r'\bне\s+просто\s+[^.!?\n]{1,50}?,\s*а\s+', 'не просто X, а Y'),
        (r'\bне\s+только\s+[^.!?\n]{1,50}?,\s*но\s+и\s+', 'не только X, но и Y'),
        (r'\bдело\s+не\s+в\s+', 'дело не в X'),
    ]
    total_crit = 0
    for pat, name in pats:
        hits = list(re.finditer(pat, low))
        if hits:
            total_crit += len(hits)
            print(f"  !! {name}: {len(hits)}")
            for h in hits:
                s = max(0, h.start() - 35); e = min(len(body), h.end() + 35)
                print(f"     ...{body[s:e].strip()}...")
    if total_crit == 0:
        print("  OK - 0 совпадений")
    else:
        print(f"  ИТОГО КРИТИЧЕСКИХ: {total_crit} - ДОЛЖНО БЫТЬ 0")

    # --- ряды отрицаний ---
    print("\n[РЯДЫ] тройные конструкции:")
    for pat, name in [(r'без\s+\w+[.,]\s*без\s+', 'ряд «без... без...»'),
                      (r'через\s+\w+[.,]\s*через\s+', 'ряд «через... через...»'),
                      (r'\bне\s+\w+,\s*не\s+\w+,\s*не\s+', 'ряд «не... не... не...»')]:
        n = len(re.findall(pat, low))
        print(f"  {name}: {n}" + (" !!" if n else " - OK"))

    # --- механика ---
    print("\n[МЕХАНИКА]")
    print(f"  длинное тире —: {body.count(chr(8212))}" + (" !!" if chr(8212) in body else " - OK"))
    print(f"  короткое тире –: {body.count(chr(8211))}" + (" !!" if chr(8211) in body else " - OK"))
    print(f"  стрелка →: {body.count(chr(8594))}")
    print(f"  точка с запятой: {body.count(';')}")
    bold = len(re.findall(r'\*\*[^*]+\*\*', raw))
    print(f"  жирных фрагментов: {bold} (лимит 4)" + (" !!" if bold > 4 else " - OK"))
    colons = body.count(':')
    print(f"  двоеточий: {colons}")

    # --- кавычки: единообразие ---
    yol = body.count('«')
    straight = body.count('"')
    if yol and straight:
        print(f"  !! СМЕШАНЫ кавычки: ёлочки {yol}, прямые {straight} - выбрать один тип")
    else:
        print(f"  кавычки: ёлочки {yol}, прямые {straight} - OK (единообразно)")

    # --- лексика ---
    print("\n[ЛЕКСИКА]")
    found = [(w, low.count(w)) for w in STOP_WORDS if w in low]
    print("  стоп-слова: " + (", ".join(f"{w} x{n}" for w, n in found) if found else "0 - OK"))
    fe = [w for w in FAKE_EMPATHY if w in low]
    print("  фальшивая эмпатия: " + (", ".join(fe) if fe else "0 - OK"))
    g = [w for w in GUARANTEES if w in low]
    print("  гарантии: " + (", ".join(g) if g else "0 - OK"))

    # --- частицы по абзацам ---
    print("\n[ЧАСТИЦЫ] >2 на абзац:")
    bad = 0
    for i, p in enumerate(body.split('\n\n'), 1):
        n = len(re.findall(r'\b(же|ведь|вот)\b|\w+-то\b', p.lower()))
        if n > 2:
            bad += 1
            print(f"  !! абзац {i}: {n}")
    if not bad:
        print("  OK")

    # --- раскладка ---
    print("\n[РАСКЛАДКА] латиница внутри русских слов:")
    mix = re.findall(r'\b(?=\w*[а-яё])(?=\w*[a-z])\w+\b', body, re.IGNORECASE)
    mix = [w for w in mix if not w.startswith('http')]
    print("  " + (", ".join(set(mix)) + " !!" if mix else "0 - OK"))

    # --- абзацы ---
    print("\n[АБЗАЦЫ] длиннее 7 строк (~40 симв/строка):")
    longp = 0
    for i, p in enumerate(body.split('\n\n'), 1):
        p = p.strip()
        if p.startswith('#') or not p:
            continue
        if len(p) / 40 > 7.5:
            longp += 1
            print(f"  !! абзац {i}: ~{round(len(p)/40)} строк")
    if not longp:
        print("  OK")

    # --- таблицы (в тексте статьи запрещены) ---
    tables = len(re.findall(r'^\|.*\|\s*$', raw, re.MULTILINE))
    print("\n[ТАБЛИЦЫ] строк markdown-таблиц: " + str(tables) + (" !! в тексте статьи таблиц быть не должно" if tables else " - OK"))

    # --- списки (в тексте запрещены полностью) ---
    lists = len(re.findall(r'^\s*(?:[-*+]\s|\d+[.)]\s)', re.sub(r'^#.*$','',raw,flags=re.MULTILINE), re.MULTILINE))
    print("\n[СПИСКИ] строк маркированных/нумерованных: " + str(lists) + (" !! в тексте статьи списков быть не должно" if lists else " - OK"))

    # --- восклицательные знаки (запрещены) ---
    excl = body.count('!')
    print("[ВОСКЛИЦАНИЯ] знаков '!': " + str(excl) + (" !! в этом формате запрещены" if excl else " - OK"))

    # --- обязательные блоки ---
    print("\n[ОБЯЗАТЕЛЬНЫЕ БЛОКИ]")
    low_raw = raw.lower()
    heads = [h.lower() for h in re.findall(r'^#{1,6}\s*(.+)$', raw, re.MULTILINE)]
    has_gloss = any('глоссар' in h for h in heads)
    has_src = any('источник' in h for h in heads)
    print("  глоссарий: " + ("есть - OK" if has_gloss else "!! НЕ НАЙДЕН"))
    print("  список источников: " + ("есть - OK" if has_src else "!! НЕ НАЙДЕН"))
    faq = len(re.findall(r'\?', body))
    print(f"  вопросительных знаков (ориентир FAQ 8-10): {faq}")

    # --- ссылки ---
    print("\n[ССЫЛКИ]")
    links = re.findall(r'https?://[^\s)]+', raw)
    for l in set(links):
        print(f"  {l}")

    # --- итог ---
    print("\n" + "=" * 60)
    ok = (total_crit == 0 and 8500 <= no_spaces <= 9500 and not tables and not lists and not excl and has_gloss and has_src
          and not mix and not (yol and straight))
    print("ИТОГ: " + ("ГОТОВО К СДАЧЕ" if ok else "ЕСТЬ ЗАМЕЧАНИЯ - СМОТРИ !! ВЫШЕ"))
    print("=" * 60)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'article.md')
