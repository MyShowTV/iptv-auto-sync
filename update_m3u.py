import requests
import time
import re
import os
from datetime import datetime, timedelta

# --- 配置区 ---
SOURCES_URLS = [
    "https://gyssi.link/iptv/chinaiptv/%E5%9B%9B%E5%B7%9D%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w",
    "https://gyssi.link/iptv/chinaiptv/%E6%B2%B3%E5%8D%97%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w",
    "https://gyssi.link/iptv/chinaiptv/%E5%90%89%E6%9E%97%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w"
]

def clean_name(name):
    name = name.upper()
    for noise in ["综合", "频道", "高清", "超清", "HD", "FHD", "-", " ", "PLUS", "+", "TV"]:
        name = name.replace(noise, "")
    return name

def check_480p_and_speed(url):
    try:
        if "[" in url: return 9999, 9999
        start = time.time()
        r = requests.get(url, timeout=0.8, stream=True)
        if r.status_code == 200:
            delay = int((time.time() - start) * 1000)
            sample = r.iter_lines()
            found_720p = False
            for _ in range(15):
                line = next(sample).decode('utf-8', errors='ignore').upper()
                if "480X360" in line:
                    found_480p = True
                    break
            score = delay - 1000 if found_480p else delay
            return score, delay
    except:
        pass
    return 9999, 9999

def main():
    # 获取当前北京时间 (GitHub Action 默认是 UTC，需要 +8 小时)
    bj_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 启动优选任务，当前时间：{bj_time}")

    pool = {}
    for s_url in SOURCES_URLS:
        try:
            r = requests.get(s_url, timeout=10)
            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    c_name = clean_name(lines[i].split(",")[-1].strip())
                    link = lines[i+1].strip()
                    if link.startswith("http"):
                        if c_name not in pool: pool[c_name] = []
                        pool[c_name].append(link)
        except: continue

    if not os.path.exists("TWTV.m3u"): return
    with open("TWTV.m3u", "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_output = []
    i = 0
    update_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            my_raw_name = line.split(",")[-1].strip()
            my_clean_name = clean_name(my_raw_name)
            
            if my_clean_name in pool:
                urls = list(set(pool[my_clean_name]))
                best_url = None
                min_score = 9000
                
                for u in urls:
                    score, delay = check_720p_and_speed(u)
                    if score < min_score:
                        min_score = score
                        best_url = u
                    if score < -500: break
                
                if best_url:
                    final_output.append(line)
                    final_output.append(best_url)
                    # 在链接下方插入一行更新时间注释
                    final_output.append(f"# 更新时间：{bj_time}")
                    update_count += 1
                    i += 1
                    # 跳过旧链接和旧的时间戳注释
                    while i + 1 < len(lines):
                        next_l = lines[i+1].strip()
                        if next_l.startswith("http") or next_l.startswith("# 更新时间") or not next_l:
                            i += 1
                        else:
                            break
                else:
                    final_output.append(line)
            else:
                final_output.append(line)
        elif line and not line.startswith("# 更新时间"):
            final_output.append(line)
        i += 1

    with open("TWTV.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))
    print(f"✨ 优选完成！已更新 {update_count} 个频道的时间戳。")

if __name__ == "__main__":
    main()
