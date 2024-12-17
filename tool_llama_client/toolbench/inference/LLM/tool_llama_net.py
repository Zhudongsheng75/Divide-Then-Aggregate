import requests
import json
from termcolor import colored


class ToolLLaMANet:
    def __init__(self, url):
        self.conversation_history = []
        self.url = url

    def add_message(self, message):
        self.conversation_history.append(message)

    def change_messages(self, messages):
        self.conversation_history = messages

    def display_conversation(self, detailed=False):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        print("before_print" + "*" * 50)
        for message in self.conversation_history:
            print_obj = f"{message['role']}: {message['content']} "
            if "function_call" in message.keys():
                print_obj = print_obj + f"function_call: {message['function_call']}"
            print_obj += ""
            print(colored(print_obj, role_to_color[message["role"]]))
        print("end_print" + "*" * 50)

    def parse(self, functions, process_id, **args):
        data = dict(messages=self.conversation_history, functions=functions)
        response = requests.post(self.url, json=data)
        if response.status_code != 200:
            raise ValueError(f"Failed to get result: {response.text}")
        else:
            message, _, completion_tokens, prompt_tokens = response.json()
            if process_id == 0:
                print(f"[process({process_id})]completion tokens: {completion_tokens} prompt tokens: {prompt_tokens}")
        return message, 0, completion_tokens, prompt_tokens
