#USERNAM TO MEDIA INSTA BOT(OG)
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright
import threading
import requests
import datetime
import time
import random
import re
import json
from io import BytesIO
from queue import Queue
import instaloader
# =========================
# BOT TOKEN
# =========================

TOKEN = "8429656135:AAFZcHr-sKqcp5eBYsJWeP8YaSlvCeoyp2s"
bot = telebot.TeleBot(TOKEN, threaded=True)
from queue import Queue

job_queue = Queue()
# =========================
# INSTAGRAM SESSION
# =========================

IG_SESSIONID = "31692982599%3AZxQHYK849fXkZU%3A5%3AAYid8-0UFtDvt87Ksva3MbKD7U5Kb4i6_DI5BQGU9A"

# =========================
# JOB SYSTEM

# =========================
# LOG FUNCTION
# =========================



def log(msg):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] {msg}")
    
# SESSION FUNCTION
import os
print("Files in project:", os.listdir())
# =========================
# INSTALOADER
# =========================

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    save_metadata=False
)

L.context._session.cookies.set(
    "sessionid",
    IG_SESSIONID,
    domain=".instagram.com"
)
print("Instaloader session active")
# =========================
# START PLAYWRIGHT
# =========================

print("Starting browser...")

def get_profile_posts(username, limit=100):

    posts = []

    profile = instaloader.Profile.from_username(
        L.context,
        username
    )

    for post in profile.get_posts():

        posts.append(post)

        if len(posts) >= limit:
            break

    log(f"Collected {len(posts)} posts using Instaloader")

    return posts
def extract_media(post):

    items = []

    # carousel
    if post.typename == "GraphSidecar":

        for node in post.get_sidecar_nodes():

            if node.is_video:
                items.append(("video", node.video_url))
            else:
                items.append(("photo", node.display_url))

    # single video
    elif post.is_video:

        items.append(("video", post.video_url))

    # single image
    else:

        items.append(("photo", post.url))

    return items

def get_post_from_url(post_url):

    try:

        shortcode = re.search(r"(?:p|reel|tv)/([^/?]+)", post_url).group(1)

        post = instaloader.Post.from_shortcode(
            L.context,
            shortcode
        )

        return post

    except Exception as e:

        log(f"Instaloader error: {e}")
        return None
# =========================
# SCRAPER
# =========================

def scrape_background(job, context):
    username = job.username
    log(f"Scraping started for {username}")

    try:

        page = context.new_page()

        url = f"https://www.instagram.com/{username}/"

        delay = random.uniform(4,7)
        time.sleep(delay)

        page.goto(url, wait_until="domcontentloaded")

        time.sleep(5)

        log(f"Current URL: {page.url}")
        if "challenge" in page.url:
            log("Instagram triggered a security challenge. Session is blocked.")
            page.close()
            return

        if "accounts/login" in page.url:
            log("Session expired. Instagram requires login.")
            page.close()
            return
        # wait until page loads
        page.wait_for_load_state("networkidle")

        # small delay for JS rendering
        time.sleep(3)

        # scroll once to trigger posts loading
        page.evaluate("""
        window.scrollBy({
            top: 800,
            left: 0,
            behavior: 'smooth'
        });
        """)
        time.sleep(random.uniform(4,6))

        for _ in range(20):

            if not job.running:
                break
            log("Scanning page for posts...")
            links = page.evaluate("""
                Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(h => h.includes('/p/') || h.includes('/reel/'))
            """)

            new_posts = 0

            for link in links:
                link = link.split("?")[0]

                if link not in job.posts:
                    job.posts.append(link)
                    new_posts += 1

            log(f"Collected posts: {len(job.posts)} (+{new_posts})")

            page.evaluate("""
            window.scrollBy({
                top: 1200,
                left: 0,
                behavior: 'smooth'
            });
            """)

            time.sleep(3)

        page.close()

    except Exception as e:
        log(f"Scraper error: {e}")

    finally:
        try:
            page.close()
        except:
            pass

