
from bs4 import BeautifulSoup
import requests
import telegram
import time

# Telegram config
TELEGRAM_BOT_TOKEN = "7832602909:AAHF_4wMrfGoCcef5WDaan3STejesdlFxHA"
TELEGRAM_CHAT_ID = "-4673685313"
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def parse_number(text):
    text = text.replace(',', '').upper()
    if 'B' in text:
        return float(text.replace('B', '')) * 1e9
    elif 'M' in text:
        return float(text.replace('M', '')) * 1e6
    elif text.endswith('%'):
        return float(text.replace('%', ''))
    return float(text)

def fetch_filtered_assets():
    url = "https://botvsing.com"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all("tr")[1:]

    signals = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        try:
            name = cols[0].text.strip()
            apr = parse_number(cols[1].text.strip())
            oi = parse_number(cols[2].text.strip())
            mcap = parse_number(cols[3].text.strip())
            vol = parse_number(cols[4].text.strip())
            oi_ratio = oi / mcap if mcap else 0
            vol_ratio = vol / mcap if mcap else 0

            if apr > 10 and oi > 20_000_000 and oi_ratio > 0.2 and vol_ratio > 0.3:
                signals.append({
                    "name": name,
                    "APR": apr,
                    "OI": oi,
                    "OI/MCap": round(oi_ratio, 3),
                    "Vol/MCap": round(vol_ratio, 3)
                })
        except:
            continue
    return signals

def send_alerts(signals):
    for asset in signals:
        msg = (
            f"🚨 <b>{asset['name']}</b> 符合拉升條件\n"
            f"APR: <b>{asset['APR']}%</b>\n"
            f"OI: <b>{asset['OI']/1e6:.2f}M</b>\n"
            f"OI/MCap: <b>{asset['OI/MCap']}</b>\n"
            f"Vol/MCap: <b>{asset['Vol/MCap']}</b>\n"
            f"#Altcoin #Signal"
        )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode=telegram.constants.ParseMode.HTML)

def run_bot():
    seen = set()
    while True:
        try:
            assets = fetch_filtered_assets()
            new_assets = [a for a in assets if a['name'] not in seen]
            send_alerts(new_assets)
            seen.update(a['name'] for a in new_assets)
        except Exception as e:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ Bot 錯誤: {e}")
        time.sleep(300)

run_bot()
