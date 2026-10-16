# improve-system

Un skill pour Claude Code qui relit **ton** historique de conversations, en local, et te dit :
- les corrections qui reviennent (« refais », « c'est pas ça »…) ;
- les tâches que tu redemandes dans plusieurs sessions ;
- les moments où tu dis « je le fais toujours à la main » ;
puis propose les skills à créer, et les écrit après ton accord.

Local, sans dépendance (Python 3 standard), aucun envoi de données.

## Installer
```bash
git clone https://github.com/HelloPixDig/improve-system ~/.claude/skills/improve-system
```
Puis dans Claude Code : « analyse mon historique et propose-moi des skills ».

## Utiliser le script seul
```bash
python3 scripts/scan_history.py --days 30
python3 scripts/scan_history.py --days 30 --json --no-examples
```

## Limites
- Détection par mots-clés (français et anglais) : le skill s'appuie sur la relecture du résumé par Claude.
- Il faut quelques semaines d'historique pour un signal fiable.
- Les extraits peuvent contenir des données personnelles : relis avant de partager.

Licence MIT.
