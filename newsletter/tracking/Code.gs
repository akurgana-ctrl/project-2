/**
 * כח התערבות · מעקב לחיצות בניוזלטר
 *
 * כל כפתור בניוזלטר מפנה לכאן עם ?l=<מזהה>&i=<מספר גיליון>. הסקריפט רושם את הלחיצה בגיליון
 * "clicks" ומעביר מיד ליעד שרשום בגיליון "links". מזהה שלא מופיע ב-links
 * לא מועבר לשום מקום, כך שאי אפשר להשתמש בקישור כדי להפנות לאתר זר.
 *
 * פתיחות: בכל מייל יש תמונה זעירה שנטענת מכאן עם ?o=<מספר גיליון>. כל טעינה נרשמת
 * בגיליון "opens". אין בה שום פרט על הקורא.
 */
const SHEET_ID = '1FpN0MS3njxH8pd-GGv2c7r_FQQQVIeCwL-JcEnl_ivw';

function doGet(e) {
  if (e && e.parameter && e.parameter.o !== undefined) return logOpen(e.parameter.o);
  const id = String((e && e.parameter && e.parameter.l) || '').trim().slice(0, 40);
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const link = ss.getSheetByName('links').getDataRange().getValues()
    .find(function (r) { return r[0] === id && r[2]; });

  if (!link) {
    return HtmlService.createHtmlOutput('<p dir="rtl" style="font-family:Arial">הקישור לא נמצא.</p>');
  }

  const issue = String(e.parameter.i || link[3] || '').replace(/\D/g, '').slice(0, 4);
  ss.getSheetByName('clicks').appendRow([new Date(), id, issue, today()]);

  const page = HtmlService.createTemplateFromFile('Redirect');
  page.url = String(link[2]);
  return page.evaluate()
    .setTitle('כח התערבות')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// the day goes in as text (leading ') so the sheet keeps it as yyyy-MM-dd
function today() {
  return "'" + Utilities.formatDate(new Date(), 'Asia/Jerusalem', 'yyyy-MM-dd');
}

function logOpen(issue) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = ss.getSheetByName('opens') || ss.insertSheet('opens');
  if (sheet.getLastRow() === 0) sheet.appendRow(['time', 'issue', 'day']);
  sheet.appendRow([new Date(), String(issue).replace(/\D/g, '').slice(0, 4), today()]);
  // Apps Script cannot return image bytes; an empty reply is enough for the request to be counted
  return ContentService.createTextOutput('');
}
