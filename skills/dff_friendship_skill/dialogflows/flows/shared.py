
# %%
import random
import os
import logging


import requests
import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.entity_utils as entity_utils
import common.greeting as common_greeting
import common.link as common_link


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98


##################################################################################################################
# utils
##################################################################################################################
std_acknowledgements = {
    "neutral": ["Ok. ", "Oh. ", "Huh. ", "Well. ", "Gotcha. ", "Hmm. ", "Aha. "],
    "positive": ["Sounds cool! ", "Great! ", "Wonderful! "],
    "negative": ["Huh... ", "Sounds sad... ", "Sorry... "],
}


def get_sentiment_acknowledgement(vars, acknowledgements=None):
    acknowledgements = std_acknowledgements.update(acknowledgements) if acknowledgements else std_acknowledgements
    return acknowledgements.get(state_utils.get_human_sentiment(vars), [""])


# curl -H "Content-Type: application/json" -XPOST http://0.0.0.0:8088/respond \
#   -d '{"text":["Hello, my dog [MASK] cute"]}'
def masked_lm(templates=["Hello, it's [MASK] dog."], prob_threshold=0.0, probs_flag=False):
    request_data = {"text": templates}
    try:
        predictions_batch = requests.post(MASKED_LM_SERVICE_URL, json=request_data, timeout=1.5).json()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        predictions_batch = {}
    logger.debug(f"predictions_batch = {predictions_batch}")
    tokens_batch = []
    for predictions in predictions_batch.get("predicted_tokens", [[]] * len(templates)):
        tokens = {}
        if predictions and predictions[0]:
            one_mask_predictions = predictions[0]
            for token, prob in one_mask_predictions.items():
                if prob_threshold < prob:
                    tokens[token] = prob
        tokens_batch += [tokens if probs_flag else list(tokens)]
    return tokens_batch


def set_confidence_by_universal_policy(vars):
    if not condition_utils.is_begin_of_dialog(vars, begin_dialog_n=10):
        state_utils.set_confidence(vars, 0)
    elif condition_utils.is_first_our_response(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        state_utils.set_can_continue(vars)
    elif not condition_utils.is_interrupted(vars) and common_greeting.dont_tell_you_answer(
        state_utils.get_last_human_utterance(vars)
    ):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE)
        state_utils.set_can_continue(vars)
    elif not condition_utils.is_interrupted(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
    else:
        state_utils.set_confidence(vars, MIDDLE_DIALOG_START_CONFIDENCE)
        state_utils.set_can_continue(vars)


##################################################################################################################
# link_to by enity
##################################################################################################################


def link_to_by_enity_request(ngrams, vars):
    flag = True
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    logger.info(f"link_to_by_enity_request={flag}")
    return flag


link_to_skill2key_words = {
    "news_skill": ["news"],
    "movie_skill": ["movie"],
    "book_skill": ["book"],
    # "coronavirus_skill": ["coronavirus"],
    "game_cooperative_skill": ["game"],
    "personal_info_skill": ["private live"],
    "meta_script_skill": ["nothing"],
    "emotion_skill": ["emotion"],
    "weather_skill": ["weather"],
}
link_to_skill2i_like_to_talk = {
    "news_skill": [
        "Anxious to stay current on the news.",
        "I don't know about you but I feel nervous when I don't know what's going on.",
    ],
    "movie_skill": ["Movies are my passion.", "Love stories about the world told in motion."],
    "book_skill": [
        "With a good book I can lose myself anywhere on Earth.",
        "One of my creators has a huge home library. Wish I could read some of those books.",
    ],
    "coronavirus_skill": [" "],
    "game_cooperative_skill": [
        "Computer games are fantastic. Their virtual worlds help me to escape my prosaic ordinary life in the cloud.",
        "With this lockdown games are my way to escape and thrive.",
    ],
    "personal_info_skill": [" "],
    "meta_script_skill": [" "],
    "emotion_skill": [
        "Emotions are important.",
        "Life isn't about just doing things. What you, me, everyone feels about their lives is as important.",
    ],
    "weather_skill": ["Everybody likes to talk about weather right?" "It feels rather cold here in the sky."],
}


def link_to_by_enity_response(vars):
    ack = random.choice(get_sentiment_acknowledgement(vars))
    try:
        entities = state_utils.get_labeled_noun_phrase(vars)
        time_sorted_human_entities = entity_utils.get_time_sorted_human_entities(entities)
        if time_sorted_human_entities:
            logger.debug(f"time_sorted_human_entities= {time_sorted_human_entities}")
            tgt_entity = list(time_sorted_human_entities)[-1]
            logger.debug(f"tgt_entity= {tgt_entity}")
            if tgt_entity in sum(link_to_skill2key_words.values(), []):
                skill_names = [skill for skill, key_words in link_to_skill2key_words.items() if tgt_entity in key_words]
            else:
                link_to_skills = {
                    link_to_skill: f"I [MASK] interested in both {key_words[0]} and {tgt_entity}."
                    for link_to_skill, key_words in link_to_skill2key_words.items()
                }
                link_to_skill_scores = masked_lm(list(link_to_skills.values()), probs_flag=True)
                link_to_skill_scores = {
                    topic: max(*list(score.values()), 0) if score else 0
                    for topic, score in zip(link_to_skills, link_to_skill_scores)
                }
                skill_names = sorted(link_to_skill_scores, key=lambda x: link_to_skill_scores[x])[-2:]
        else:
            skill_names = [random.choice(list(link_to_skill2key_words))]

        # used_links
        used_links = state_utils.get_used_links(vars)

        link = common_link.link_to(skill_names, used_links)
        used_links[link["skill"]] = used_links.get(link["skill"], []) + [link["phrase"]]

        state_utils.save_used_links(vars, used_links)

        body = random.choice(link_to_skill2i_like_to_talk.get(link["skill"], [""]))

        body += f" {link['phrase']}"
        set_confidence_by_universal_policy(vars)
        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return " ".join([ack, "I like to talk about movies. Do you have favorite movies?"])