import os
import re
import uuid
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from ckip_transformers.nlp import CkipWordSegmenter
from transformers import pipeline
from sentence_transformers import SentenceTransformer

load_dotenv()

XAI_API_KEY = os.getenv('XAI_API_KEY')
XAI_API_ENDPOINT = "https://api.x.ai/v1/chat/completions"  # 使用即時搜索端點

# 可靠來源的域名清單
TRUSTED_DOMAINS = [
    "zeiss.com", "zeiss.com.tw", "aao.org", "nih.gov", "who.int",
    "ncbi.nlm.nih.gov", "medlineplus.gov", "nobeleye.com.tw",
    "health.gov.tw", "bmjopen.bmj.com", "biomedcentral.com"
]

# 擴展的搜尋關鍵字（中文和英文，涵蓋更多眼睛相關醫學知識）
SEARCH_QUERIES = [
    # 中文
    "視力檢測方法", "眼睛健康與保健", "近視", "遠視", "散光", 
    "青光眼", "白內障", "視力檢查標準", "家庭視力篩檢", "視力相關生活品質",
    "老花眼", "視網膜病變", "角膜炎", "乾眼症", "眼壓", 
    "視神經損傷", "色盲", "夜盲症", "飛蚊症", "眼瞼炎", 
    "結膜炎", "角膜移植", "視網膜剝離", "糖尿病視網膜病變", "黃斑部病變",
    # 英文
    "vision screening methods", "eye health and care", "myopia", "hyperopia", "astigmatism",
    "glaucoma", "cataract", "vision testing standards", "home-based vision screening", 
    "vision-related quality of life", "presbyopia", "retinal disorders", "keratitis", 
    "dry eye syndrome", "intraocular pressure", "optic nerve damage", "color blindness", 
    "night blindness", "floaters", "blepharitis", "conjunctivitis", "corneal transplant", 
    "retinal detachment", "diabetic retinopathy", "macular degeneration"
]

# 初始化 NLP 工具
summarizer = pipeline("summarization", model="t5-small")  # 摘要工具
ws_driver = CkipWordSegmenter(model="bert-base", device=0)  # CKIP 分詞器
embedder = SentenceTransformer('distilbert-base-nli-stsb-mean-tokens')  # 向量嵌入

# 資料清洗函數
def clean_content(content: str) -> str:
    # 移除 HTML 標籤
    content = re.sub(r'<[^>]+>', '', content)
    # 移除多餘空白和換行
    content = re.sub(r'\s+', ' ', content).strip()
    # 移除無意義字符（如特殊符號、過多的標點）
    content = re.sub(r'[^\w\s,.!?]', '', content)
    # 移除過短或無意義的內容
    if len(content) < 20 or content.lower() in ['not found', 'error', '']:
        return None
    return content

# xAI API 即時搜索函數
def search_xai_api(query: str, lang: str = "zh") -> List[Dict]:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "max_results": 20,
        "lang": lang,
        "filter": {
            "domains": TRUSTED_DOMAINS,
            "exclude_ads": True,
            "require_secure": True
        }
    }
    try:
        response = session.post(XAI_API_ENDPOINT, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [
            item for item in data.get("results", [])
            if "source" in item and item["source"].startswith(('http://', 'https://'))
        ]
    except requests.exceptions.RequestException as e:
        print(f"查詢失敗: {query}, 錯誤: {e}")
        return []

# 提取知識重點
def extract_knowledge_points(content: str, max_length: int = 100) -> List[str]:
    cleaned_content = clean_content(content)
    if not cleaned_content:
        return []
    try:
        summary = summarizer(cleaned_content, max_length=max_length, min_length=50, do_sample=False)
        return [summary[0]["summary_text"]]
    except Exception as e:
        print(f"摘要提取失敗: {e}")
        return [cleaned_content[:max_length] + "..." if len(cleaned_content) > max_length else cleaned_content]

# 使用 CKIP 生成標籤
def generate_tags(query: str, content: str) -> List[str]:
    cleaned_content = clean_content(content)
    if not cleaned_content:
        return query.split()[:5]
    # 使用 CKIP 分詞
    ws_result = ws_driver([cleaned_content])[0]  # CKIP 返回分詞結果
    # 過濾停用詞並提取關鍵詞（簡單模擬關鍵詞提取）
    stopwords = {'的', '是', '在', '了', '和', '與', '及', '或', '等'}
    keywords = [word for word in ws_result if word not in stopwords and len(word) > 1]
    # 結合查詢關鍵字和提取的關鍵詞，去重
    combined = list(set(keywords + query.split()))
    return combined[:5]  # 限制最多 5 個標籤

# 儲存知識點的列表
knowledge_points: List[Dict] = []

# 執行搜尋並整理知識點
for query in SEARCH_QUERIES:
    print(f"正在查詢: {query}")
    lang = "zh" if any(c in query for c in "中文") else "en"
    search_results = search_xai_api(query, lang)
    
    for item in search_results:
        content = item.get("content", "")
        source = item.get("source", "")
        title = item.get("title", "")
        
        # 提取知識點
        extracted_points = extract_knowledge_points(content)
        
        for point in extracted_points:
            # 跳過空或無效的知識點
            if not point or len(point) < 20:
                continue
                
            # 生成向量嵌入
            embedding = embedder.encode(point).tolist()
            
            # 構建知識點條目
            knowledge_entry = {
                "id": str(uuid.uuid4()),
                "title": title or f"{query} - 知識點",
                "knowledge_points": point,
                "tags": generate_tags(query, point),
                "source": source,
                "language": lang,
                "timestamp": datetime.now().isoformat(),
                "relevance_score": item.get("relevance", 0.0),
                "category": query,
                "embedding": embedding
            }
            knowledge_points.append(knowledge_entry)

# 資料清洗：移除重複條目
unique_points = []
seen_points = set()
for entry in knowledge_points:
    point_text = entry["knowledge_points"]
    if point_text not in seen_points:
        seen_points.add(point_text)
        unique_points.append(entry)

# 將知識點儲存為 JSON 檔案
output_file = "vision_health_knowledge_points.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(unique_points, f, ensure_ascii=False, indent=4)

print(f"知識點已儲存至 {output_file}")
print(f"共蒐集 {len(unique_points)} 個唯一知識點")