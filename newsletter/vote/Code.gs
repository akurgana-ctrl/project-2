/**
 * כח התערבות · מערכת ההצבעה של הניוזלטר
 *
 * כל כפתור הצבעה במייל מוביל לכתובת של ה-Web App הזה, עם ?v=<אפשרות>&id=<מזהה מנוי>.
 * הקול נרשם רק כשהדף נטען בדפדפן (לא בלחיצה עצמה), כך שסורקי אבטחה של מיילים לא סופרים קולות.
 * כל מנוי נספר פעם אחת: הצבעה חוזרת מעדכנת את הקול הקודם שלו.
 * ביום ראשון בבוקר נשלח סיכום התוצאות למייל של RESULTS_TO.
 *
 * בכל גיליון חדש: מעדכנים ISSUE ו-OPTIONS בלבד.
 */

const ISSUE = '1';
const OPTIONS = {
  a: 'מעיפים את אנדריי X',
  b: 'אבי מעוז, קח אחריות ופרוש',
};
const RESULTS_TO = 'akurgana@gmail.com';
const PRESSURE_GROUP_URL = 'https://chat.whatsapp.com/Cxw30pP21S34YVVI3dAeJi';
const SHEET_NAME = 'votes';

/** מריצים פעם אחת מהעורך: יוצר את הגיליון ואת השליחה השבועית. */
function setup() {
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('SHEET_ID')) {
    const ss = SpreadsheetApp.create('כח התערבות · הצבעות ניוזלטר');
    const sheet = ss.getSheets()[0];
    sheet.setName(SHEET_NAME);
    sheet.appendRow(['גיליון', 'מזהה מנוי', 'אפשרות', 'זמן']);
    sheet.setFrozenRows(1);
    props.setProperty('SHEET_ID', ss.getId());
  }
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'sendWeeklyResults')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('sendWeeklyResults')
    .timeBased().onWeekDay(ScriptApp.WeekDay.SUNDAY).atHour(8).create();
}

function doGet(e) {
  const v = String((e.parameter && e.parameter.v) || '').toLowerCase();
  const page = HtmlService.createTemplateFromFile('Thanks');
  page.option = OPTIONS[v] ? v : '';
  page.label = OPTIONS[v] || '';
  page.id = String((e.parameter && e.parameter.id) || '');
  page.groupUrl = PRESSURE_GROUP_URL;
  return page.evaluate()
    .setTitle('כח התערבות · הצבעה')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** נקרא מהדף אחרי שנטען. מזהה ריק (או משתנה שלא הוחלף) נרשם כקול אנונימי. */
function record(option, id) {
  if (!OPTIONS[option]) return false;
  const voter = /^\{\{.*\}\}$|^\*\|.*\|\*$/.test(id) ? '' : id;
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sheet = getSheet_();
    if (voter) {
      const rows = sheet.getDataRange().getValues();
      for (let i = 1; i < rows.length; i++) {
        if (String(rows[i][0]) === ISSUE && String(rows[i][1]) === voter) {
          sheet.getRange(i + 1, 3, 1, 2).setValues([[option, new Date()]]);
          return true;
        }
      }
    }
    sheet.appendRow([ISSUE, voter, option, new Date()]);
    return true;
  } finally {
    lock.releaseLock();
  }
}

function sendWeeklyResults() {
  const rows = getSheet_().getDataRange().getValues().slice(1)
    .filter(r => String(r[0]) === ISSUE);
  const counts = {};
  Object.keys(OPTIONS).forEach(k => counts[k] = 0);
  rows.forEach(r => { if (counts[r[2]] !== undefined) counts[r[2]]++; });
  const total = rows.length;

  const lines = Object.keys(OPTIONS).map(k => {
    const pct = total ? Math.round(counts[k] / total * 100) : 0;
    return '<tr><td style="padding:8px 0;font-weight:bold">' + OPTIONS[k] + '</td>' +
      '<td style="padding:8px 12px;text-align:left">' + counts[k] + ' קולות</td>' +
      '<td style="padding:8px 0;text-align:left;font-weight:bold;color:#1D2E67">' + pct + '%</td></tr>';
  }).join('');
  const winner = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];

  const html =
    '<div dir="rtl" style="font-family:Arial,sans-serif;color:#141A2E;max-width:520px">' +
    '<div style="background:#1D2E67;color:#fff;padding:16px 20px;font-size:20px;font-weight:bold">תוצאות ההצבעה · גיליון ' + ISSUE + '</div>' +
    '<div style="border-bottom:4px solid #F0C000"></div>' +
    '<div style="padding:16px 20px">' +
    '<p style="margin:0 0 12px">סה״כ הצביעו: <b>' + total + '</b></p>' +
    '<table style="width:100%;border-collapse:collapse">' + lines + '</table>' +
    (total ? '<p style="margin:16px 0 0;font-size:16px">הנושא שנבחר: <b>' + OPTIONS[winner] + '</b></p>' : '') +
    '</div></div>';

  MailApp.sendEmail({
    to: RESULTS_TO,
    subject: 'כח התערבות · תוצאות ההצבעה, גיליון ' + ISSUE,
    htmlBody: html,
  });
}

function getSheet_() {
  const id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!id) throw new Error('הריצו קודם את setup()');
  return SpreadsheetApp.openById(id).getSheetByName(SHEET_NAME);
}
