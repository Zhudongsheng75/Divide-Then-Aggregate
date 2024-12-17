import os
import json
import sys
import traceback
from time import sleep
from typing import List, Dict

import openai
from loguru import logger

__registered_evaluators__ = {}


def register_evaluator(cls):
    """
    Decorator function to register classes with the registered_evaluators list.
    """
    __registered_evaluators__[cls.__name__] = cls
    return cls


def get_evaluator_cls(clsname):
    """
    Return the evaluator class with the given name.
    """
    try:
        return __registered_evaluators__.get(clsname)
    except:
        raise ModuleNotFoundError("Cannot find evaluator class {}".format(clsname))


class OpenaiPoolRequest:
    def __init__(self, pool_json_file=None):
        self.pool: List[Dict] = []
        __pool_file = pool_json_file
        if os.environ.get("API_POOL_FILE", None) is not None:
            __pool_file = os.environ.get("API_POOL_FILE")
            # self.now_pos = random.randint(-1, len(self.pool))
            self.now_pos = 0
        if os.path.exists(__pool_file):
            self.pool = json.load(open(__pool_file))
            # self.now_pos = random.randint(-1, len(self.pool))
            self.now_pos = 0
        # print(__pool_file)
        if os.environ.get("OPENAI_KEY", None) is not None:
            self.pool.append(
                {
                    "api_key": os.environ.get("OPENAI_KEY"),
                    "organization": os.environ.get("OPENAI_ORG", None),
                    "api_type": os.environ.get("OPENAI_TYPE", None),
                    "api_version": os.environ.get("OPENAI_VER", None),
                }
            )

    # @retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(10),reraise=True)
    def request(self, messages, **kwargs):
        try:
            # self.now_pos = (self.now_pos + 1) % len(self.pool)
            # key_pos = self.now_pos
            key_pos = 0
            item = self.pool[key_pos]
            openai.api_key = item["api_key"]
            openai.api_base = item.get("api_base", None)
            kwargs["api_key"] = item["api_key"]
            if item.get("organization", None) is not None:
                kwargs["organization"] = item["organization"]
            return openai.ChatCompletion.create(messages=messages, **kwargs)
        except Exception as e:
            logger.error(f"模型：{self.pool[0]['api_key']}, 错误：{e}")
            # traceback.print_exc()
            sleep(1)
            if "请求过于频繁" in str(e):
                sleep(1)
            # 如果遇到额度用完错误，删除这个api_key
            elif "使用量已用完" in str(e):
                logger.warning(f"key：{self.pool[0]['api_key']} 额度用完，删除")
                del self.pool[0]

            if len(self.pool) == 0:
                logger.info("所有api key额度使用完毕，程序结束。")
                sys.exit(1)
            else:
                logger.info("重试中")
                return self.request(messages, **kwargs)

    def __call__(self, messages, **kwargs):
        return self.request(messages, **kwargs)
