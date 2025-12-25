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
    for noise in ["综合", "频道", "高清", "超清", "HD", "FHD", "-", " ", "PLUS", "+", "TV"]:
        name = name.replace(noise, "")
    return name

def get_quality_and_speed(url):
    """同时评估画质和速度：返回 (得分, 耗时)"""
    try:
        # 排除 IPv6 地址（带有方括号的），除非你确定家里环境支持
        if "[" in url and "]" in url:
            return 9999, 9999
            
        start = time.time()
        # 模拟浏览器并请求头信息
        r = requests.head(url, timeout=0.8, allow_redirects=True) 
        if r.status_code == 200:
            delay = int((time.time() - start) * 1000)
            
            # 【画质判断逻辑】
            # 1. 优先选择包含 1080p, FHD, 4K 关键词的源
            # 2. 如果服务器返回 Content-Length 很大，通常说明码率更高更清晰
            quality_score = 0
            if any(x in url.upper() for x in ["FHD", "1080P", "4K", "8M"]):
                quality_score -= 200 # 得分越低（越负）越优先
            
            # 将延迟和画质权重结合
            final_score = delay + quality_score
            return final_score, delay
    except:
        pass
    return 9999, 9999

def main():
    print("📡 正在全网搜寻 IPv4 高清源...")
    pool = {}
    for s_url in SOURCES_URLS:
        try:
            r = requests.get(s_url, timeout=10)
            r.encoding = 'utf-8'
            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    raw_name = lines[i].split(",")[-1].strip()
                    c_name = clean_name(raw_name)
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
                min_score = 9999
                
                # 遍历测速并选择得分最低（最优）的
                for u in urls:
                    score, delay = get_quality_and_speed(u)
                    if score < min_score:
                        min_score = score
                        best_url = u
                    # 如果找到一个延迟低于 100ms 且得分很低的，直接秒杀退出循环
                    if score < 50:
                        break
                
                if best_url:
                    final_output.append(line)
                    final_output.append(best_url)
                    update_count += 1
                    i += 1
                    while i + 1 < len(lines) and (lines[i+1].strip().startswith("http") or not lines[i+1].strip()):
                        i += 1
                else:
                    final_output.append(line)
            else:
                final_output.append(line)
        elif line:
            final_output.append(line)
        i += 1

    with open("TWTV.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))
    print(f"✨ 优化完成！已选出 {update_count} 个最清晰、最快的 IPv4 线路。")

if __name__ == "__main__":
    main()
