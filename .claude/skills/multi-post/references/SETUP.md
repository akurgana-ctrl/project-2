# הקמת Postiz על השרת של הארגון (פעם אחת)

המקורות: docs.postiz.com/self-host (נבדק 11/2026). זמן משוער: שעתיים לשרת, ועוד 15–40 דקות לכל רשת.

## 0. מה צריך
- שרת Linux עם Docker, **לפחות 4GB RAM** ו-2 ליבות (Postiz + Postgres + Redis + Temporal).
- **דומיין עם HTTPS** (למשל `social.<הדומיין-של-הארגון>`). בלי HTTPS טיקטוק, Meta ולינקדאין לא יאשרו את כתובת החזרה.
- **דפי תנאי שימוש ופרטיות** בכתובת ציבורית ב-HTTPS. טיקטוק ו-Meta דורשים אותם, ואפשר לשים אותם באתר תוכנית הכנסת.

## 1. התקנה
```bash
mkdir -p /opt/postiz && cd /opt/postiz
curl -fsSLO https://raw.githubusercontent.com/gitroomhq/postiz-app/main/docker-compose.yaml
nano docker-compose.yaml
```
לשנות ב-`environment`:
```yaml
MAIN_URL: 'https://social.example.org'
FRONTEND_URL: 'https://social.example.org'
NEXT_PUBLIC_BACKEND_URL: 'https://social.example.org/api'
JWT_SECRET: '<מחרוזת אקראית ארוכה: openssl rand -hex 32>'
DISABLE_REGISTRATION: 'true'      # אחרי שנרשמת בעצמך פעם אחת
API_LIMIT: 90                     # ב-compose ברירת המחדל היא 30 פוסטים בשעה
RUN_CRON: 'true'
```
ולהחליף את הסיסמאות של Postgres בקובץ. אחר כך:
```bash
docker compose up -d
```
HTTPS: reverse proxy (Caddy הכי פשוט) מ-`social.example.org` ל-`localhost:4007`.
```
social.example.org {
  reverse_proxy localhost:4007
}
```
**הכתובות `FRONTEND_URL` ו-`NEXT_PUBLIC_BACKEND_URL` חייבות להתאים בדיוק לכתובת בדפדפן** (פרוטוקול ופורט). אחרת ההתחברות נשברת ומופיעה השגיאה "Origin not allowed".

## 2. כל רשת = אפליקציית מפתחים + משתני סביבה
כתובת החזרה (Redirect URI) תמיד: `https://social.example.org/integrations/social/<ספק>`.
אחרי כל שינוי במשתנים: `docker compose up -d`, ואז בממשק של Postiz: **Add Channel**.

| רשת | איפה פותחים | משתנים | ספק בכתובת החזרה | ⚠ מגבלה עד אישור |
|---|---|---|---|---|
| **פייסבוק + אינסטגרם עסקי** | developers.facebook.com ← App מסוג Business | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | `facebook`, `instagram` | במצב פיתוח עובד רק למי שיש לו תפקיד באפליקציה. לחשבונות של הארגון זה מספיק. אינסטגרם חייב להיות חשבון Business/Creator שמקושר לדף פייסבוק. |
| **אינסטגרם בלי פייסבוק** | אותו מקום, מוצר Instagram API with Instagram Login | `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` | `instagram-standalone` | כנ"ל |
| **טיקטוק** | developers.tiktok.com/apps ← Login Kit + Content Posting API (Direct Post) | `TIKTOK_CLIENT_ID`, `TIKTOK_CLIENT_SECRET` | `tiktok` | **עד ה-audit: הסרטונים פרטיים (SELF_ONLY), החשבון חייב להיות פרטי, ועד 5 משתמשים ביום.** מגישים audit מיד. בינתיים להשתמש ב-`content_posting_method: "UPLOAD"`: הסרטון מגיע לתיבה באפליקציה, ומשם מפרסמים בלחיצה (תוך 24 שעות). |
| **יוטיוב** | console.cloud.google.com ← YouTube Data API v3 + OAuth client (Web) | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` | `youtube` | **פרויקט שלא עבר אימות מעלה סרטונים כפרטיים.** מגישים את בקשת ה-audit של YouTube API. בינתיים משנים ידנית לציבורי ב-YouTube Studio. |
| **X** | developer.x.com ← Project + App, User auth: Read and write, Web App | `X_API_KEY`, `X_API_SECRET` | `x` | המסלול החינמי מוגבל בכמות פוסטים בחודש. לבדוק את המחיר העדכני. |
| **לינקדאין** | linkedin.com/developers ← Share on LinkedIn + Sign In with OpenID | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | `linkedin`, `linkedin-page` | פרסום **לעמוד חברה** דורש את Community Management API, שמחייב אישור של לינקדאין. לפרופיל אישי זה עובד מיד. |
| **טלגרם** | ב-@BotFather: newbot ← לכבות Group Privacy ← להוסיף את הבוט **כמנהל** לערוץ/קבוצה | `TELEGRAM_BOT_NAME` (בלי @), `TELEGRAM_TOKEN` | – | טוקן אחד = התקנה אחת. אסור להשתמש באותו בוט בשני מקומות (שגיאת 409). |

## 3. מפתח ה-API ובדיקה
Postiz ← Settings ← **Public API** ← להעתיק את המפתח. אחר כך מהמחשב או מהסשן:
```bash
export POSTIZ_URL=https://social.example.org/api
export POSTIZ_API_KEY=<המפתח>          # לא לשמור בקובץ בריפו
node .claude/skills/multi-post/scripts/postiz.mjs check
node .claude/skills/multi-post/scripts/postiz.mjs channels
```
בסשן ענן של Claude: לבקש מ-Claude לשמור את המפתח כסוד רשת (`request_credential`) ל-host של השרת, במקום `export`.

## 4. (רשות) Postiz כמחבר ב-claude.ai
ל-Postiz יש שרת MCP מובנה. אם מוסיפים אותו ב-claude.ai ← Settings ← Connectors, Claude יכול לפרסם גם בלי הסקריפט, ודף מרכז הפרסום יכול לפרסם ישירות מהטלפון (צריך לעדכן את הדף). יש באג פתוח בהתחברות ה-OAuth של ה-MCP כשה-backend יושב תחת `/api` (gitroomhq/postiz-app#2426), אז לבדוק לפני שסומכים עליו.

## 5. וואטסאפ
אין API לערוצי וואטסאפ, וה-Cloud API של וואטסאפ עסקי לא שולח לקבוצות. לכן הערוץ מקבל חבילה מוכנה: קובץ ונוסח, וכפתור "שתף" בטלפון. לא להתקין גשרים לא רשמיים, כי הם מסכנים את המספר של הארגון.
