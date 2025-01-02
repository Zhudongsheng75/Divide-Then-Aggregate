import requests
import json
import os

url = "http://127.0.0.1:8080/real"

data = {
    "category": "Tools",
    "tool_name": "bulk_whois",
    "api_name": "get_whois_batch_for_bulk_whois",
    "tool_input": '{"batch_id": 1}',
    "strip": "truncate",
    "toolbench_key": "your toolbench_key from ToolBench",
}
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
}

# Make the POST request
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.text)
