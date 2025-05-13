from bs4 import BeautifulSoup
import requests
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import datetime

TELEGRAM_BOT_TOKEN = "7832602909:AAHF_4wMrfGoCcef5WDaan3STejesdlFxHA"
TELEGRAM_CHAT_ID = "-4673685313"
last_checked = "尚未啟動"
daily_data = []

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
    global last_checked
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
    last_checked = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return signals

async def send_alerts(bot, signals):
    for asset in signals:
        msg = (
            f"🚨 <b>{asset['name']}</b> 符合拉升條件\\n"
            f"APR: <b>{asset['APR']}%</b>\\n"
            f"OI: <b>{asset['OI']/1e6:.2f}M</b>\\n"
            f"OI/MCap: <b>{asset['OI/MCap']}</b>\\n"
            f"Vol/MCap: <b>{asset['Vol/MCap']}</b>\\n"
            f"#Altcoin #Signal"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode=telegram.constants.ParseMode.HTML)

async def check_loop(app):
    seen = set()
    while True:
        try:
            assets = fetch_filtered_assets()
            new_assets = [a for a in assets if a['name'] not in seen]
            await send_alerts(app.bot, new_assets)
            daily_data.extend(new_assets)
            seen.update(a['name'] for a in new_assets)
        except Exception as e:
            await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ Bot 錯誤: {e}")
        await asyncio.sleep(300)

async def daily_report_loop(app):
    while True:
        now = datetime.datetime.now()
        if now.hour == 23 and now.minute == 59:
            if daily_data:
                msg = f"📊 <b>{now.strftime('%Y-%m-%d')}</b> 當日異常資產報告\\n符合條件資產數：<b>{len(daily_data)}</b>\\n"
                for asset in daily_data:
                    msg += (
                        f"\\n<b>{asset['name']}</b> APR: {asset['APR']}% | "
                        f"OI: {asset['OI']/1e6:.2f}M | OI/MCap: {asset['OI/MCap']} | Vol/MCap: {asset['Vol/MCap']}"
                    )
                await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode=telegram.constants.ParseMode.HTML)
            daily_data.clear()
        await asyncio.sleep(60)

async def check_command(update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"✅ Bot 運行中\\n上次檢查時間：<b>{last_checked}</b>\\n"
    msg += f"今日已發現 {len(daily_data)} 筆異常資產" if daily_data else "今日尚未發現異常資產"
    await update.message.reply_text(msg, parse_mode=telegram.constants.ParseMode.HTML)

async def post_init(app):
    asyncio.create_task(check_loop(app))
    asyncio.create_task(daily_report_loop(app))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("check", check_command))
    app.run_polling()
