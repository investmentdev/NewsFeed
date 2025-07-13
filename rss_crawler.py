import requests
from dateutil import parser
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import jdatetime
from collections import defaultdict
import os
import time

def fetch_rss_content(url):
    response = requests.get(url, timeout=10)
    return response.content
print("update 2")
# --- Mappings ---
PERSIAN_WEEKDAYS = {
    "Saturday": "شنبه",
    "Sunday": "یک‌شنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنج‌شنبه",
    "Friday": "جمعه"
}

PERSIAN_MONTHS = {
    "Farvardin": "فروردین",
    "Ordibehesht": "اردیبهشت",
    "Khordad": "خرداد",
    "Tir": "تیر",
    "Mordad": "مرداد",
    "Shahrivar": "شهریور",
    "Mehr": "مهر",
    "Aban": "آبان",
    "Azar": "آذر",
    "Dey": "دی",
    "Bahman": "بهمن",
    "Esfand": "اسفند"
}

def to_persian_digits(s):
    english_digits = "0123456789"
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    return s.translate(str.maketrans(english_digits, persian_digits))

# --- Feed Dictionary ---
feeds = {
    "اقتصاد": {
        "تسنیم": "https://www.tasnimnews.com/fa/rss/feed/0/7/7/%D8%A7%D9%82%D8%AA%D8%B5%D8%A7%D8%AF%DB%8C",
        "اقتصاد آنلاین": "https://www.eghtesadonline.com/fa/rss/8",
        "باشگاه خبرنگاران": "https://www.yjc.ir/fa/rss/6",
        "ایرنا": "https://www.irna.ir/rss/tp/20",
        "ایسنا": "https://www.isna.ir/rss/tp/34",
        "جام جم": "https://jamejamonline.ir/fa/rss/15",
        "جوان": "https://www.javanonline.ir/fa/rss/6",
        "همشهری": "https://www.hamshahrionline.ir/rss/tp/10"
    },
    "بورس، بانک و بیمه": {
        "(بورس) ایرنا": "https://www.irna.ir/rss/tp/1001669",
        "(بورس) اقتصاد آنلاین": "https://www.eghtesadonline.com/fa/rss/9",
        "بورس پرس": "https://boursepress.ir/rss/feeds/featured",
        "(بانک و بیمه) ایرنا": "https://www.irna.ir/rss/tp/26",
        "(بانک و بیمه) اقتصاد آنلاین": "https://www.eghtesadonline.com/fa/rss/25",
        "(بورس) همشهری": "https://www.hamshahrionline.ir/rss/tp/683",
        "(بانک و بیمه) همشهری": "https://www.hamshahrionline.ir/rss/tp/92"
    },
    "صنعت، معدن و تجارت": {
        "ایرنا": "https://www.irna.ir/rss/tp/23",
        "اقتصاد آنلاین": "https://www.eghtesadonline.com/fa/rss/26",
        "ایسنا": "https://www.isna.ir/rss/tp/74",
        "همشهری": "https://www.hamshahrionline.ir/rss/tp/87"
    },
    "سیاسی و اجتماعی": {
        "(جهانی) ایرنا": "https://www.irna.ir/rss/tp/1",
        "(بین‌الملل) تسنیم": "https://www.tasnimnews.com/fa/rss/feed/0/7/8/%D8%A8%DB%8C%D9%86-%D8%A7%D9%84%D9%85%D9%84%D9%84",
        "(جهانی) باشگاه خبرنگاران": "https://www.yjc.ir/fa/rss/9",
        "(سیاسی) تسنیم": "https://www.tasnimnews.com/fa/rss/feed/0/7/1/%D8%B3%DB%8C%D8%A7%D8%B3%DB%8C",
        "(سیاسی) اقتصاد آنلاین": "https://www.eghtesadonline.com/fa/rss/11",
        "(سیاسی) باشگاه خبرنگاران": "https://www.yjc.ir/fa/rss/3",
        "(سیاسی) همشهری": "https://www.hamshahrionline.ir/rss/tp/6",
        "(بین‌المللی) همشهری": "https://www.hamshahrionline.ir/rss/tp/11",
        "(سیاسی) جام جم": "https://jamejamonline.ir/fa/rss/17",
        "(جهانی) جام جم": "https://jamejamonline.ir/fa/rss/12",
        "(سیاسی) جوان": "https://www.javanonline.ir/fa/rss/3",
        "(جهانی) جوان": "https://www.javanonline.ir/fa/rss/2",
        "(جهانی) ایسنا": "https://www.isna.ir/rss/tp/17"
    }
}


