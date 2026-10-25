/**
 * כח התערבות · מעקב לחיצות בניוזלטר
 *
 * כל כפתור בניוזלטר מפנה לכאן עם ?l=<מזהה>. הסקריפט רושם את הלחיצה בגיליון
 * "clicks" ומעביר מיד ליעד שרשום בגיליון "links". מזהה שלא מופיע ב-links
 * לא מועבר לשום מקום, כך שאי אפשר להשתמש בקישור כדי להפנות לאתר זר.
 */
const SHEET_ID = '1FpN0MS3njxH8pd-GGv2c7r_FQQQVIeCwL-JcEnl_ivw';

function doGet(e) {
  const id = String((e && e.parameter && e.parameter.l) || '').trim().slice(0, 40);
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const link = ss.getSheetByName('links').getDataRange().getValues()
    .find(function (r) { return r[0] === id && r[2]; });

  if (!link) {
    return HtmlService.createHtmlOutput('<p dir="rtl" style="font-family:Arial">הקישור לא נמצא.</p>');
  }

  // the day goes in as text (leading ') so the sheet keeps it as yyyy-MM-dd
  const day = Utilities.formatDate(new Date(), 'Asia/Jerusalem', 'yyyy-MM-dd');
  ss.getSheetByName('clicks').appendRow([new Date(), id, link[3], "'" + day]);

  const page = HtmlService.createTemplateFromFile('Redirect');
  page.url = String(link[2]);
  return page.evaluate()
    .setTitle('כח התערבות')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
