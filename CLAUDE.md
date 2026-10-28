# CLAUDE.md

הריפו מכיל שלושה דברים נפרדים:
- **אתר תוכנית הכנסת** (שורש הריפו) – ראו `README.md`. מתפרסם מהענף `gh-pages`.
- **דיווח יומי ושבועי** (`reports/`) – כשהמשתמש מדביק רשימה של מה שעשה היום, או מבקש "מצגת שבועית" / "מה פתוח?" / "תקן: …", עבוד **בדיוק** לפי `reports/PROCESS.md`. קרא קודם את `reports/config.md`.
- **מכתבים ונייר עמדה רשמיים** – עבוד לפי `reports/templates/letter/README.md`. לא לשמור את המכתבים עצמם בריפו, כי הוא ציבורי.
- **יומן כוח התערבות** (`reports/journal.md`) – כשהמשתמש אומר משהו שצריך לזכור או לעשות ("צריך…", "תזכיר לי…"), עבוד לפי סעיף ד ב-`reports/PROCESS.md`. היומן מוצג כדף קבוע: https://claude.ai/artifact/ViMJf8DoyppsSYtb3CatYX
- **סרטונים (HyperFrames)** – הסקילים `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use` מותקנים ב-`.claude/skills/` (מקור: heygen-com/hyperframes, קומיט 2c3d1e0). את פרויקטי הווידאו ליצור מחוץ לריפו (בתיקיית scratchpad), ולא לשמור בו קובצי MP4. עדכון: `npx hyperframes skills update` ואז להעתיק מחדש.
