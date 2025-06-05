import os
import json
import time
import uuid
import requests
from dotenv import load_dotenv
from typing import List, Dict

# --- 環境設定 ---
# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數讀取 API 金鑰
# 請確保你的 .env 檔案中有 XAI_API_KEY="你的金鑰"
XAI_API_KEY = os.getenv('XAI_API_KEY')
if not XAI_API_KEY:
    raise ValueError("請在 .env 檔案中設定您的 XAI_API_KEY")

XAI_API_ENDPOINT = "https://api.x.ai/v1/chat/completions"

# --- 常數設定 ---
# 信任的醫療資訊來源網站
TRUSTED_DOMAINS = [
    "www.mohw.gov.tw",
    "www.ntuh.gov.tw",
    "www.vghtpe.gov.tw",
    "www.cgh.org.tw",
    "www.nobeleye.com.tw",
    "www.tso.org.tw",
    "www.aao.org",
    "www.mayoclinic.org",
    "www.nei.nih.gov",
    "www.hopkinsmedicine.org",
    "www.webmd.com"
]

# 要搜尋的中文關鍵字列表
SEARCH_QUERIES = [
    # --- 基礎屈光與常見視力問題 ---
    "近視",
    "遠視",
    "散光",
    "老花眼",
    "弱視",
    "斜視",

    # --- 常見眼科疾病與症狀 ---
    "白內障",
    "青光眼",
    "乾眼症",
    "黃斑部病變",
    "糖尿病視網膜病變",
    "視網膜剝離",
    "飛蚊症",
    "結膜炎",
    "角膜炎",
    "眼瞼炎",
    "麥粒腫", # 俗稱針眼
    "霰粒腫",
    "葡萄膜炎",
    "結膜下出血",
    "視神經損傷",
    "色盲",
    "夜盲症",
    
    # --- 視力矯正方式與治療手術 ---
    "眼鏡",
    "隱形眼鏡",
    "角膜塑型片", #俗稱OK鏡
    "屈光手術",   # 母分類
    "近視雷射",   # 通俗說法
    "LASIK",
    "SMILE",
    "PRK",
    "人工水晶體",
    "角膜移植",
    "視力校正",   # 概括性術語

    # --- 診斷、檢查與測量 ---
    "驗光",
    "視力檢測方法",
    "視力檢查標準",
    "家庭視力篩檢",
    "眼壓",
    "視野檢查",
    "光學同調斷層掃描", # OCT

    # --- 保健、用藥與其他 ---
    "眼睛健康與保健",
    "視力保健",
    "葉黃素",
    "藍光",
    "眼科用藥",
    "人工淚液",
    "眼球結構",
    "視覺原理",
    "視力相關生活品質",
    "眼疾與遺傳的關係"
]

# --- 核心功能 ---

