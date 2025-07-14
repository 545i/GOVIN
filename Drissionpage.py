import requests
from DrissionPage import ChromiumPage
import re
import os
from dotenv import load_dotenv
import time
from pynput.keyboard import Controller, Key  # 新增
import pygetwindow as gw  # 新增
import json # 新增

os.makedirs("douyin", exist_ok=True)
load_dotenv()

headers = {"cookie": os.getenv("DOUYIN_COOKIE"),
    "referer":os.getenv("DOUYIN_REFERER"),
    "user-agent":os.getenv("DOUYIN_UA")}

def download_video_with_retry(video_url, title, index=None, max_retries=3, progress_callback=print):
    """下載視頻並處理錯誤"""
    # 清理文件名 - 移除所有不允許的字符
    title_clean = re.sub(r'[<>/?~`!@#$%^&*()_+-=,.|;:"\'\\]', "", title)
    
    # 如果有提供索引，在文件名前加上數字
    if index is not None:
        file_path = f"douyin/{index}_{title_clean}.mp4"
    else:
        file_path = f"douyin/{title_clean}.mp4"
    
    # 檢查文件是否已存在（忽略前面的數字與底線，只比對標題）
    existed = False
    for fname in os.listdir("douyin"):
        if fname.endswith(".mp4"):
            # 去掉前面的數字與底線
            pure_name = re.sub(r'^\\d+_', '', fname)
            if pure_name == f"{title_clean}.mp4":
                existed = True
                break
    if existed:
        if progress_callback:
            progress_callback(f"文件已存在，跳過下載: {title_clean}")
        return "existed"
    
    for attempt in range(max_retries):
        try:
            if progress_callback:
                progress_callback(f"正在下載: {title} (嘗試 {attempt + 1}/{max_retries})")
            
            # 使用 stream=True 來處理大文件
            response = requests.get(url=video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 分塊下載
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if progress_callback:
                progress_callback(f"下載完成: {title_clean}")
            return "success"
            
        except requests.exceptions.RequestException as e:
            if progress_callback:
                progress_callback(f"下載失敗 (嘗試 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒後重試
            else:
                if progress_callback:
                    progress_callback(f"下載失敗，已跳過: {title}")
                return "failed"

def get_total_video_count(page):
    """獲取帳戶的總影片數量"""
    try:
        # 方法1: 優先查找MNSB3oPV類的元素（測試顯示這個最準確）
        try:
            mnsb_elements = page.eles('.MNSB3oPV')
            for ele in mnsb_elements:
                text = ele.text.strip()
                if text.isdigit() and int(text) > 10:  # 影片數量通常大於10
                    return int(text)
        except:
            pass
        
        # 方法2: 直接查找data-e2e屬性的元素
        try:
            element = page.ele('span[data-e2e="user-tab-count"]', timeout=3)
            if element:
                count_text = element.text.strip()
                if count_text.isdigit() and int(count_text) > 0:
                    return int(count_text)
        except:
            pass
        
        # 方法3: 查找包含"作品"文本的元素，然後找相鄰的數字
        try:
            # 查找包含"作品"的元素
            work_elements = page.eles('span:contains("作品")')
            for work_ele in work_elements:
                # 查找相鄰的兄弟元素
                parent = work_ele.parent
                if parent:
                    # 查找父元素下的所有span
                    spans = parent.eles('span')
                    for span in spans:
                        text = span.text.strip()
                        if text.isdigit() and int(text) > 0:
                            # 檢查這個數字是否在"作品"附近
                            if int(text) > 10:  # 影片數量通常大於10
                                return int(text)
        except:
            pass
        
        # 方法4: 通過頁面HTML內容查找
        try:
            page_content = page.html
            import re
            
            # 查找"作品"附近的數字模式
            patterns = [
                r'class="[^"]*MNSB3oPV[^"]*"[^>]*>(\d+)<',  # 優先匹配MNSB3oPV類
                r'data-e2e="user-tab-count">(\d+)<',  # 直接匹配data-e2e屬性
                r'作品.*?(\d{2,})',  # 作品後面跟2位以上數字
                r'(\d{2,}).*?作品',  # 2位以上數字後面跟作品
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_content)
                for match in matches:
                    if match.isdigit() and int(match) > 10:
                        return int(match)
        except:
            pass
        
        # 方法5: 查找所有數字，然後篩選合理的影片數量
        try:
            spans = page.eles('span')
            candidates = []
            for span in spans:
                text = span.text.strip()
                if text.isdigit() and int(text) > 10:
                    # 檢查這個span是否在合理的區域
                    try:
                        # 檢查父元素是否包含相關文本
                        parent_text = span.parent.text if span.parent else ""
                        if "作品" in parent_text or "視頻" in parent_text or "post" in parent_text.lower():
                            candidates.append(int(text))
                    except:
                        candidates.append(int(text))
            
            # 如果找到候選數字，返回最大的（通常是最準確的）
            if candidates:
                return max(candidates)
        except:
            pass
        
        # 方法6: 使用JavaScript查找
        try:
            js_code = """
            function findVideoCount() {
                // 優先查找MNSB3oPV類的元素
                let mnsbElements = document.querySelectorAll('.MNSB3oPV');
                for (let el of mnsbElements) {
                    let text = el.textContent.trim();
                    if (/^\d+$/.test(text) && parseInt(text) > 10) {
                        return parseInt(text);
                    }
                }
                
                // 查找data-e2e="user-tab-count"的元素
                let elements = document.querySelectorAll('span[data-e2e="user-tab-count"]');
                for (let el of elements) {
                    let text = el.textContent.trim();
                    if (/^\d+$/.test(text) && parseInt(text) > 10) {
                        return parseInt(text);
                    }
                }
                
                // 查找包含"作品"的元素附近的數字
                let workElements = Array.from(document.querySelectorAll('span')).filter(el => 
                    el.textContent.includes('作品')
                );
                
                for (let workEl of workElements) {
                    let parent = workEl.parentElement;
                    if (parent) {
                        let spans = parent.querySelectorAll('span');
                        for (let span of spans) {
                            let text = span.textContent.trim();
                            if (/^\d+$/.test(text) && parseInt(text) > 10) {
                                return parseInt(text);
                            }
                        }
                    }
                }
                
                return null;
            }
            return findVideoCount();
            """
            
            result = page.run_js(js_code)
            if result and isinstance(result, (int, float)) and result > 10:
                return int(result)
        except:
            pass
            
        return None
    except Exception as e:
        print(f"獲取影片數量時出錯: {e}")
        return None

def run_crawler(target_url, progress_callback=print):
    """主爬蟲函數，接受目標URL參數"""
    progress_callback(f"[訊息] 開始爬取目標網址: {target_url}")
    
    # 更新 headers 中的 referer
    headers["referer"] = target_url
    
    Google = ChromiumPage()

    # 設置更完整的瀏覽器標頭
    Google.set.headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })

    Google.listen.start("aweme/post")  # 開始監聽
    Google.get(target_url)
    progress_callback(f"[訊息] 頁面標題: {Google.title}")
    
    # 取得網頁標題
    page_title = Google.title if Google.title else "未知標題"
    history = load_history()
    if page_title not in history:
        history[page_title] = []

    # 等待頁面加載完成
    time.sleep(3)
    
    # 獲取帳戶總影片數量
    total_videos = get_total_video_count(Google)
    if total_videos is None:
        progress_callback("[警告] 無法獲取帳戶總影片數量，將使用預設下滑次數")
        target_count = 50  # 預設目標
    else:
        progress_callback(f"[訊息] 檢測到帳戶總共有 {total_videos} 個影片")
        target_count = total_videos
    
    # 計算需要的下滑次數（每頁大約20-30個影片）
    estimated_scrolls = max(15, (target_count // 20) + 5)  # 至少15次，根據影片數量調整
    progress_callback(f"[訊息] 預計需要下滑 {estimated_scrolls} 次來加載所有影片")

    # 新增：初始化 pynput keyboard controller
    keyboard = Controller()

    # 下滑加載更多影片
    progress_callback("[訊息] 正在下滑加載更多影片...")
    all_data = []
    consecutive_no_new_data = 0  # 連續沒有新數據的次數
    max_consecutive_no_new = 3   # 最大連續無新數據次數
    
    for i in range(estimated_scrolls):
        # 新增：自動聚焦Google瀏覽器視窗
        try:
            for w in gw.getAllWindows():
                if w.title and 'Google' in w.title:
                    w.activate()
                    break
        except Exception as e:
            progress_callback(f"[警告] 聚焦Google視窗失敗: {e}")
        Google.scroll.to_bottom()
        # 新增：發送 PageDown 鍵
        keyboard.press(Key.page_down)
        keyboard.release(Key.page_down)
        time.sleep(3)  # 等待頁面加載
        progress_callback(f"[訊息] 已下滑 {i+1}/{estimated_scrolls} 次")
        
        # 嘗試獲取數據包
        try:
            A1 = Google.listen.wait(timeout=5)  # 設置5秒超時
            if A1 and A1.response and A1.response.body:
                JSON = A1.response.body
                if "aweme_list" in JSON:
                    current_data = JSON["aweme_list"]
                    previous_count = len(all_data)
                    all_data.extend(current_data)
                    new_count = len(all_data)
                    
                    if new_count > previous_count:
                        consecutive_no_new_data = 0  # 重置計數器
                        progress_callback(f"[訊息] 當前已獲取 {new_count} 個影片")
                    else:
                        consecutive_no_new_data += 1
                        progress_callback(f"[訊息] 本次未獲取到新影片，連續 {consecutive_no_new_data} 次")
                        
                    if consecutive_no_new_data >= max_consecutive_no_new:
                        progress_callback(f"[訊息] 連續 {max_consecutive_no_new} 次未獲取到新影片，停止下滑")
                        break
        except Exception as e:
            progress_callback(f"[警告] 獲取數據時出錯: {e}")
            consecutive_no_new_data += 1

    # 去重並獲取最終數據
    if all_data:
        # 使用 aweme_id 去重
        unique_data = {}
        for item in all_data:
            if "aweme_id" in item:
                unique_data[item["aweme_id"]] = item
        
        data = list(unique_data.values())
        progress_callback(f"[訊息] 去重後總共獲取到 {len(data)} 個影片")
        
        if total_videos:
            if len(data) >= total_videos:
                progress_callback(f"✅ 成功獲取到所有影片 ({len(data)}/{total_videos})")
            else:
                progress_callback(f"⚠️  只獲取到 {len(data)}/{total_videos} 個影片，可能還有更多影片未加載")
    else:
        progress_callback("[訊息] 使用最後一次監聽結果...")
        try:
            A1 = Google.listen.wait(timeout=10)
            JSON = A1.response.body
            data = JSON["aweme_list"]
        except:
            progress_callback("[錯誤] 無法獲取任何影片數據")
            return {"total": 0, "success": 0, "failed": 0}

    # 開始下載
    progress_callback(f"[訊息] 開始下載 {len(data)} 個影片...")
    progress_callback("[載入] 正在準備下載，請稍候...")
    existed_files = []
    success_count = 0
    failed_count = 0
    download_targets = []

    for i, video_data in enumerate(data, 1):
        try:
            video_url = video_data["video"]["play_addr"]["url_list"][0]
            title = video_data["desc"]
            title_clean = re.sub(r'[<>/?~`!@#$%^&*()_+-=,.|;:"\'\\]', "", title)
            # 先查 history.json
            if title_clean in history[page_title]:
                existed_files.append((i, title))
                continue
            # 記錄到 history
            history[page_title].append(title_clean)
            result = download_video_with_retry(video_url, title, index=i, progress_callback=None)
            if result == "existed":
                existed_files.append((i, title))
            else:
                download_targets.append((i, title, video_url))
        except Exception as e:
            failed_count += 1

    # 下載結束後，保存 history
    save_history(history)

    if existed_files:
        progress_callback("以下文件已存在，跳過下載：")
        for index, name in existed_files:
            progress_callback(f"{index}_{name}")

    for idx, title, video_url in download_targets:
        progress_callback(f"正在下載 ({idx}/{len(data)}): {title}")
        result = download_video_with_retry(video_url, title, index=idx, progress_callback=progress_callback)
        if result == "success":
            success_count += 1
        else:
            failed_count += 1

    progress_callback(f"\n[完成] 下載完成！成功: {success_count}, 失敗: {failed_count}")

    if failed_count > 0:
        progress_callback(f"⚠️  有 {failed_count} 個影片下載失敗，請檢查網絡連接或重試")
    else:
        progress_callback("✅ 所有影片下載成功！")

    progress_callback(f"[完成] 總共處理了 {len(data)} 個影片")
    
    return {
        "total": len(data),
        "success": success_count,
        "failed": failed_count
    }

def save_history(history, history_path="douyin/history.json"):
    """保存下載歷史"""
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[訊息] 歷史已保存到 {history_path}")
    except Exception as e:
        print(f"[錯誤] 保存歷史失敗: {e}")

def load_history(history_path="douyin/history.json"):
    if not os.path.exists(history_path):
        # 自動建立一個空的 json 檔案
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 如果直接執行此腳本，使用預設URL
if __name__ == "__main__":
    default_url = "https://www.douyin.com/user/MS4wLjABAAAAiqA-N9BxrTTC8-X5217ndAfAhat6x6tM_fRqkWmmCLs?from_tab_name=main&vid=7524847257405902118"
    run_crawler(default_url)



