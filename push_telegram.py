import os, requests

def find_my_chat_id():
    # 1. 获取临时通行证
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token = requests.post(auth_url, json={"app_id": app_id, "app_secret": app_secret}).json().get("tenant_access_token")

    # 2. 查询机器人加入的所有群组
    list_url = "https://open.feishu.cn/open-apis/im/v1/chats"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(list_url, headers=headers).json()
    
    if resp.get("code") == 0:
        items = resp.get("data", {}).get("items", [])
        for chat in items:
            print(f"✅ 找到群聊: {chat['name']} | ID: {chat['chat_id']}")
    else:
        print(f"❌ 查询失败: {resp.get('msg')}")

if __name__ == "__main__":
    find_my_chat_id()
