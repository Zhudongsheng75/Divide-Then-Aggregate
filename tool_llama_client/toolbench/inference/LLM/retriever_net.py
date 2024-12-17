import requests


class ToolRetrieverNet:
    def __init__(self, url):
        self.url = url

    def retrieving(self, query, top_k=5, excluded_tools={}):
        data = dict(query=query, top_k=top_k)
        response = requests.post(self.url + "/retrieving", json=data)
        if response.status_code != 200:
            raise ValueError(f"Failed to get result: {response.text}")
        else:
            retrieved_tools = response.json()
            return retrieved_tools
