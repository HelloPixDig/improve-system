#!/usr/bin/env python3
"""Trie l'historique local de Claude Code et en sort un résumé : corrections récurrentes, tâches répétées
(dans plusieurs sessions distinctes) et aveux de travail manuel. Python standard, 100 % local, rien n'est envoyé.
Usage : python3 scan_history.py [--days N] [--root DIR] [--json] [--min-sessions 3]"""
import argparse, collections, glob, json, os, re, sys, time

SKIP = re.compile(r"^\s*(<|\[Request interrupted|This session is being continued|Caveat:|/)", re.I)
CORRECTION = [r"c'est pas ça", r"c'est pas", r"ce n'est pas ça", r"refais", r"recommence", r"tu t'es trompé", r"tu as oublié", r"^non[,.! ]", r"\bfaux\b",
              r"that's wrong", r"that is wrong", r"not what i", r"you forgot", r"redo", r"try again", r"i said", r"i told you", r"incorrect", r"pas ce que"]
MANUAL = [r"à la main", r"manuellement", r"je fais toujours", r"je refais", r"à chaque fois", r"encore une fois", r"comme d'habitude",
          r"every time", r"manually", r"by hand", r"again and again", r"as usual", r"i always"]
VERBS = r"\b(?:refais|fais|crée|cree|génère|genere|ajoute|corrige|modifie|vérifie|verifie|publie|programme|lance|remplace|mets|met|écris|ecris|regarde|teste|compare|résume|resume|traduis|make|create|generate|add|fix|update|check|publish|schedule|run|replace|write|test|compare|summarize|translate)\b"

STOP = set("cette ceci cela quoi comment pourquoi tous toutes toujours encore aussi alors maintenant juste cette votre notre avec pour dans sans plus moins très trop".split())

def text_of(msg):
    c = msg.get("content")
    if isinstance(c, str): return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""

def user_messages(root, days):
    since = time.time() - days * 86400 if days else 0
    for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        if since and os.path.getmtime(path) < since: continue
        sid = os.path.basename(path)[:-6]
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try: d = json.loads(line)
                    except ValueError: continue
                    if d.get("type") != "user" or d.get("isMeta") or d.get("isSidechain"): continue
                    t = text_of(d.get("message", {})).strip()
                    if not t or SKIP.match(t) or len(t) > 1500: continue   # blocs collés / système : bruit
                    yield sid, d.get("timestamp", "")[:10], t
        except OSError:
            continue

def snippet(t, n=140):
    t = re.sub(r"\s+", " ", t)
    return t[:n] + ("…" if len(t) > n else "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0); ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--min-sessions", type=int, default=3); ap.add_argument("--json", action="store_true"); ap.add_argument("--no-examples", action="store_true", help="ne pas afficher d'extraits de messages")
    a = ap.parse_args()
    corr, manual, clusters = collections.defaultdict(list), [], collections.defaultdict(lambda: {"sessions": set(), "examples": []})
    sessions, days, n = set(), set(), 0
    for sid, day, t in user_messages(a.root, a.days):
        n += 1; sessions.add(sid); days.add(day); low = t.lower()
        for p in CORRECTION:
            if re.search(p, low): corr[p].append((sid, snippet(t))); break
        if any(re.search(p, low) for p in MANUAL): manual.append(snippet(t))
        m = re.search(VERBS, low)
        if m and len(t) < 300:
            obj = [w for w in re.findall(r"[a-zà-ÿ0-9\-]{5,}", low[m.end():]) if w not in STOP][:1]
            if not obj: continue   # « fais quoi ? » ne désigne aucune tâche
            key = m.group(0) + " " + obj[0]
            c = clusters[key]; c["sessions"].add(sid)
            if len(c["examples"]) < 3: c["examples"].append(snippet(t))
    out = {
        "total_sessions": len(sessions), "total_user_messages": n, "active_days": len(days),
        "top_correction_phrases": [{"phrase": p.lstrip("^").replace("[,.! ]", ""), "count": len(v), "sessions": len({s for s, _ in v}), "examples": [e for _, e in v[:3]]}
                                   for p, v in sorted(corr.items(), key=lambda kv: -len(kv[1]))[:8]],
        "repeated_task_clusters": [{"task": k, "sessions": len(v["sessions"]), "examples": v["examples"]}
                                   for k, v in sorted(clusters.items(), key=lambda kv: -len(kv[1]["sessions"])) if len(v["sessions"]) >= a.min_sessions][:12],
        "explicit_repetition_mentions": manual[:12],
    }
    if a.no_examples:
        for k in ("top_correction_phrases", "repeated_task_clusters"):
            for e in out[k]: e["examples"] = []
        out["explicit_repetition_mentions"] = []
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=2)); return
    print(f"{out['total_user_messages']} messages dans {out['total_sessions']} sessions ({out['active_days']} jours)")
    print("\nCorrections fréquentes :"); [print(f" - « {c['phrase']} » x{c['count']} ({c['sessions']} sessions) ex. {(c['examples'] or [''])[0]}") for c in out["top_correction_phrases"]]
    print("\nTâches répétées :"); [print(f" - {c['task']} ({c['sessions']} sessions) ex. {(c['examples'] or [''])[0]}") for c in out["repeated_task_clusters"]]
    print("\nAveux de travail manuel :"); [print(f" - {m}") for m in out["explicit_repetition_mentions"]]

if __name__ == "__main__":
    main()