def fetch_knowledge_from_ai(query: str) -> List[Dict]:
    """
    呼叫 Grok API，根據給定的查詢從信任網站中搜尋資訊，
    並要求 API 直接生成指定格式的 JSON。

    Args:
        query (str): 搜尋的關鍵字。

    Returns:
        List[Dict]: 從 API 回傳的知識點列表，若失敗則回傳空列表。
    """
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # 設計一個非常精確的 Prompt，要求 AI 直接輸出 JSON 格式
    # 這是這個腳本成功的關鍵
    prompt_content = f"""
請你扮演一位嚴謹的醫療資訊整理專家。
你的任務是根據關鍵字「{query}」，僅從以下指定的信任網站清單中搜尋相關的醫療知識：
[{', '.join(TRUSTED_DOMAINS)}]

請將搜尋到的重要知識點，整理成一個 JSON 陣列，陣列中會儲存多筆知識點，每個知識點都必須包含以下欄位：
1.  "knowledge_points": 一段不超過 150 字的重要醫療知識內容，內容要以正規醫療知識或是衛教資訊為主。
2.  "summary": 比 knowledge_points 更簡短的核心摘要。
3.  "tags": 一個包含最多 5 個與主題高度相關的中文或英文術語標籤的陣列。
4.  "source": 提供該知識點的具體來源 URL，該 URL 必須來自上述的信任網站清單，且應指向最相關的子頁面，若無子頁面則使用涵蓋該主題的通用頁面。

範例格式如下，注意這只是範例，僅供參考json格式，內容須由搜尋統整後得出：
[
    {{
        "knowledge_points": "知識1的內容",
        "summary": "對知識點的簡單摘要",
        "tags": ["tag1", "tag2", "tag3", ...],
        "source": "https://xxx.xxx.xxx.xxx"
    }},
    {{
        "knowledge_points": "知識2的內容",
        "summary": "對知識點的簡單摘要",
        "tags": ["tag1", "tag2", "tag3", ...],
        "source": "https://xxx.xxx.xxx.xxx"
    }},
    .
    .
    .
    多個知識點
]

請嚴格遵守以下要求：
1. 你的回答「必須」是一個完整的 JSON 陣列，直接以 `[` 開始，以 `]` 結束。
2. 不要在 JSON 陣列前後包含任何額外的文字、解釋、或 markdown 標記 (例如 ```json)。
3. 關鍵字必須在眼科背景下解釋，若關鍵字較廣泛（如「發炎」），優先整理眼科相關知識（如結膜炎、葡萄膜炎）。
4. 針對該關鍵字的知識深度判斷知識點數量，：簡單主題（如結膜炎、近視）提供 10~15 個知識點，複雜主題（如青光眼、視網膜剝離）提供 15~20 個知識點。
5. 所有關鍵字搜尋到的相關知識都要由淺至深來統整列出
6. 同類型知識請合併成一個知識點，避免重複。若知識點超過 150 字，拆分成多個知識點，但避免過度拆分。
7. 若信任網站資料不足，根據可用資料提供知識點。
8. 搜尋時同時使用英文查詢，翻譯成中文時保留標準醫療術語，如：青光眼(glaucoma)。
9. 確保知識內容足夠專業且適合衛教。
10. 每個關鍵字都要額外補充一個知識點，內容為該關鍵字的別稱、學名、英文、俗稱等，必須來自信任網站。
"""

    payload = {
        "model": "grok-3-latest",
        "messages": [{"role": "user", "content": prompt_content}],
        "search_parameters": {
            "mode": "auto"
        },
        "max_tokens": 30000
    }

    try:
        response = requests.post(XAI_API_ENDPOINT, headers=headers, json=payload, timeout=180)
        response.raise_for_status()

        response_text = response.json()["choices"][0]["message"]["content"]
        
        knowledge_data = json.loads(response_text)
        
        if isinstance(knowledge_data, list):
            return knowledge_data
        else:
            print(f"警告：API 為查詢 '{query}' 回傳的不是一個列表。")
            return []

    except requests.exceptions.RequestException as e:
        print(f"錯誤：查詢 '{query}' 時發生網路錯誤: {e}")
        return []
    except json.JSONDecodeError:
        print(f"錯誤：無法解析查詢 '{query}' 的 API 回應。收到的內容：\n{response_text}")
        return []
    except (KeyError, IndexError) as e:
        print(f"錯誤：API 回應格式不符預期: {e}")
        print(f"完整回應: {response.text}")
        return []


# --- 主程式 ---
def main():
    """
    主執行函數，遍歷所有關鍵字，獲取知識點，並儲存為 JSON 檔案。
    """
    all_knowledge_points = []
    
    print("開始從信任來源蒐集眼科醫療知識...")

    for query in SEARCH_QUERIES:
        print(f"\n正在查詢關鍵字: '{query}'")
        
        # 呼叫 API 獲取結構化資料
        results = fetch_knowledge_from_ai(query)
        
        if results:
            print(f"成功獲取 {len(results)} 筆關於 '{query}' 的知識點")
            all_knowledge_points.extend(results)
        else:
            print(f"未能從 API 獲取關於 '{query}' 的有效資料")
        
        # 每次請求後暫停一下，避免對 API 造成過大負擔
        time.sleep(2)
    
    # 重新編排 ID
    for point in all_knowledge_points:
        point["id"] = str(uuid.uuid4())

    print(f"資料蒐集完成。總共蒐集到 {len(all_knowledge_points)} 筆資料")

    # 將最終結果儲存為 JSON 檔案
    output_file = "data/vision_health_knowledge_base_new.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_knowledge_points, f, ensure_ascii=False, indent=4)
        print(f"\n知識庫已成功儲存至檔案: {output_file}")
    except IOError as e:
        print(f"\n錯誤：無法寫入檔案 {output_file}: {e}")


if __name__ == "__main__":
    main()