seen_links = set()
category_articles = defaultdict(list)

for category, sources in feeds.items():
    for source, url in sources.items():
        print(f"📥 Reading from: {source} -> {url}")
        try:
            rss_content = fetch_rss_content(url)
            soup = BeautifulSoup(rss_content, "xml")
            items = soup.find_all("item")
        except Exception:
            continue

        for item in items[:]:
            try:
                title = item.title.text.strip()
                link = item.link.text.strip()
                if link in seen_links:
                    continue
                seen_links.add(link)

                pub_date = item.pubDate.text.strip()
                try:
                    
                    try:
                        dt = parser.parse(pub_date)
                        if dt.tzinfo is None:
                            # Assume GMT if no timezone is present
                            dt = dt.replace(tzinfo=ZoneInfo("GMT"))
                        dt_tehran = dt.astimezone(ZoneInfo("Asia/Tehran"))
                        jd = jdatetime.datetime.fromgregorian(datetime=dt_tehran)
                    
                        weekday_en = jd.strftime('%A')
                        weekday_fa = PERSIAN_WEEKDAYS.get(weekday_en, weekday_en)
                    
                        day = to_persian_digits(jd.strftime('%d'))
                        month_en = jd.strftime('%B')
                        month_fa = PERSIAN_MONTHS.get(month_en, month_en)
                        year = to_persian_digits(jd.strftime('%Y'))
                        time_str = to_persian_digits(jd.strftime('%H:%M'))
                    
                        date_str = f"{day} {month_fa} {year}"
                        pub_date_formatted = f"{weekday_fa}، {date_str} ⏰ {time_str}"
                    
                    except Exception as e:
                        print(f"⚠️ Error parsing date: {e}")
                        pub_date_formatted = pub_date
                        dt_tehran = None  # Fallback
                    weekday_en = jd.strftime('%A')
                    weekday_fa = PERSIAN_WEEKDAYS.get(weekday_en, weekday_en)

                    day = to_persian_digits(jd.strftime('%d'))
                    month_en = jd.strftime('%B')
                    month_fa = PERSIAN_MONTHS.get(month_en, month_en)
                    year = to_persian_digits(jd.strftime('%Y'))
                    time_str = to_persian_digits(jd.strftime('%H:%M'))

                    date_str = f"{day} {month_fa} {year}"
                    pub_date_formatted = f"{weekday_fa}، {date_str} ⏰ {time_str}"
                except Exception:
                    pub_date_formatted = pub_date


                desc_raw = item.description.text.strip()
                soup_desc = BeautifulSoup(desc_raw, "html.parser")
                
                desc_text = soup_desc.get_text().strip()  # cleaned description
                
                img_url = None
                
                # Try enclosure
                enclosure = item.find("enclosure")
                if enclosure and enclosure.get("type", "").startswith("image"):
                    img_url = enclosure.get("url")
                
                # Try media:thumbnail or media:content
                if not img_url:
                    media_thumbnail = item.find("media:thumbnail")
                    media_content = item.find("media:content")
                    if media_thumbnail and media_thumbnail.get("url"):
                        img_url = media_thumbnail["url"]
                    elif media_content and media_content.get("url"):
                        img_url = media_content["url"]
                
                # Try <img> inside <description>
                if not img_url:
                    img_tag = soup_desc.find("img")
                    if img_tag and img_tag.get("src"):
                        img_url = img_tag["src"]


                category_articles[category].append({
                    "title": title,
                    "link": link,
                    "desc": desc_text,
                    "date": pub_date_formatted,
                    "image": img_url,
                    "source": source,
                    "gregorian": dt_tehran
                })

            except Exception:
                continue



# Sort each category's articles by parsed datetime (if possible)
for articles in category_articles.values():
    def parse_datetime(article):
        try:
            # We extract datetime from the 'date' field already in Persian, so we store the original Gregorian datetime instead
            # Let's enhance the scraping code above to store gregorian too
            return article.get("gregorian") or datetime.min
        except:
            return datetime.min
    articles.sort(key=parse_datetime, reverse=True)