def playwright_worker():

    log("Starting browser in worker thread...")

    with sync_playwright() as play:

        browser = play.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context()

        context.add_cookies([{
            "name": "sessionid",
            "value": IG_SESSIONID,
            "domain": ".instagram.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }])

        page = context.new_page()
        page.goto("https://www.instagram.com/")

        log("Instagram session activated")

        while True:

            job = job_queue.get()

            if job is None:
                break

            try:
                # fetch profile info first
               job.profile = get_profile_info(job.username, context)

               # then scrape posts
               scrape_background(job, context)
            except Exception as e:
                log(f"Worker error: {e}")

            job_queue.task_done()
def extract_username(text):

    text = text.strip()

    # remove query parameters
    text = text.split("?")[0]

    # if full URL
    match = re.search(r"instagram\.com/([^/]+)/?", text)

    if match:
        return match.group(1).lower()

    # if just username
    if re.match(r"^[a-zA-Z0-9._]+$", text):
        return text.lower()

    return None
# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "Send Instagram username"
    )
class Job:
    def __init__(self, username):
        self.username = username
        self.posts = []
        self.sent = 0
        self.running = True
        self.profile = None
user_jobs ={}
job_queue = Queue()

def get_profile_info(username, context):
    try:
        page = context.new_page()

        url = f"https://www.instagram.com/{username}/"
        page.goto(url, wait_until="domcontentloaded")

        time.sleep(5)

        # handle blocked / login
        if "login" in page.url or "challenge" in page.url:
            page.close()
            return None

        # extract data from page
        data = page.evaluate("""
        () => {
            const name = document.querySelector("h2")?.innerText || "";
            const bio = document.querySelector("div.-vDIg span")?.innerText || "";

            const stats = document.querySelectorAll("header section ul li span");
            
            let posts = stats[0]?.innerText || "0";
            let followers = stats[1]?.innerText || "0";
            let following = stats[2]?.innerText || "0";

            const profilePic = document.querySelector("header img")?.src || "";

            return {
                name,
                bio,
                posts,
                followers,
                following,
                profilePic
            };
        }
        """)

        page.close()
        return data

    except Exception as e:
        log(f"Profile fetch error: {e}")
        return None
# =========================
# USERNAME HANDLER
# =========================

@bot.message_handler(func=lambda m: True)
def profile_handler(message):

    username = extract_username(message.text)

    if not username:
        bot.send_message(
            message.chat.id,
            "❌ Invalid input.\n\nSend:\n• Instagram username\n• Instagram profile link"
        )
        return

    job = Job(username)
    user_jobs[message.chat.id] = job

    bot.send_message(
        message.chat.id,
        "🔍 Fetching profile info & posts...\nPlease wait..."
    )

    job_queue.put(job)

    # wait until profile OR posts fetched
    wait_time = 0
    while (job.profile is None and len(job.posts) == 0) and wait_time < 40:
        time.sleep(2)
        wait_time += 2

    # ❌ nothing fetched
    if job.profile is None and len(job.posts) == 0:
        bot.send_message(
            message.chat.id,
            "❌ Failed to fetch profile.\nInstagram may have blocked the request."
        )
        return

    # ✅ SEND PROFILE INFO FIRST
    if job.profile:
        p = job.profile

        text = f"""👤 Profile Info

Name: {p['name']}
Username: @{username}

Posts: {p['posts']}
Followers: {p['followers']}
Following: {p['following']}

Bio:
{p['bio']}
"""

        try:
            if p["profilePic"]:
                bot.send_photo(message.chat.id, p['profilePic'], caption=text)
            else:
                bot.send_message(message.chat.id, text)
        except:
            bot.send_message(message.chat.id, text)

    # ❌ if no posts
    if len(job.posts) == 0:
        bot.send_message(
            message.chat.id,
            "⚠️ Profile loaded but no posts found (private or blocked)."
        )
        retur@bot.message_handler(func=lambda m: True)
def profile_handler(message):

    username = extract_username(message.text)

    if not username:
        bot.send_message(
            message.chat.id,
            "❌ Invalid input.\n\nSend:\n• Instagram username\n• Instagram profile link"
        )
        return

    # create job
    job = Job(username)
    user_jobs[message.chat.id] = job

    bot.send_message(
        message.chat.id,
        "🔍 Fetching profile & collecting posts...\nPlease wait..."
    )

    # send job to worker
    job_queue.put(job)

    # =========================
    # WAIT FOR PROFILE
    # =========================
    wait_profile = 0
    while job.profile is None and wait_profile < 20:
        time.sleep(1)
        wait_profile += 1

    # =========================
    # SEND PROFILE INFO FIRST
    # =========================
    if job.profile:
        p = job.profile

        text = f"""👤 Profile Info

Name: {p['name']}
Username: @{username}

Posts: {p['posts']}
Followers: {p['followers']}
Following: {p['following']}

Bio:
{p['bio']}
"""

        try:
            bot.send_photo(message.chat.id, p['profilePic'], caption=text)
        except:
            bot.send_message(message.chat.id, text)

    else:
        bot.send_message(
            message.chat.id,
            "⚠️ Could not fetch profile info (private/blocked)."
        )

    # =========================
    # WAIT FOR POSTS
    # =========================
    wait_time = 0
    while len(job.posts) == 0 and wait_time < 40:
        time.sleep(2)
        wait_time += 2

    # =========================
    # CHECK POSTS
    # =========================
    if len(job.posts) == 0:
        bot.send_message(
            message.chat.id,
            "❌ Failed to collect posts.\nInstagram may have blocked the request."
        )
        return

    # =========================
    # SHOW BUTTONS
    # =========================
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Download 10 Posts", callback_data="next"),
        InlineKeyboardButton("Cancel", callback_data="cancel")
    )

    bot.send_message(
        message.chat.id,
        f"✅ {len(job.posts)} posts ready.\nPress download.",
        reply_markup=markup
    )
