import requests
import json

url = "http://154.37.215.220:11434/api/generate"
payload = {
    "model": "qwen3:0.6b",
    "prompt": "你好，介绍一下你自己"
}
response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        try:
            data = json.loads(line.decode('utf-8'))
            # 只输出 response 字段内容
            print(data.get("response", ""), end="", flush=True)
            # 如果 done 为 True，则换行
            if data.get("done", False):
                print()
        except Exception as e:
            pass  # 忽略解析异常