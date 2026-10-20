// The WhatsApp appeal to the Knesset Speaker, opened right after a donation.
window.APPEAL = {
  number: "972547484840",
  message: `שלום יו״ר הכנסת, אמיר אוחנה.
פונה אליך באופן אישי.
היום חבר כנסת לא יכול להניח הצעת חוק על שולחן הכנסת. במערכת החקיקה "סנהדרין" הרשאות החקיקה ניתנות רק ליועצים המשפטיים, גורם שכלל לא מופיע בתקנון הכנסת.
אבקש ממך לפעול כדי להחזיר לחברי הכנסת את הכלים לחוקק בעצמם.
אשמח לראות שינוי בקרוב. תודה.`,
};
window.APPEAL.url = `https://wa.me/${window.APPEAL.number}?text=${encodeURIComponent(window.APPEAL.message)}`;
