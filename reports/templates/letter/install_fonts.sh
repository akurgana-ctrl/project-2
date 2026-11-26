#!/bin/sh
# Install the David font for PDF conversion (Culmus "David CLM", GPL) and map "David" to it,
# so that soffice embeds David in the PDF and does not fall back to another font.
set -e
fc-list | grep -qi "David CLM" && exit 0
T=$(mktemp -d)
curl -sSL --max-time 120 -o "$T/c.tgz" "https://downloads.sourceforge.net/project/culmus/culmus/0.133/culmus-0.133.tar.gz"
tar xzf "$T/c.tgz" -C "$T"
mkdir -p /usr/local/share/fonts/culmus /etc/fonts/conf.d
cp "$T"/culmus-0.133/DavidCLM* /usr/local/share/fonts/culmus/
cat > /etc/fonts/conf.d/09-david.conf <<'XML'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="pattern">
    <test qual="any" name="family"><string>David</string></test>
    <edit name="family" mode="assign" binding="strong"><string>David CLM</string></edit>
  </match>
</fontconfig>
XML
fc-cache -f >/dev/null
rm -rf "$T"
fc-match David
