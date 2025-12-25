import requests
import time
import re
import os

# --- 配置区 ---
SOURCES_URLS = [
    "https://gyssi.link/iptv/chinaiptv/%E5%9B%9B%E5%B7%9D%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w",
    "https://gyssi.link/iptv/chinaiptv/%E6%B2%B3%E5%8D%97%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w",
    "https://gyssi.link/iptv/chinaiptv/%E5%90%89%E6%9E%97%E7%9C%81.m3u?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjI0NDUxOTY1NjY5MjEzMjYsImlhdCI6MTc2NDU3ODkyMSwiZXhwIjoxNzk3NDEwOTIxfQ.oVHRqqzLtkWKIHGeqinVeve1t8dAoWrNkXXPB5NBS9w"
]

def clean_name(name):
    """提取核心名称，提高匹配成功率"""
    if not name: return ""
    name = name.upper()
    # 过滤掉干扰字符
    for noise in ["综合", "频道", "高清", "超清", "HD", "FHD", "-", " ", "PLUS", "+"]:
        name = name.replace(noise, "")
    return name

def get_speed(url):
    """测速：请求头部，1.2秒超时"""
    try:
        start = time.time()
        r = requests.head(url, timeout=1.2, allow_redirects=True)
        if r.status_code == 200:
            return int((time.time() - start) * 1000)
    except:
        pass
    return 9999

def main():
    print("📡 正在抓取三个高清源的数据...")
    pool = {}
    for s_url in SOURCES_URLS:
        try:
            r = requests.get(s_url, timeout=10)
            r.encoding = 'utf-8'
            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    # 获取对方源里的频道名
                    raw_name = lines[i].split(",")[-1].strip()
                    c_name = clean_name(raw_name)
                    link = lines[i+1].strip()
                    if link.startswith("http"):
                        if c_name not in pool: pool[c_name] = []
                        pool[c_name].append(link)
        except: continue

    if not os.path.exists("TWTV.m3u"):
        print("❌ 错误：未在仓库找到 TWTV.m3u")
        return

    with open("TWTV.m3u", "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_output = []
    i = 0
    update_count = 0
    
    print("开始匹配测速...")
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            # 尝试通过名字匹配
            my_raw_name = line.split(",")[-1].strip()
            my_clean_name = clean_name(my_raw_name)
            
            if my_clean_name in pool:
                # 测速选出最快的
                urls = list(set(pool[my_clean_name]))
                best_url = min(urls, key=get_speed)
                final_output.append(line)
                final_output.append(best_url)
                update_count += 1
                # 跳过原有的旧链接行
                i += 1
                while i + 1 < len(lines) and (lines[i+1].strip().startswith("http") or not lines[i+1].strip()):
                    i += 1
            else:
                final_output.append(line)
        elif line:
            final_output.append(line)
        i += 1

    with open("TWTV.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))
    print(f"✅ 更新完成！共优化 {update_count} 个链接。")

if __name__ == "__main__":
    main()
