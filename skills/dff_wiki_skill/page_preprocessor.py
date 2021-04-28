# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import logging

import sentry_sdk

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.estimator import Component

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def split_page(page):
    if isinstance(page, str):
        page_split = page.split('\n')
    else:
        page_split = page
    titles = []
    text_list = []
    dict_level = {2: {}, 3: {}, 4: {}}
    for elem in page_split:
        find_title = re.findall(r"^([=]{1,4})", elem)
        if find_title:
            cur_level = len(find_title[0])
            eq_str = "=" * cur_level
            title = re.findall(f"{eq_str}(.*?){eq_str}", elem)
            title = title[0].strip()
            if text_list:
                if titles:
                    last_title, last_level = titles[-1]
                    if cur_level <= last_level:
                        while titles and last_level >= cur_level:
                            if titles[-1][1] < cur_level:
                                last_title, last_level = titles[-1]
                            else:
                                last_title, last_level = titles.pop()
                            if dict_level.get(last_level + 1, {}):
                                if last_title in dict_level[last_level]:
                                    dict_level[last_level][last_title] = {**dict_level[last_level + 1],
                                                                          **dict_level[last_level][last_title]}
                                else:
                                    dict_level[last_level][last_title] = dict_level[last_level + 1]
                                dict_level[last_level + 1] = {}
                            else:
                                dict_level[last_level][last_title] = text_list
                                text_list = []
                    else:
                        dict_level[last_level][last_title] = {"first_par": text_list}
                        text_list = []
                else:
                    dict_level[2]["first_par"] = text_list
                    text_list = []

            titles.append([title, cur_level])
        else:
            text_list.append(elem)

    if text_list:
        if titles:
            last_title, last_level = titles[-1]
            if cur_level <= last_level:
                while titles:
                    last_title, last_level = titles.pop()
                    if last_level + 1 in dict_level and dict_level[last_level + 1]:
                        if last_title in dict_level[last_level]:
                            dict_level[last_level][last_title] = {**dict_level[last_level + 1],
                                                                  **dict_level[last_level][last_title]}
                        else:
                            dict_level[last_level][last_title] = dict_level[last_level + 1]
                        dict_level[last_level + 1] = {}
                    else:
                        dict_level[last_level][last_title] = text_list
                        text_list = []
            else:
                dict_level[last_level]["first_par"] = text_list
                text_list = []

    return dict_level[2]


@register("page_preprocessor")
class PagePreprocessor(Component):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, pages_batch):
        processed_pages_batch = []
        for pages_list in pages_batch:
            processed_pages_list = []
            for page in pages_list:
                processed_page = split_page(page)
                processed_pages_list.append(processed_page)
            processed_pages_batch.append(processed_pages_list)

        return processed_pages_batch