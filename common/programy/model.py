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

import pathlib
import uuid
import logging
import re

from programy.clients.embed.basic import EmbeddedDataFileBot

logger = logging.getLogger(__name__)


spaces_patter = re.compile(r"\s+", re.IGNORECASE)
special_symb_patter = re.compile(r"[^a-zа-я0-9 ]", re.IGNORECASE)


class DataFileBot(EmbeddedDataFileBot):
    def ask_question(self, userid, question):
        client_context = self.create_client_context(userid)
        return self.renderer.render(client_context, self.process_question(client_context, question))

    def __call__(self, texts):
        userid = uuid.uuid4().hex
        for text in texts:
            logger.info(f"{text=}")
            text = special_symb_patter.sub("", spaces_patter.sub(" ", text.lower())).strip()
            response = self.ask_question(userid, text)
            logger.info(f"{response=}")
        response = response if response else ""
        return response


def get_configuration_files(storage: pathlib.Path = pathlib.Path("data")):
    storage = pathlib.Path(storage)
    files = {
        "aiml": [storage / "categories"],
        # "learnf": [storage / "categories/learnf"],
        "sets": [storage / "sets"],
        "maps": [storage / "maps"],
        "rdfs": [storage / "rdfs"],
        # "properties": storage / "properties/properties.txt",
        # "defaults": storage / "properties/defaults.txt",
        "denormals": storage / "lookups/denormal.txt",
        "normals": storage / "lookups/normal.txt",
        "genders": storage / "lookups/gender.txt",
        "persons": storage / "lookups/person.txt",
        "person2s": storage / "lookups/person2.txt",
        # "triggers": storage / "triggers/triggers.txt",
        # "regexes": storage / "regex/regex-templates.txt",
        "usergroups": storage / "security/usergroups.yaml",
        "spellings": storage / "spelling/corpus.txt",
        "preprocessors": storage / "processing/preprocessors.conf",
        "postprocessors": storage / "processing/postprocessors.conf",
        # "postquestionprocessors": storage / "processing/postquestionprocessors.conf",
        "licenses": storage / "licenses/license.keys",
        # "conversations": storage / "conversations",
        "duplicates": storage / "debug/duplicates.txt",
        "errors": storage / "debug/errors.txt",
        # "services": storage / "services",
    }
    for name in files:
        files[name] = str(files[name]) if isinstance(files[name], pathlib.Path) else [str(i) for i in files[name]]
    return files


def get_programy_model(storage: pathlib.Path = pathlib.Path("data")):
    return DataFileBot(get_configuration_files(storage))