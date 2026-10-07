# כח התערבות – התוכנית לכנסת

אתר סטטי (HTML/CSS/JS, בלי בנייה): קרוסלת חברי דירקטוריון ← קרוסלת מטרות ← ציר שלבים ולוח זמנים.

## עריכה מתוך האתר
כפתור העיפרון הקטן בפינה השמאלית התחתונה פותח את מצב העריכה.
בפעם הראשונה בכל דפדפן צריך להדביק **מפתח GitHub (Fine-grained token)**:

1. https://github.com/settings/personal-access-tokens/new
2. Repository access → **Only select repositories** → `project-2`
3. Permissions → Repository permissions → **Contents: Read and write**
4. Generate → מעתיקים ומדביקים בחלון ההגדרות באתר

במצב עריכה אפשר להוסיף, לערוך, למחוק ולשנות סדר של חברי דירקטוריון (כולל העלאת תמונה), מטרות ושלבים.
**שמירה** (או Ctrl+S) שומרת את השינויים בריפו (`data.json` + תמונות ב-`assets/directors/`), ו-GitHub Pages מעדכן את האתר לכולם תוך כדקה.
המפתח נשמר רק בדפדפן שבו הוזן. בלי מפתח – אין אפשרות לשמור, גם אם מישהו לוחץ על העיפרון.

## התוכן
כל התוכן נמצא ב-`data.json` (אפשר לערוך גם ידנית). סטטוס של שלב: `done` / `active` / `planned`.

## צפייה מקומית
```
python3 -m http.server 8000
```
ואז לפתוח http://localhost:8000 (פתיחה ישירה של הקובץ לא תטען את התוכן).

## פרסום
האתר החי: https://akurgana-ctrl.github.io/project-2/
GitHub Pages מפרסם מהענף **`gh-pages`** – זה הענף החי, והעורך שומר אליו.
כל שמירה מהעורך מתפרסמת לכולם תוך כדקה.
