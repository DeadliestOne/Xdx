import re
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

def scrape_proxies(urls):
    proxies = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            proxies += re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text) 
        except Exception as e:
            print(f"ERROR SCRAPING {url}: {e}")
    return proxies

def save_and_send(update, context, proxies, file_name):
    bot = context.bot
    chat_id = update.effective_chat.id

    if context.user_data.get("last_message"):
        bot.delete_message(chat_id=chat_id, message_id=context.user_data["last_message"])
 
    if proxies:
        with open(file_name, "w") as file:
            file.write("\n".join(proxies))
        message = bot.send_message(chat_id, f"𝗦𝗖𝗥𝗔𝗣𝗘𝗗 {len(proxies)} 𝐏𝐑𝐎𝐗𝐈𝐄𝐒! 𝐒𝐄𝐍𝐃𝐈𝐍𝐆 𝐓𝐇𝐄 𝐅𝐈𝐋𝐄...")
        context.user_data["last_message"] = message.message_id
        bot.send_document(chat_id, open(file_name, "rb"))
    else:
        message = bot.send_message(chat_id, "𝐍𝐎 𝐏𝐑𝐎𝐗𝐈𝐄𝐒 𝐅𝐎𝐔𝐍𝐃. 𝐏𝐋𝐄𝐀𝐒𝐄 𝐓𝐑𝐘 𝐀𝐆𝐀𝐈𝐍 𝐋𝐀𝐓𝐄𝐑.")
        context.user_data["last_message"] = message.message_id

def scrape_http(update: Update, context: CallbackContext) -> None:
    urls = [
        "http://proxysearcher.sourceforge.net/Proxy%20List.php?type=http",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://openproxy.space/list/http",
    "https://openproxylist.xyz/http.txt",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
    "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/https.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
    "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/https.txt",
    "https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxy-list/data.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/https.txt",
    "https://rootjazz.com/proxies/proxies.txt",
    "https://sheesh.rip/http.txt",
    "https://spys.me/proxy.txt",
    "https://www.freeproxychecker.com/result/http_proxies.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://www.proxyscan.io/download?type=http",
    ]
    message = update.message.reply_text("𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆 𝐇𝐓𝐓𝐏 𝐏𝐑𝐎𝐗𝐈𝐄𝐒...")
    context.user_data["last_message"] = message.message_id

    proxies = scrape_proxies(urls)
    save_and_send(update, context, proxies, "r4x-proxy-http.txt")

def scrape_socks4(update: Update, context: CallbackContext) -> None:
    urls = [
        "http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    "https://openproxy.space/list/socks4",
    "https://openproxylist.xyz/socks4.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
    "https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/socks4.txt",
    "https://spys.me/socks.txt",
    "https://www.freeproxychecker.com/result/socks4_proxies.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://www.proxyscan.io/download?type=socks4",
    ]
    message = update.message.reply_text("𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆 𝐒𝐎𝐂𝐊𝐒𝟒 𝐏𝐑𝐎𝐗𝐈𝐄𝐒...")
    context.user_data["last_message"] = message.message_id

    proxies = scrape_proxies(urls)
    save_and_send(update, context, proxies, "r4x-proxy-socks4.txt")

def scrape_socks5(update: Update, context: CallbackContext) -> None:
    urls = [
        "http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    "https://openproxy.space/list/socks5",
    "https://openproxylist.xyz/socks5.txt",
    "https://proxyspace.pro/socks5.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/socks5.txt",
    "https://spys.me/socks.txt",
    "https://www.freeproxychecker.com/result/socks5_proxies.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://www.proxyscan.io/download?type=socks5",
    ]
    message = update.message.reply_text("𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆 𝐒𝐎𝐂𝐊𝐒𝟓 𝐏𝐑𝐎𝐗𝐈𝐄𝐒...")
    context.user_data["last_message"] = message.message_id

    proxies = scrape_proxies(urls)
    save_and_send(update, context, proxies, "r4x-proxy-socks5.txt")

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    welcome_message = (
        f"𝐖𝐄𝐋𝐂𝐎𝐌𝐄!, {user.first_name}!\n\n"
        "𝐈'𝐌 𝐏𝐑𝐎𝐗𝐘 𝐒𝐂𝐑𝐀𝐏𝐄𝐑 𝐁𝐎𝐓. 𝐔𝐒𝐄 𝐓𝐇𝐄 𝐅𝐎𝐋𝐋𝐎𝐖𝐈𝐍𝐆 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒 𝐓𝐎 𝐒𝐂𝐑𝐀𝐏𝐄 𝐏𝐑𝐎𝐗𝐈𝐄𝐒:\n\n"
        "/http - 𝐒𝐂𝐑𝐀𝐏𝐄 𝐇𝐓𝐓𝐏 𝐏𝐑𝐎𝐗𝐈𝐄𝐒\n"
        "/socks4 - 𝐒𝐂𝐑𝐀𝐏𝐄 𝐒𝐎𝐂𝐊𝐒𝟒 𝐏𝐑𝐎𝐗𝐈𝐄𝐒\n"
        "/socks5 - 𝐒𝐂𝐑𝐀𝐏𝐄 𝐒𝐎𝐂𝐊𝐒𝟓 𝐏𝐑𝐎𝐗𝐈𝐄𝐒\n\n"
        "𝐒𝐈𝐌𝐏𝐋𝐘 𝐓𝐘𝐏𝐄 𝐀𝐍𝐘 𝐂𝐎𝐌𝐌𝐀𝐍𝐃, 𝐀𝐍𝐃 𝐈'𝐥𝐥 𝐒𝐂𝐑𝐀𝐏𝐄 𝐏𝐑𝐎𝐗𝐈𝐄𝐒 𝐅𝐎𝐑 𝐘𝐎𝐔 𝐖𝐈𝐓𝐇𝐈𝐍 𝐀 𝐌𝐈𝐍𝐔𝐓𝐄!"
    )
    update.message.reply_text(welcome_message)

def main():

    updater = Updater("7924809623:AAFwfB2w1kZS-veic8dkbj4GsRR03Ggr-6k")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("http", scrape_http))
    dispatcher.add_handler(CommandHandler("socks4", scrape_socks4))
    dispatcher.add_handler(CommandHandler("socks5", scrape_socks5))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
