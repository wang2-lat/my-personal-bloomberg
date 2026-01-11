import os, requests, json

def diagnose_lark():
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    
    print(f"🔍 正在诊断... App ID 是否存在: {bool(app_id)}")
    
    # 1. 尝试获取 Token
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        
        if data.get("code") == 0:
            token = data.get("tenant_access_token")
            print(f"✅ Token 获取成功! 前五位: {token[:5]}...")
            
            # 2. 顺便查询机器人加入的群 ID (LARK_CHAT_ID)
            chat_url = "https://open.feishu.cn/open-apis/im/v1/chats"
            headers = {"Authorization": f"Bearer {token}"}
            chat_res = requests.get(chat_url, headers=headers).json()
            print(f"🤖 机器人所在的群信息: {json.dumps(chat_res, ensure_ascii=False)}")
            
        else:
            print(f"❌ 飞书拒绝了请求! 错误信息: {data.get('msg')}")
            print(f"💡 排查建议: 请确认应用已发布(Released) 且 Secret 没填错。")
            
    except Exception as e:
        print(f"💥 网络请求崩了: {e}")

if __name__ == "__main__":
    diagnose_lark()
