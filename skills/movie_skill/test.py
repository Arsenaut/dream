import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": res}


def test_one_step_responses():
    url = 'http://0.0.0.0:8023/movie_skill'

    print("check_actor")
    input_data = get_input_json("test_configs/check_actor.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['Chris Evans', 'actor', 'very_positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)

    print("check_director_more_important_than_actor")
    input_data = get_input_json("test_configs/check_director_more_important_than_actor.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['Quentin Tarantino', 'director', 'very_positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)

    print("check_movie")
    input_data = get_input_json("test_configs/check_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['0848228', 'movie', 'very_positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)

    print("check_person_of_the_same_prof")
    input_data = get_input_json("test_configs/check_person_of_the_same_prof.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['Quentin Tarantino', 'actor', 'positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)

    print("check_person_from_movie")
    input_data = get_input_json("test_configs/check_person_from_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    name = 'Chris Evans'
    profession = "actor"
    article = "an"
    templates = [f"{name} gave their best as {article} {profession} in",
                 f"{name} gave their best in",
                 f"{name} showed their great potential in",
                 f"{name} showed their talent as {article} {profession} in",
                 ]
    if_response_of_template = [temp in response[0] for temp in templates]
    assert sum(if_response_of_template) == 1, print(response)

    print("check_person_not_in_movie")
    input_data = get_input_json("test_configs/check_person_not_in_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['Brad Pitt', 'actor', 'very_positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)
    assert "Although I am not sure " in response[0], print(response)

    print("check_persons_comparison")
    input_data = get_input_json("test_configs/check_persons_comparison.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {"bot_attitudes": [['Brad Pitt', 'actor', 'very_positive'],
                                                             ['Chris Evans', 'actor', 'very_positive']],
                                           "human_attitudes": []
                                           }], \
        print(response)

    print("check_persons_comparison2")
    input_data = get_input_json("test_configs/check_persons_comparison2.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {'bot_attitudes': [['Brad Pitt', 'actor', 'very_positive']],
                                           'human_attitudes': [['Brad Pitt', 'actor', 'neutral'],
                                                               ['Quentin Tarantino', 'director', 'neutral']]}], \
        print(response)
    assert "They all good. But" in response[0], print(response)

    print("check_genre")
    input_data = get_input_json("test_configs/check_genre.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {'bot_attitudes': [['Comedy', 'genre', 'very_positive']],
                                           'human_attitudes': []}], \
        print(response)

    print("check_favorite_genres")
    input_data = get_input_json("test_configs/check_favorite_genres.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {'bot_attitudes': [['Comedy', 'genre', 'very_positive'],
                                                             ['Documentary', 'genre', 'very_positive'],
                                                             ['Sci-fi', 'genre', 'very_positive']],
                                           'human_attitudes': []}], \
        print(response)

    print("check_get_opinion_give_opinion")
    input_data = get_input_json("test_configs/check_get_opinion_give_opinion.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [0.98, {}, {}, {'bot_attitudes': [['Comedy', 'genre', 'very_positive']],
                                           'human_attitudes': [['Comedy', 'genre', 'very_positive']]}], \
        print(response)

    print("SUCCESS!")


if __name__ == '__main__':
    test_one_step_responses()
