# CLAUDE.md

הריפו מכיל שלושה דברים נפרדים:
- **אתר תוכנית הכנסת** (שורש הריפו) – ראו `README.md`. מתפרסם מהענף `gh-pages`.
- **דיווח יומי ושבועי** (`reports/`) – כשהמשתמש מדביק רשימה של מה שעשה היום, או מבקש "מצגת שבועית" / "מה פתוח?" / "תקן: …", עבוד **בדיוק** לפי `reports/PROCESS.md`. קרא קודם את `reports/config.md`.
- **מכתבים ונייר עמדה רשמיים** – עבוד לפי `reports/templates/letter/README.md`. לא לשמור את המכתבים עצמם בריפו, כי הוא ציבורי.
- **יומן כוח התערבות** (`reports/journal.md`) – כשהמשתמש אומר משהו שצריך לזכור או לעשות ("צריך…", "תזכיר לי…"), עבוד לפי סעיף ד ב-`reports/PROCESS.md`. היומן מוצג כדף קבוע: https://claude.ai/artifact/ViMJf8DoyppsSYtb3CatYX
- **סרטונים (HyperFrames)** – הסקילים `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use` וגם `slideshow` (מצגות חיות דרך `hyperframes present`) מותקנים ב-`.claude/skills/` (מקור: heygen-com/hyperframes, קומיט 8195920). את פרויקטי הווידאו ליצור מחוץ לריפו (בתיקיית scratchpad), ולא לשמור בו קובצי MP4. עדכון: `npx hyperframes skills update` ואז להעתיק מחדש.
- **סקילים לעיצוב** (מהסרטון "5 Plugins That Turn Claude Into a Design Genius"), מותקנים ב-`.claude/skills/`: `taste-skill` (Leonxlnx/taste-skill, קומיט 12af471), `impeccable` (pbakaus/impeccable, קומיט 02523ae, בלי ה-hook שלו), `playwright-cli` (microsoft/playwright-cli, קומיט b1a5903; בכל סשן חדש להריץ `npm install -g @playwright/cli@latest`), `img2threejs` (hoainho/img2threejs, קומיט 3e7099e), `awesome-design-md` (VoltAgent/awesome-design-md, קומיט fcc7028; ה-SKILL.md נכתב כאן כי במקור זה רק אוסף). עדכון: לשכפל מחדש ולהעתיק.