# --- Generate Persian update time ---
now_tehran = datetime.now(ZoneInfo("Asia/Tehran"))
now_jalali = jdatetime.datetime.fromgregorian(datetime=now_tehran)

weekday_fa = PERSIAN_WEEKDAYS.get(now_jalali.strftime('%A'), now_jalali.strftime('%A'))
day = to_persian_digits(now_jalali.strftime('%d'))
month_en = now_jalali.strftime('%B')
month_fa = PERSIAN_MONTHS.get(month_en, month_en)
year = to_persian_digits(now_jalali.strftime('%Y'))
time_str = to_persian_digits(now_jalali.strftime('%H:%M'))

last_updated_html = f"""
<div style="text-align:center; font-size: 16px; color: #666; margin-bottom: 16px;">
    بروزرسانی اخیر: {weekday_fa}، {day} {month_fa} {year} ⏰ {time_str}
</div>
"""

output_path = "desktop.html"

html_content = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>اخبار گزیده روز</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', sans-serif;
            background: #f2f2f2;
            direction: rtl;
            overflow-x: hidden; 
            overflow-y: auto;    
        }}

        h1 {{
            text-align: center;
            color: #003366;
            font-size: 32px;
            margin-bottom: 40px;
        }}

        .container {{
            padding-left: 30px;
            padding-right: 30px;
            padding-bottom: 40px;
            box-sizing: border-box;
            height: 100%%; /* match full height for internal layout */
        }}
    
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            height: calc(100vh - 200px); 
            overflow: hidden; 
        }}
    
        .category {{
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow-y: auto;
        }}
    
        .category-title {{
            background-color: #003366;
            color: white;
            font-size: 22px;
            font-weight: bold;
            padding: 14px 10px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
    
        .article {{
            border-bottom: 1px solid #ddd;
            padding: 14px 10px;
            background-color: #fafafa;
            border-radius: 4px;
            margin: 10px;
        }}
    
        .article img {{
            width: 100%%;
            max-height: 160px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
    
        .title {{
            font-size: 18px;
            font-weight: 700;
            color: #0056b3;
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
        }}
    
        .desc {{
            font-size: 14px;
            color: #333;
            margin-bottom: 6px;
            line-height: 1.6;
        }}
    
        .date, .source {{
            font-size: 12px;
            color: #777;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>گزیده اخبار</h1>
    {last_updated_html}
    <div style="font-weight: bold; text-align: center; margin-bottom: 26px;">
        <a href="https://www.pishkhan.com/all" target="_blank" style="
            background-color: #0056b3;
            color: white;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: inline-block;
            transition: background-color 0.3s ease;
        " onmouseover="this.style.backgroundColor='#003f7f'" onmouseout="this.style.backgroundColor='#0056b3'">
            📰 صفحه اول روزنامه‌های امروز
        </a>
    </div>
    <div class="grid">
"""


for category, articles in category_articles.items():
    html_content += f'<div class="category">'
    html_content += f'<div class="category-title">{category}</div>'
    for article in articles:
        image_url = article.get("image")
        html_content += '<div class="article">'
        if image_url:
            html_content += f'<img src="{image_url}" alt="تصویر">'
        html_content += f'<a class="title" href="{article["link"]}" target="_blank">{article["title"]}</a>'
        html_content += f'<div class="date">{article["date"]}</div>'
        html_content += f'<div class="source">📌 {article["source"]}</div>'
        html_content += f'<div class="desc">{article["desc"]}</div>'
        html_content += '</div>'
    html_content += '</div>'


html_content += """
    </div> <!-- end of .grid -->
    <div style="margin-top: 40px; padding: 20px; background-color: #fff; border-top: 1px solid #ccc; border-radius: 10px; box-shadow: 0 -2px 8px rgba(0,0,0,0.05); font-size: 15px; color: #444; line-height: 1.8;">
    <p style="margin: 0; text-align: justify;">
        این صفحه گزیده‌ای از آخرین اخبار منتشرشده توسط منابع خبری معتبر ایرانی است و به‌صورت دسته‌بندی‌شده نمایش داده می‌شود. اطلاعات حدودا هر ۳۰ دقیقه یک‌بار به‌روزرسانی می‌شود و
        منابعی مانند <strong>تسنیم</strong>، <strong>ایسنا</strong>، <strong>ایرنا</strong>، <strong>اقتصاد آنلاین</strong>، <strong>همشهری</strong> و <strong>باشگاه خبرنگاران جوان</strong> از جمله خبرگزاری‌هایی هستند که مطالب آن‌ها در این صفحه نمایش داده می‌شود.
    </p>
</div>
</div> <!-- end of .container -->
</body>
</html>
"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ desktop version...")

# -------------------------------------------------------------------------------------------------------------------------------- #

output_path = "mobile.html"

html_content = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>اخبار گزیده روز</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', sans-serif;
            background: #f4f6f8;
            direction: rtl;
            overflow-x: hidden;
            overflow-y: auto;
        }}

        h1 {{
            text-align: center;
            color: #1a237e;
            font-size: 32px;
            font-weight: bold;
            margin: 20px 0 10px;
        }}

        .container {{
            padding: 0 20px 30px;
            box-sizing: border-box;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            height: calc(80vh - 150px);
            overflow: hidden;
        }}

        .category {{
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}

        .category-title {{
            background-color: #1a237e;
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
        }}

        .article {{
            border-bottom: 1px solid #e0e0e0;
            padding: 10px;
            background-color: #fdfdfd;
            border-radius: 6px;
            margin: 8px;
        }}

        .article img {{
            width: 100%;
            max-height: 140px;
            object-fit: cover;
            border-radius: 6px;
            margin-bottom: 8px;
        }}

        .title {{
            font-size: 16px;
            font-weight: 700;
            color: #0d47a1;
            text-decoration: none;
            display: block;
            margin-bottom: 6px;
        }}

        .desc {{
            font-size: 13px;
            color: #444;
            margin-bottom: 6px;
            line-height: 1.5;
        }}

        .date, .source {{
            font-size: 11px;
            color: #757575;
        }}

        .top-button {{
            font-size: 16px;
            padding: 10px 24px;
            border-radius: 8px;
            background-color: #3949ab;
            color: white;
            text-decoration: none;
            display: inline-block;
            font-weight: bold;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
            transition: background-color 0.3s ease;
        }}

        .top-button:hover {{
            background-color: #2c387e;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>گزیده اخبار</h1>
    <div style="font-size: 13px; color: #666; text-align: center; margin-bottom: 12px;">
        {last_updated_html}
    </div>
    <div style="text-align: center; margin-bottom: 20px;">
        <a href="https://www.pishkhan.com/all" target="_blank" class="top-button">
            📰 صفحه اول روزنامه‌های امروز
        </a>
    </div>
    <div class="grid">
"""

# Append articles by category...

for category, articles in category_articles.items():
    html_content += f'<div class="category">'
    html_content += f'<div class="category-title">{category}</div>'
    for article in articles:
        image_url = article.get("image")
        html_content += '<div class="article">'
        if image_url:
            html_content += f'<img src="{image_url}" alt="تصویر">'
        html_content += f'<a class="title" href="{article["link"]}" target="_blank">{article["title"]}</a>'
        html_content += f'<div class="date">{article["date"]}</div>'
        html_content += f'<div class="source">📌 {article["source"]}</div>'
        html_content += '</div>'
    html_content += '</div>'


html_content += """
    </div> <!-- end of .grid -->
    <div style="margin-top: 40px; padding: 20px; background-color: #fff; border-top: 1px solid #ccc; border-radius: 10px; box-shadow: 0 -2px 8px rgba(0,0,0,0.05); font-size: 15px; color: #444; line-height: 1.8;">
    <p style="margin: 0; text-align: justify;">
        این صفحه گزیده‌ای از آخرین اخبار منتشرشده توسط منابع خبری معتبر ایرانی است و به‌صورت دسته‌بندی‌شده نمایش داده می‌شود. اطلاعات حدودا هر ۳۰ دقیقه یک‌بار به‌روزرسانی می‌شود و
        منابعی مانند <strong>تسنیم</strong>، <strong>ایسنا</strong>، <strong>ایرنا</strong>، <strong>اقتصاد آنلاین</strong>، <strong>همشهری</strong> و <strong>باشگاه خبرنگاران جوان</strong> از جمله خبرگزاری‌هایی هستند که مطالب آن‌ها در این صفحه نمایش داده می‌شود.
    </p>
</div>
</div> <!-- end of .container -->
</body>
</html>
"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ mobile version...")
