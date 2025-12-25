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
    name = name.upper()
    for noise in ["综合", "频道", "高清", "超清", "HD", "FHD", "-", " ", "PLUS", "+", "TV"]:
        name = name.replace(noise, "")
    return name

def check_720p_and_speed(url):
    """
    不仅测速，还深度检查是否符合 720P 分辨率
    返回 (得分, 延迟)
    """
    try:
        if "[" in url: return 9999, 9999 # 过滤 IPv6
        
        start = time.time()
        # 1. 第一阶段：基础连通性测试 (0.5秒快速过滤)
        r = requests.get(url, timeout=0.8, stream=True)
        if r.status_code == 200:
            delay = int((time.time() - start) * 1000)
            
            # 2. 第二阶段：读取 m3u8 前几行检查分辨率
            # 很多优质源会在 m3u8 内部标注 RESOLUTION=1280x720
            sample = r.iter_lines()
            found_720p = False
            # 检查前 20 行即可
            for _ in range(20):
                line = next(sample).decode('utf-8', errors='ignore').upper()
                if "1280X720" in line:
                    found_720p = True
                    break
            
            # 3. 计分逻辑
            score = delay
            if found_720p:
                score -= 1000 # 命中 720P 的源权重极大，优先选择
            elif "1920X1080" in line:
                score += 500  # 如果是 1080P，稍微靠后（因为你要求 720P）
            
            return score, delay
    except:
        pass
    return 9999, 9999

def main():
    print("🚀 启动 720P 专项优选任务...")
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
            my_clean_name = clean_name(line.split(",")[-1].strip())
            
            if my_clean_name in pool:
                urls = list(set(pool[my_clean_name]))
                best_url = None
                min_score = 9000 # 初始分
                
                for u in urls:
                    score, delay = check_720p_and_speed(u)
                    if score < min_score:
                        min_score = score
                        best_url = u
                    if score < -500: # 只要是 720P 且延迟尚可，就直接过
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
    print(f"✨ 720P 优选完成！共更新 {update_count} 个频道。")

if __name__ == "__main__":
    main()
