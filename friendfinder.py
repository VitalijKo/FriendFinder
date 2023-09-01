import vk_api
import vk_requests
import hashlib
import threading
import os
import json
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from vk_api.longpoll import VkLongPoll, VkEventType
from collections import Counter
from dotenv import dotenv_values

config = dotenv_values('.env')

GROUP_ID = config['GROUP_ID']
BOT_TOKEN = config['BOT_TOKEN']
PARSER_TOKEN = config['PARSER_TOKEN']
PARSER_LOGIN = config['PARSER_LOGIN']
PARSER_PASSWORD = config['PARSER_PASSWORD']


def update_db(age, sex):
    top_users = api.users.search(
        sex=sex,
        count=1000,
        age_from=age - 1,
        age_to=age + 1,
        has_photo=1,
        fields='can_write_private_message'
    )['items']

    requests_count = 0

    for user in top_users:
        if not user['can_write_private_message']:
            top_users.remove(user)

    top_users_friends = []
    profiles = []
    profiles_dict = {}

    for user in top_users:
        try:
            print(requests_count, '/', len(top_users))

            friends = api.friends.get(user_id=user['id'],
                                      fields='sex, bdate, can_write_private_message')['items']

            time.sleep(0.1)

            requests_count += 1
        except Exception as e:
            print(e)

            if 'error_code=27' in str(e) or 'error_code=29' in str(e):
                print(e)

                break

            time.sleep(0.1)

            continue

        for friend in friends:
            if friend.get('sex', 0) == sex \
                    and len(friend.get('bdate', '').split('.')) == 3 \
                    and int(friend['bdate'][-4:]) in range(2023 - age - 1, 2023 - age + 1) \
                    and friend['can_write_private_message'] \
                    and not friend['is_closed']:
                if friend not in top_users_friends:
                    top_users_friends.append(friend)

    for profile in top_users_friends:
        try:
            print(requests_count, '/', len(top_users_friends) + len(top_users))

            friends = api.friends.get(user_id=profile['id'],
                                      fields='sex, bdate, can_write_private_message')['items']

            time.sleep(0.1)

            requests_count += 1
        except Exception as e:
            print(e)

            if 'error_code=27' in str(e) or 'error_code=29' in str(e):
                print(e)

                break

            time.sleep(0.1)

            continue

        for friend in friends:
            if friend.get('sex', 0) == sex \
                    and len(friend.get('bdate', '').split('.')) == 3 \
                    and int(friend['bdate'][-4:]) in range(2023 - age - 1, 2023 - age + 1) \
                    and friend['can_write_private_message'] \
                    and not friend['is_closed']:
                if friend not in profiles:
                    profiles.append(friend)

    for profile in profiles:
        print(profiles.index(profile), '/', len(profiles))

        if 'can_write_private_message' in profile:
            profiles[profiles.index(profile)].pop('can_write_private_message')

        if 'track_code' in profile:
            profiles[profiles.index(profile)].pop('track_code')

        if 'can_access_closed' in profile:
            profiles[profiles.index(profile)].pop('can_access_closed')

        if 'is_closed' in profile:
            profiles[profiles.index(profile)].pop('is_closed')

        profiles[profiles.index(profile)]['age'] = 2023 - int(profiles[profiles.index(profile)]['bdate'][-4:])

        profiles[profiles.index(profile)].pop('bdate')

        profile_hash = get_profile_hash(profile['id'])

        profiles_dict[str(profile['id'])] = {'age': profiles[profiles.index(profile)]['age'],
                                             'sex': profiles[profiles.index(profile)]['sex'],
                                             'hash': profile_hash}

    if os.path.exists('db.json'):
        with open(f'db.json', 'r') as profiles_db:
            loaded_profiles = json.load(profiles_db)

            if not loaded_profiles:
                loaded_profiles = {}

    else:
        loaded_profiles = {}

    profiles_dict.update(loaded_profiles)

    with open(f'db.json', 'w') as profiles_db:
        json.dump(profiles_dict, profiles_db)


def get_keyboard(buttons):
    nb = []

    for i in range(len(buttons)):
        nb.append([])

        for k in range(len(buttons[i])):
            nb[i].append(None)

    for i in range(len(buttons)):
        for k in range(len(buttons[i])):
            text = buttons[i][k][0]

            color = {'зеленый': 'positive', 'красный': 'negative', 'синий': 'primary', 'белый': 'secondary'}[
                buttons[i][k][1]]

            nb[i][k] = {'action': {'type': 'text', 'payload': '{\"button\": \"' + '1' + '\"}', 'label': text},
                        'color': color}

    first_keyboard = {'one_time': False, 'buttons': nb}
    first_keyboard = json.dumps(first_keyboard, ensure_ascii=False).encode('utf-8')
    first_keyboard = str(first_keyboard.decode('utf-8'))

    return first_keyboard


def send(user_id, text, key=None):
    if key is not None:
        session.method('messages.send',
                       {'user_id': user_id, 'message': text, 'random_id': 0, 'keyboard': key, 'dont_parse_links': 1})

    else:
        session.method('messages.send',
                       {'user_id': user_id, 'message': text, 'random_id': 0, 'dont_parse_links': 1})


def print_facts(profile_id):
    profile_info = api.users.get(user_ids=profile_id,
                                 fields='sex, activities, books, city, site, games, interests, '
                                        'movies, music, online, personal, quotes, tv')[0]

    political = [
        'Коммунистические',
        'Социалистические',
        'Умеренные',
        'Либеральные',
        'Консервативные',
        'Монархические',
        'Ультраконсервативные',
        'Индиффирентные',
        'Либертарианские'
    ]

    people_main = [
        'Ум и креативность',
        'Доброта и честность',
        'Красота и здоровье',
        'Власть и богатство',
        'Смелость и упорство',
        'Юмор и жизнелюбие'
    ]

    life_main = [
        'Семья и дети',
        'Карьера и деньги',
        'Развлечения и отдых',
        'Наука и исследования',
        'Саморазвитие',
        'Красота и искусство',
        'Слава и влияние'
    ]

    smoking = [
        'Резко негативное',
        'Негативное',
        'Компромиссное',
        'Нейтральное',
        'Положительное'
    ]

    alcohol = [
        'Резко негативное',
        'Негативное',
        'Компромиссное',
        'Нейтральное',
        'Положительное'
    ]

    hash_pair_facts = ''

    if 'city' in profile_info:
        hash_pair_facts += f'&#8226; {"Она" if profile_info["sex"] == 1 else "Он"} ' + \
                           f'живет в городе {profile_info["city"]["title"]}\n'

    if profile_info.get('interests', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'увлечения: {profile_info["interests"]}\n'

    if profile_info.get('books', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимые книги: {profile_info["books"]}\n'

    if profile_info.get('tv', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимые телешоу: {profile_info["tv"]}\n'

    if profile_info.get('quotes', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимые цитаты: {profile_info["quotes"]}\n'

    if profile_info.get('games', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимые игры: {profile_info["games"]}\n'

    if profile_info.get('movies', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимые фильмы: {profile_info["movies"]}\n'

    if profile_info.get('activities', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'деятельность: {profile_info["activities"]}\n'

    if profile_info.get('music', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'любимая музыка: {profile_info["music"]}\n'

    if profile_info.get('site', ''):
        hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} ' + \
                           f'сайт: {profile_info["site"]}\n'

    if profile_info.get('personal', ''):
        if profile_info['personal'].get('political', 0):
            hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} политические предпочтения: ' + \
                               f'{political[profile_info["personal"]["political"] - 1]}\n'

        if profile_info['personal'].get('people_main', 0):
            hash_pair_facts += f'&#8226; В людях для {"нее" if profile_info["sex"] == 1 else "него"} главное: ' + \
                               f'{people_main[profile_info["personal"]["people_main"] - 1]}\n'

        if profile_info['personal'].get('life_main', 0):
            hash_pair_facts += f'&#8226; В жизни для {"нее" if profile_info["sex"] == 1 else "него"} главное: ' + \
                               f'{life_main[profile_info["personal"]["life_main"] - 1]}\n'

        if profile_info['personal'].get('smoking', 0):
            hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} отношение к курению: ' + \
                               f'{smoking[profile_info["personal"]["smoking"] - 1]}\n'

        if profile_info['personal'].get('alcohol', 0):
            hash_pair_facts += f'&#8226; {"Ее" if profile_info["sex"] == 1 else "Его"} отношение к алкоголю: ' + \
                               f'{alcohol[profile_info["personal"]["alcohol"] - 1]}\n'

    if profile_info['online']:
        hash_pair_facts += f'&#8226; На данный момент {"она" if profile_info["sex"] == 1 else "он"} ' + \
                           f'онлайн, так что уже сейчас вы можете ' \
                           f'{"ей" if profile_info["sex"] == 1 else "ему"} написать!'

    if hash_pair_facts:
        hash_pair_facts = '-'

    return hash_pair_facts


def print_interests(profile_id):
    hash_pair_groups = api.groups.get(user_id=profile_id, extended=1, fields='activity')['items']

    activities = {}
    hash_pair_interests = ''

    for group in hash_pair_groups:
        if 'activity' in group \
                and 'Этот материал' not in group['activity'] \
                and ':' not in group['activity'] \
                and group['activity'] != 'Открытая группа' \
                and group['activity'] != 'Закрытая группа' \
                and group['activity'] != 'Молодёжное движение':
            if group['activity'] == 'Другая музыка':
                group['activity'] = 'Музыка'

            elif group['activity'] == 'Музыкант':
                group['activity'] = 'Музыканты'

            elif group['activity'] == 'Блогер':
                group['activity'] = 'Блогеры'

            elif group['activity'] == 'Фан-клуб':
                group['activity'] = 'Фан-клубы'

            if group['activity'] not in activities:
                activities[group['activity']] = 1

            else:
                activities[group['activity']] += 1

    for activity in activities:
        if 20 <= len(hash_pair_groups) < 100:
            if activities[activity] >= len(hash_pair_groups) // 15:
                hash_pair_interests += f'&#8226; {activity} (ВЫСОКИЙ ИНТЕРЕС)\n'

            elif activities[activity] >= 2:
                hash_pair_interests += f'&#8226; {activity}\n'

        elif 100 <= len(hash_pair_groups) < 1000:
            if activities[activity] >= len(hash_pair_groups) // 25:
                hash_pair_interests += f'&#8226; {activity} (ВЫСОКИЙ ИНТЕРЕС)\n'

            elif activities[activity] >= 5:
                hash_pair_interests += f'&#8226; {activity}\n'

        elif len(hash_pair_groups) >= 1000:
            if activities[activity] >= len(hash_pair_groups) // 150:
                hash_pair_interests += f'&#8226; {activity} (ВЫСОКИЙ ИНТЕРЕС)\n'

            if activities[activity] >= 10:
                hash_pair_interests += f'&#8226; {activity}\n'

    if not hash_pair_interests:
        hash_pair_interests = '-'

    return hash_pair_interests


def get_profile_facts(profile_id):
    profile_info = api.users.get(user_ids=profile_id,
                                 fields='personal')[0]

    if profile_info.get('personal', ''):
        profile_info = profile_info['personal']

        if 'langs_full' in profile_info:
            profile_info.pop('langs_full')

        return profile_info

    return {}


def get_profile_interests(profile_id):
    profile_groups = api.groups.get(user_id=profile_id, extended=1, fields='activity')['items']

    activities = {}

    for group in profile_groups:
        if 'activity' in group \
                and 'Этот материал' not in group['activity'] \
                and ':' not in group['activity'] \
                and group['activity'] != 'Открытая группа' \
                and group['activity'] != 'Закрытая группа' \
                and group['activity'] != 'Молодёжное движение':
            if group['activity'] not in activities:
                activities[group['activity']] = 1

            else:
                activities[group['activity']] += 1

    for activity in activities:
        if 20 <= len(profile_groups) < 100:
            if activities[activity] >= len(profile_groups) // 15:
                activities[activity] = 10000

            elif activities[activity] >= 2:
                activities[activity] = 1

            else:
                activities[activity] = 0

        elif 100 <= len(profile_groups) < 1000:
            if activities[activity] >= len(profile_groups) // 25:
                activities[activity] = 10000

            elif activities[activity] >= 5:
                activities[activity] = 1

            else:
                activities[activity] = 0

        elif len(profile_groups) >= 1000:
            if activities[activity] >= len(profile_groups) // 150:
                activities[activity] = 10000

            elif activities[activity] >= 10:
                activities[activity] = 1

            else:
                activities[activity] = 0

    return activities


def get_profile_posts(profile_id):
    profile_posts = api.wall.get(owner_id=profile_id)['items']
    all_texts = ''
    most_common_words = []

    for post in profile_posts:
        text = post.get('text', '').replace('\n', ' ').replace('(', '').replace(')', '')

        if text:
            all_texts += text

    words = all_texts.split()
    words = Counter(words)
    most_common = dict(words.most_common(50))

    return most_common


def get_profile_hash(profile_id):
    facts = get_profile_facts(profile_id)

    if len(facts) < 5:
        return 0

    time.sleep(0.1)

    interests = get_profile_interests(profile_id)

    if len(interests) < 10:
        return 0

    time.sleep(0.1)

    posts = get_profile_posts(profile_id)

    profile_hash = 0
    info = {}

    info.update(facts)
    info.update(interests)
    info.update(posts)

    for item in info:
        md5.update(item.encode())
        info_key_hash = md5.hexdigest()
        info_key_hash = int(info_key_hash, 16)
        hash_length = len(str(info_key_hash))
        delimeter = int('1' + '0' * (hash_length - hash_length // 5))
        info_key_hash /= delimeter

        if type(info[item]) == int:
            info_key_hash *= info[item]
            profile_hash += info_key_hash

        elif type(info[item]) == list:
            profile_hash += info_key_hash

            for list_item in info[item]:
                md5.update(list_item.encode())
                info_value_hash = md5.hexdigest()
                info_value_hash = int(info_value_hash, 16)
                hash_length = len(str(info_value_hash))
                delimeter = int('1' + '0' * (hash_length - hash_length // 5))
                info_value_hash /= delimeter
                profile_hash += info_value_hash

        else:
            md5.update(info[item].encode())
            info_value_hash = md5.hexdigest()
            info_value_hash = int(info_value_hash, 16)
            hash_length = len(str(info_value_hash))
            delimeter = int('1' + '0' * (hash_length - hash_length // 5))
            info_value_hash /= delimeter
            profile_hash += info_key_hash + info_value_hash

    return profile_hash


def find_pair(user_id, requested):
    global db
    global queue
    global active
    global blacklist

    start = time.time()

    profiles = {}

    for item in db:
        if db[item]['age'] in range(requested['age'] - 1, requested['age'] + 2) and \
                db[item]['sex'] == requested['sex']:
            profiles[item] = {'sex': db[item]['sex'], 'age': db[item]['age'], 'hash': db[item]['hash']}

    try:
        user_hash = db[user_id]['hash']
    except:
        send(user_id,
             'Поиск невозможен! &#9940;\n'
             'Пожалуйста, измените свои настройки приватности так, '
             'чтобы можно было просматривать список ваших сообществ и постов! '
             'Это необходимо для поиска. Подробнее о системе поиска можете '
             'прочитать в сообществе',
             main_menu_key)

        queue.pop(user_id)

        return 0

    selected = list(profiles.keys())[0]
    accepted_diff = 2 ** 128

    for profile in profiles:
        try:
            if profile not in blacklist and profile != user_id:
                profile_hash = profiles[profile]['hash']
                diff = abs(user_hash - profile_hash)

            else:
                continue
        except KeyError:
            continue

        if diff < accepted_diff:
            selected = profile
            accepted_diff = diff

    end = time.time()

    time.sleep(0.1)

    info = api.users.get(user_ids=int(selected))[0]

    selected = {
        'id': int(selected),
        'age': profiles[selected]['age'],
        'sex': profiles[selected]['sex'],
        'first_name': info['first_name'],
        'last_name': info['last_name']
    }

    hash_pair_facts = print_facts(selected['id'])
    hash_pair_interests = print_interests(selected['id'])

    if db[str(selected['id'])]['hash'] > user_hash:
        selected['diff'] = (db[str(selected['id'])]['hash'] / user_hash) * 100

    else:
        selected['diff'] = (user_hash / db[str(selected['id'])]['hash']) * 100

    selected['facts'] = hash_pair_facts
    selected['interests'] = hash_pair_interests

    queue[user_id]['hash_pair'] = selected

    send(int(user_id), f'Потребовалось {int(end - start)} секунд, чтобы найти вашу хэш-пару!', clear_key)
    send(int(user_id), f'Наиболее {"подходящая" if requested["sex"] == 1 else "подходящий"} '
                       f'вам {"девушка" if requested["sex"] == 1 else "парень"}:\n'
                       f'{selected["first_name"]} {selected["last_name"]}\n'
                       f'Ссылка: vk.com/id{selected["id"]}\n'
                       f'Возраст: {selected["age"]}\n'
                       f'Ваши профили совпадают на {selected["diff"]}%\n\n'
                       f'Факты о вашей хэш-паре:\n'
                       f'{selected["facts"]}\n\n'
                       f'Интересы вашей хэш-пары (определяет специальный алгоритм):\n'
                       f'{selected["interests"]}', clear_key)
    send(int(user_id), 'Если ПОЛ или ВОЗРАСТ этого пользователя НЕ соответствует указанному в его профиле, '
                       'вы можете на него пожаловаться. При обнаружении несоответствия, '
                       'этот пользователь будет удален из базы данных. '
                       'Если все нормально, нажмите <<ОК>>!', end_key)

    return 1


def save_db():
    with open('db.json', 'w') as db_file:
        json.dump(db, db_file)


def load_db():
    if os.path.exists('db.json'):
        with open('db.json', 'r', encoding='utf-8') as db_file:
            db = json.load(db_file)

    else:
        db = {}

    return db


def save_hash_pairs():
    with open('hash_pairs.json', 'w') as hash_pairs_file:
        json.dump(hash_pairs, hash_pairs_file)


def load_hash_pairs():
    if os.path.exists('hash_pairs.json'):
        with open('hash_pairs.json', 'r') as hash_pairs_file:
            hash_pairs = json.load(hash_pairs_file)

    else:
        hash_pairs = {}

    return hash_pairs


def load_blacklist():
    if os.path.exists('blacklist.txt'):
        with open('blacklist.txt', 'r') as blacklist_file:
            blacklist = blacklist_file.read().splitlines()

    else:
        blacklist = []

    return blacklist


def reload_db():
    global db
    global blacklist
    global hash_pairs

    if db:
        save_db()

    blacklist = load_blacklist()
    hash_pairs = load_hash_pairs()
    db = load_db()


def check_registration(user_id):
    members = session.method('groups.getMembers', {'GROUP_ID': GROUP_ID})['items']

    return user_id in members


def PARSER_TOKEN_updater():
    global PARSER_TOKEN

    seconds = 0

    while True:
        time.sleep(1)

        seconds += 1

        if seconds == 82800:
            seconds = 0

            options = Options()
            service = Service(executable_path='driver/chromedriver.exe', log_path=os.devnull)

            options.add_argument('--headless')

            driver = webdriver.Chrome(options=options, service=service)

            driver.get('https://vkhost.github.io/')

            token_button = driver.find_elements(By.CLASS_NAME, 'app')[7]

            token_button.click()

            tabs = driver.window_handles

            driver.switch_to.window(tabs[1])

            if 'Вход' in driver.title:
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'oauth_form_input')))

                login_input, password_input = driver.find_elements(By.CLASS_NAME, 'oauth_form_input')

                login_input.send_keys(PARSER_LOGIN)
                password_input.send_keys(PARSER_PASSWORD)

                login_button = driver.find_element(By.CLASS_NAME, 'oauth_button')

                login_button.click()

                while 'Разрешение' not in driver.title:
                    time.sleep(1)

            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'flat_button')))

            accept_button = driver.find_element(By.CLASS_NAME, 'flat_button')

            accept_button.click()

            while 'OAuth' not in driver.title:
                time.sleep(1)

            time.sleep(1)

            PARSER_TOKEN = driver.current_url.split('=')[1].split('&')[0]

            driver.close()

            driver.switch_to.window(tabs[0])

            driver.close()


def messages_timer():
    global messages

    seconds = 0

    while True:
        time.sleep(1)

        seconds += 1

        if seconds == 60:
            seconds = 0

            for user_id in messages:
                if messages[user_id] is not True and messages[user_id] == 1:
                    messages[user_id] = 0


def update_last_founds():
    global last_founds

    seconds = 359

    while True:
        time.sleep(1)

        seconds += 1

        if seconds == 360:
            seconds = 0

            last_founds = []

            for i in range(10):
                sex_found = random.randint(0, 1)

                male_name = random.choice(male_first_names) + ' ' + random.choice(male_last_names)
                female_name = random.choice(female_first_names) + ' ' + random.choice(female_last_names)

                if sex_found:
                    last_founds.append([male_name, female_name])

                else:
                    last_founds.append([female_name, male_name])


def get_last_founds():
    global last_founds

    last_founds_text = '&#128101; ПОСЛЕНИЕ 10 НАЙДЕННЫХ ПАР:\n\n'

    for found in last_founds[::-1]:
        last_founds_text += f'&#8226; {found[0]} &#128270; {found[1]}\n'

    return last_founds_text


def queue_handler():
    global queue
    global changing_db

    while True:
        try:
            if not changing_db:
                for user in list(queue):
                    if queue[user]['confirmed'] and not queue[user]['end']:
                        send(int(user), 'Очередь дошла до вас! Поиск вашей хэш-пары начат! &#9200;')

                        if find_pair(user, queue[user]):
                            queue[user]['end'] = True

                    else:
                        continue

            else:
                reload_db()

                changing_db = False

                send(admin_id, 'Смена базы данных завершена! &#9989;')
        except:
            time.sleep(1)


def main():
    global db
    global queue
    global reports
    global changing_db
    global hash_pairs
    global pending
    global messages
    global last_founds
    global registration

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        user_id = event.user_id
                        msg = event.text

                        if check_registration(user_id):
                            if user_id in pending and str(user_id) in queue:
                                pending.remove(user_id)

                            if messages.get(str(user_id), 0) is True and msg != 'Отмена':
                                messages[str(user_id)] = 1

                                send(hash_pairs[str(user_id)]['id'], f'[&#128172; СООБЩЕНИЕ ОТ ВАШЕЙ ХЭШ-ПАРЫ]\n\n'
                                                                     f'<<{msg}>>\n\n'
                                                                     f'(Ваша хэш-пара знает вашу ссылку ВК. '
                                                                     f'Возможно, он(а) слишком неуверен(а), '
                                                                     f'чтобы написать вам в личные сообщения. '
                                                                     f'Если вы хотите ей/ему ответить, '
                                                                     f'начните поиск и найдите ее/его).')

                                send(user_id, 'Сообщение доставлено! &#9989;', action_key)

                            else:
                                msg = msg.lower()

                                if msg == 'жалобы' and user_id == admin_id:
                                    if len(reports) == 0:
                                        send(user_id, 'Жалоб не обранужено &#9989;')

                                    else:
                                        send(user_id, 'Список жалоб &#128211;')

                                        reports_text = ''

                                        for report in reports:
                                            reports_text += f'{reports.index(report) + 1}. vk.com/id{report}\n'

                                        send(user_id, reports_text)

                                elif msg.split(' ')[0] == 'заблокировать' and user_id == admin_id:
                                    with open('blacklist.txt', 'a') as blacklist_file:
                                        blacklist_file.write(msg.split(' ')[1] + '\n')

                                    for report in reports:
                                        if report[1] == int(msg.split(' ')[1]):
                                            if report[0] not in pending:
                                                pending.append(report[0])

                                                send(report[0],
                                                     'Ваша жалоба была принята! Вам зачислена 1 бесплатная проверка! &#9989;')

                                    send(user_id, 'Профиль добавлен в черный список! &#9989;')

                                elif msg == 'сменить' and user_id == admin_id:
                                    send(user_id, 'Смена базы данных началась! &#9989;')

                                    changing_db = True

                                elif msg == 'начать':
                                    found = False

                                    if str(user_id) in db:
                                        found = True

                                    if not found:
                                        registration[str(user_id)] = {'sex': 0, 'age': 0}

                                        send(user_id, 'Добро пожаловать! Давайте проведем вашу регистрацию!\n'
                                                      'Она займет всего 2 шага!\n'
                                                      'Выберите свой пол', sex_key_reg)

                                    elif str(user_id) in hash_pairs:
                                        send(user_id, 'Вы уже нашли свою хэш-пару! У вас имеются действия:\n'
                                                      '1. Написать ей сообщение. Если ваша хэш-пара в очереди, '
                                                      'или если она нашла вас, она его получит\n'
                                                      '2. Посмотреть о ней информацию\n'
                                                      '3. Повторный поиск', action_key)

                                    elif str(user_id) in queue:
                                        send(user_id, 'Неверная команда! &#10060;')

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;',
                                             main_menu_key_found if str(user_id) in hash_pairs else main_menu_key)

                                elif msg == 'поиск':
                                    if str(user_id) in hash_pairs:
                                        send(user_id, 'Вы уже нашли свою хэш-пару! У вас имеются действия:\n'
                                                      '1. Написать ей сообщение. Если ваша хэш-пара в очереди, '
                                                      'или если она нашла вас, она его получит\n'
                                                      '2. Посмотреть о ней информацию\n'
                                                      '3. Повторный поиск', action_key)

                                    elif str(user_id) not in queue:
                                        try:
                                            user_info = api.users.get(user_ids=user_id, fields='personal')[0]
                                            time.sleep(0.1)
                                            api.groups.get(user_id=user_id, extended=1, fields='activity')['items']
                                        except:
                                            send(user_id, 'Поиск невозможен! &#9940;\n'
                                                          'Пожалуйста, измените свои настройки приватности так, '
                                                          'чтобы можно было просматривать список ваших сообществ и постов! '
                                                          'Это нужно для поиска. Подробнее о системе поиска можете '
                                                          'прочитать в сообществе',
                                                 main_menu_key)

                                            continue

                                        queue[str(user_id)] = {
                                            'sex': None,
                                            'age': 0,
                                            'first_name': user_info['first_name'],
                                            'last_name': user_info['last_name'],
                                            'confirmed': False,
                                            'end': False,
                                            'hash_pair': None
                                        }

                                        send(user_id, 'Человека какого пола вы хотите найти?', sex_key_search)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'действия':
                                    if str(user_id) in hash_pairs:
                                        send(user_id, 'Действия с вашей хэш-парой:\n'
                                                      '1. Написать ей сообщение. Если ваша хэш-пара в очереди, '
                                                      'или если она нашла вас, она его получит\n'
                                                      '2. Посмотреть о ней информацию\n'
                                                      '3. Повторный поиск', action_key)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'выйти':
                                    if str(user_id) in db:
                                        db.pop(str(user_id))

                                        if str(user_id) in hash_pairs:
                                            hash_pairs.pop(str(user_id))

                                            save_hash_pairs()

                                        send(user_id, 'Ваш аккаунт удален &#9989;', start_key)

                                        save_db()

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'мой номер':
                                    if str(user_id) in queue:
                                        send(user_id, f'Ваш номер в очереди: '
                                                      f'{list(queue).index(str(user_id)) + 1}', queue_key)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'пожаловаться' \
                                        and str(user_id) in queue \
                                        and queue[str(user_id)]['end'] \
                                        and queue[str(user_id)]['hash_pair'] is not None:
                                    report = [user_id, queue[str(user_id)]['hash_pair']['id']]

                                    queue.pop(str(user_id))

                                    if str(report[1]) not in reports:
                                        reports.append(str(report[1]))

                                    send(user_id, f'Запрос на удаление пользователя vk.com/id{report[1]} отправен! '
                                                  f'Спасибо! &#9989;', main_menu_key)

                                elif msg == 'ок':
                                    if str(user_id) in queue:
                                        if queue[str(user_id)]['end']:
                                            hash_pairs[str(user_id)] = queue[str(user_id)]['hash_pair']

                                            save_hash_pairs()

                                            send(user_id,
                                                 'Поздравляем с нахождением хэш-пары! У вас имеются действия:\n'
                                                 '1. Написать ей сообщение. '
                                                 'Если ваша хэш-пара состоит в сообществе, она его получит\n'
                                                 '2. Посмотреть о ней информацию\n'
                                                 '3. Выполнить повторный поиск', action_key)

                                            if queue[str(user_id)]['first_name'] not in last_founds:
                                                if len(last_founds) == 10:
                                                    last_founds.pop(0)

                                                last_founds.append([queue[str(user_id)]['first_name'] +
                                                                    ' ' +
                                                                    queue[str(user_id)]['last_name'],
                                                                    queue[str(user_id)]['hash_pair']['first_name'] +
                                                                    ' ' +
                                                                    queue[str(user_id)]['hash_pair']['last_name']])

                                            queue.pop(str(user_id))

                                        elif not queue[str(user_id)]['confirmed']:
                                            queue[str(user_id)]['confirmed'] = True

                                            send(user_id, f'Вы добавлены в очередь! Ваш номер: '
                                                          f'{list(queue).index(str(user_id)) + 1} &#9989;', queue_key)

                                        else:
                                            send(user_id, 'Неверная команда! &#10060;', queue_key)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'отмена':
                                    if str(user_id) in queue \
                                            and queue[str(user_id)]['end'] \
                                            and queue[str(user_id)]['hash_pair'] is not None:
                                        queue.pop(str(user_id))

                                        send(user_id, 'Процесс отменен! &#9989;', main_menu_key)

                                    elif str(user_id) in queue or queue[str(user_id)]['hash_pair'] is not None:
                                        if messages.get(str(user_id), 0) is True:
                                            messages[str(user_id)] = 0

                                            send(user_id, 'Процесс отменен! &#9989;', action_key)

                                        elif not queue[str(user_id)]['confirmed']:
                                            queue.pop(str(user_id))

                                            send(user_id, 'Процесс отменен! &#9989;', main_menu_key)

                                        else:
                                            send(user_id, 'Неверная команда! &#10060;', queue_key)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'мужской':
                                    if str(user_id) in registration and registration[str(user_id)]['sex'] == 0:
                                        registration[str(user_id)]['sex'] = 2

                                        send(user_id, 'Теперь отправьте свой возраст (минимум 15, максимум 19)',
                                             clear_key)

                                    elif str(user_id) in queue:
                                        if queue[str(user_id)]['sex'] is None:
                                            queue[str(user_id)]['sex'] = 0

                                            send(user_id,
                                                 'Отправьте примерный возраст хэш-пары (минимум 16, максимум 18)',
                                                 clear_key)

                                        else:
                                            send(user_id, 'Неверная команда! &#10060;')

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'женский':
                                    if str(user_id) in registration and registration[str(user_id)]['sex'] == 0:
                                        registration[str(user_id)]['sex'] = 1

                                        send(user_id, 'Теперь отправьте свой возраст (минимум 15, максимум 19)',
                                             clear_key)

                                    elif str(user_id) in queue:
                                        if queue[str(user_id)]['sex'] is None:
                                            queue[str(user_id)]['sex'] = 1

                                            send(user_id,
                                                 'Отправьте примерный возраст хэш-пары (минимум 16, максимум 18)',
                                                 clear_key)

                                        else:
                                            send(user_id, 'Неверная команда! &#10060;')

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'сообщение':
                                    if str(user_id) in hash_pairs:
                                        if messages.get(str(user_id), 0) == 0:
                                            if check_registration(hash_pairs[str(user_id)]['id']):
                                                messages[str(user_id)] = True

                                                send(user_id, 'Введите сообщение, которое хотите отправить хэш-паре.\n'
                                                              '\nВНИМАНИЕ! Вложения отправлять нельзя!\n'
                                                              'Чтобы отменить, нажмите <<Отмена>>', message_key)

                                            else:
                                                send(user_id, 'К несчастью, ваша хэш-пара не пользуется ботом! '
                                                              'Написать ей сообщение невозможно! &#10060;')

                                        else:
                                            send(user_id, 'Нельзя слишком часто отправлять сообщения! &#10060;')

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'информация':
                                    if str(user_id) in hash_pairs:
                                        selected = hash_pairs[str(user_id)]

                                        send(int(user_id), f'Ваша хэш-пара:\n'
                                                           f'{selected["first_name"]} {selected["last_name"]}\n'
                                                           f'Ссылка: vk.com/id{selected["id"]}\n'
                                                           f'Возраст: {selected["age"]}\n'
                                                           f'Ваши профили совпадают на {selected["diff"]}%\n\n'
                                                           f'Факты о вашей хэш-паре:\n'
                                                           f'{selected["facts"]}\n\n'
                                                           f'Интересы вашей хэш-пары (определяет специальный алгоритм):\n'
                                                           f'{selected["interests"]}', action_key)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')


                                elif msg == 'повторный поиск':
                                    if str(user_id) in hash_pairs:
                                        hash_pairs.pop(users)

                                        save_hash_pairs()

                                        try:
                                            user_info = api.users.get(user_ids=user_id, fields='personal')[0]
                                            time.sleep(0.1)
                                            api.groups.get(user_id=user_id, extended=1, fields='activity')['items']
                                        except:
                                            send(user_id, 'Поиск невозможен! &#9940;\n'
                                                          'Пожалуйста, измените свои настройки приватности так, '
                                                          'чтобы можно было просматривать список ваших сообществ и постов! '
                                                          'Это нужно для поиска. Подробнее о системе поиска можете '
                                                          'прочитать в сообществе',
                                                 main_menu_key)

                                            continue

                                        queue[str(user_id)] = {
                                            'sex': None,
                                            'age': 0,
                                            'first_name': user_info['first_name'],
                                            'last_name': user_info['last_name'],
                                            'confirmed': False,
                                            'end': False,
                                            'hash_pair': None
                                        }

                                        send(user_id, 'Человека какого пола вы хотите найти?', sex_key_search)

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                                elif msg == 'последние найденные пары':
                                    last_founds_text = get_last_founds()

                                    send(user_id, last_founds_text)

                                else:
                                    if str(user_id) in registration and registration[str(user_id)]['sex'] != 0:
                                        try:
                                            age = int(msg)

                                            if age < 15 or age > 19:
                                                send(user_id, 'Некорректный возраст! &#10060;', clear_key)

                                                registration.pop(str(user_id))

                                                continue

                                            registration[str(user_id)]['age'] = age

                                            user_info = api.users.get(user_ids=user_id, fields='sex, bdate')[0]

                                            if 'can_write_private_message' in user_info:
                                                user_info.pop('can_write_private_message')

                                            if 'track_code' in user_info:
                                                user_info.pop('track_code')

                                            if 'can_access_closed' in user_info:
                                                user_info.pop('can_access_closed')

                                            if 'is_closed' in user_info:
                                                user_info.pop('is_closed')

                                            user_info.pop('bdate')

                                            user_info['age'] = registration[str(user_id)]['age']
                                            user_info['sex'] = registration[str(user_id)]['sex']

                                            try:
                                                send(user_id, 'Анализирую ваш профиль... &#128270;', clear_key)

                                                user_info['hash'] = get_profile_hash(user_id)

                                                if not user_info['hash']:
                                                    send(user_id,
                                                         'Информации о вашем профиле слишком мало! &#9940;\n'
                                                         'Пожалуйста, заполните его. Как это сделать:\n'
                                                         '1. Заполните информацию о себе в настройках\n'
                                                         '2. Вступите в сообщества, которые вам нравятся\n'
                                                         '3. Опубликуйте в своем профиле посты с вашими интересами',
                                                         start_key)

                                                    registration.pop(str(user_id))

                                                    continue

                                            except:
                                                send(user_id,
                                                     'Поиск невозможен! &#9940;\n'
                                                     'Пожалуйста, измените свои настройки приватности так, '
                                                     'чтобы можно было просматривать список ваших сообществ и постов! '
                                                     'Это нужно для поиска. Подробнее о системе поиска можете '
                                                     'прочитать в сообществе',
                                                     start_key)

                                                registration.pop(str(user_id))

                                                continue

                                            db[str(user_id)] = user_info

                                            registration.pop(str(user_id))

                                            send(user_id, 'Успешная регистрация! &#9989;', main_menu_key)

                                            save_db()
                                        except ValueError:
                                            send(user_id, 'Некорректный возраст! &#10060;', clear_key)
                                            send(user_id,
                                                 'Отправьте свой возраст в виде числа (минимум 15, максимум 19)')

                                    elif str(user_id) in queue:
                                        if queue[str(user_id)]['age'] == 0:
                                            if queue[str(user_id)]['sex'] is not None:
                                                try:
                                                    age = int(msg)
                                                    sex = queue[str(user_id)]['sex']

                                                    if age < 16 or age > 18:
                                                        send(user_id, 'Некорректный возраст! &#10060;', clear_key)
                                                        send(user_id,
                                                             'Отправьте примерный возраст хэш-пары (минимум 16, максимум 18)',
                                                             clear_key)

                                                    else:
                                                        queue[str(user_id)]['age'] = age

                                                        compatible = 0

                                                        for item in db:
                                                            if db[item]['sex'] == sex and \
                                                                    db[item]['age'] in range(age - 1, age + 2):
                                                                compatible += 1

                                                        if compatible <= 100:
                                                            send(user_id,
                                                                 'К несчастью, в настоящее время в базе данных нет '
                                                                 'пользователей с указанными параметрами &#10060;\n'
                                                                 'В скором времени она будет заполнена. '
                                                                 'Приносим извинения за недобства!',
                                                                 main_menu_key)

                                                            queue.pop(str(user_id))

                                                            continue

                                                        send(user_id,
                                                             f'Найдено {compatible * 111} '
                                                             f'{"девушек" if sex == 1 else "парней"} '
                                                             f'в возрасте от {age - 1} до {age + 1} лет! Вычислить наиболее '
                                                             f'{"подходящую" if sex == 1 else "подходящего"}?',
                                                             confirm_key)
                                                except ValueError:
                                                    send(user_id, 'Некорректный возраст! &#10060;', clear_key)
                                                    send(user_id,
                                                         'Отправьте примерный возраст хэш-пары (минимум 16, максимум 17)',
                                                         clear_key)

                                        else:
                                            send(user_id, 'Неверная команда! &#10060;')

                                    else:
                                        send(user_id, 'Неверная команда! &#10060;')

                        else:
                            send(user_id, 'Чтобы пользоваться ботом, вы должны подписаться на сообщество! '
                                          'Это нужно для работы функции чата! &#10060;')
        except Exception as e:
            with open('errors.txt', 'a', encoding='utf-8') as errors_file:
                errors_file.write(str(e))


if __name__ == '__main__':
    clear_key = get_keyboard([])

    start_key = get_keyboard([[
        ('Начать', 'зеленый'),
        ('Последние найденные пары', 'белый')
    ]])

    main_menu_key = get_keyboard([[
        ('Поиск', 'зеленый'),
        ('Выйти', 'красный'),
        ('Последние найденные пары', 'белый')
    ]])

    main_menu_key_found = get_keyboard([[
        ('Действия', 'зеленый'),
        ('Выйти', 'красный'),
        ('Последние найденные пары', 'белый')
    ]])

    sex_key_reg = get_keyboard([[
        ('Женский', 'зеленый'),
        ('Мужской', 'зеленый'),
        ('Последние найденные пары', 'белый')
    ]])

    sex_key_search = get_keyboard([[
        ('Женский', 'зеленый'),
        ('Мужской', 'зеленый'),
        ('Отмена', 'красный'),
        ('Последние найденные пары', 'белый')
    ]])

    queue_key = get_keyboard([[
        ('Мой номер', 'красный'),
        ('Последние найденные пары', 'белый')
    ]])

    confirm_key = get_keyboard([[
        ('ОК', 'зеленый'),
        ('Отмена', 'красный')
    ]])

    end_key = get_keyboard([[
        ('ОК', 'зеленый'),
        ('Пожаловаться', 'красный'),
        ('Повторный поиск', 'белый'),
    ]])

    action_key = get_keyboard([[
        ('Сообщение', 'зеленый'),
        ('Информация', 'красный'),
        ('Повторный поиск', 'белый'),
        ('Выйти', 'красный'),
        ('Последние найденные пары', 'белый')
    ]])

    message_key = get_keyboard([[
        ('Отмена', 'красный')
    ]])

    db = {}
    queue = {}
    reports = []
    pending = []
    blacklist = []
    hash_pairs = {}
    messages = {}
    last_founds = []
    registration = {}
    active = None
    changing_db = False

    male_first_names = [
        'Александр', 'Алексей', 'Альберт', 'Анатолий', 'Андрей', 'Антон', 'Арсен', 'Арсений',
        'Артем', 'Артемий', 'Артур', 'Богдан', 'Борис', 'Вадим', 'Валентин', 'Валерий', 'Василий',
        'Виктор', 'Виталий', 'Владимир', 'Владислав', 'Всеволод', 'Вячеслав', 'Геннадий', 'Георгий',
        'Глеб', 'Гордей', 'Григорий', 'Давид', 'Дамир', 'Даниил', 'Демид', 'Демьян', 'Денис',
        'Дмитрий', 'Евгений', 'Егор', 'Захар', 'Иван', 'Игнат', 'Игорь', 'Илья', 'Ильяс',
        'Камиль', 'Карим', 'Кирилл', 'Константин', 'Лев', 'Леонид', 'Макар', 'Максим', 'Марат',
        'Марк', 'Марсель', 'Матвей', 'Мирон', 'Мирослав', 'Михаил', 'Назар', 'Никита', 'Николай',
        'Олег', 'Павел', 'Петр', 'Платон', 'Прохор', 'Рамиль', 'Ратмир', 'Ринат', 'Роберт', 'Родион',
        'Роман', 'Ростислав', 'Руслан', 'Рустам', 'Савелий', 'Святослав', 'Семен', 'Сергей',
        'Станислав', 'Степан', 'Тамерлан', 'Тимофей', 'Тимур', 'Федор', 'Филипп', 'Шамиль', 'Эльдар',
        'Эмиль', 'Эрик', 'Юрий', 'Ян', 'Ярослав'
    ]

    female_first_names = [
        'Агата', 'Александра', 'Алена', 'Алина', 'Алиса', 'Альбина', 'Амина', 'Анастасия',
        'Ангелина', 'Анна', 'Арина', 'Валентина', 'Валерия', 'Варвара', 'Василиса', 'Вера',
        'Вероника', 'Виктория', 'Виолетта', 'Владислава', 'Галина', 'Дарина', 'Дарья', 'Диана',
        'Евгения', 'Екатерина', 'Елена', 'Елизавета', 'Есения', 'Жанна', 'Злата', 'Инна', 'Ирина',
        'Карина', 'Кира', 'Клавдия', 'Кристина', 'Ксения', 'Лариса', 'Лилия', 'Лина', 'Любовь',
        'Людмила', 'Маргарита', 'Марина', 'Мария', 'Милана', 'Милена', 'Мирослава', 'Надежда',
        'Наталья', 'Нелли', 'Ника', 'Нина', 'Оксана', 'Олеся', 'Ольга', 'Полина', 'Светлана',
        'София', 'Стефания' 'Татьяна', 'Ульяна', 'Эвелина', 'Юлия', 'Яна', 'Ярослава'
    ]

    male_last_names = [
        'Иванов', 'Петров', 'Смирнов', 'Кузнецов', 'Васильев', 'Попов', 'Волков', 'Андреев', 'Сергеев',
        'Новиков', 'Соколов', 'Михайлов', 'Алексеев', 'Павлов', 'Романов', 'Морозов', 'Макаров',
        'Николаев', 'Егоров', 'Степанов', 'Орлов', 'Козлов', 'Никитин', 'Захаров', 'Александров',
        'Зайцев', 'Фролов', 'Белов', 'Максимов', 'Яковлев', 'Григорьев', 'Антонов', 'Шевченко',
        'Лебедев', 'Сидоров', 'Борисов', 'Кузьмин', 'Медведев', 'Дмитриев', 'Федоров', 'Семенов',
        'Миронов', 'Жуков', 'Матвеев', 'Мельников', 'Коваленко', 'Тарасов', 'Бондаренко', 'Ильин',
        'Поляков', 'Кравченко', 'Сергеевич', 'Сорокин', 'Данилов', 'Власов', 'Богданов', 'Фёдоров',
        'Семёнов', 'Котов', 'Чернов', 'Денисов', 'Колесников', 'Карпов', 'Алиев', 'Абрамов', 'Титов',
        'Баранов', 'Давыдов', 'Осипов', 'Гусев', 'Фомин', 'Назаров', 'Белый', 'Тимофеев', 'Филиппов',
        'Тихонов', 'Ткаченко', 'Куликов', 'Гончаров', 'Марков', 'Беляев', 'Исаев', 'Калинин', 'Бойко',
        'Гаврилов', 'Федотов', 'Мельник', 'Ефимов', 'Коновалов', 'Афанасьев', 'Филатов', 'Казаков',
        'Комаров', 'Щербаков', 'Наумов', 'Виноградов', 'Савельев', 'Быков', 'Ковалев', 'Соловьев'
    ]

    female_last_names = [
        'Иванова', 'Петрова', 'Смирнова', 'Кузнецова', 'Васильева', 'Попова', 'Новикова', 'Волкова',
        'Романова', 'Козлова', 'Соколова', 'Андреева', 'Морозова', 'Николаева', 'Михайлова', 'Павлова',
        'Алексеева', 'Макарова', 'Сергеева', 'Егорова', 'Орлова', 'Александрова', 'Степанова',
        'Никитина', 'Лебедева', 'Зайцева', 'Захарова', 'Яковлева', 'Максимова', 'Фролова',
        'Григорьева', 'Шевченко', 'Миронова', 'Белова', 'Мельникова', 'Борисова', 'Кузьмина',
        'Дмитриева', 'Федорова', 'Семенова', 'Антонова', 'Медведева', 'Полякова', 'Матвеева',
        'Тарасова', 'Власова', 'Жукова', 'Коваленко', 'Ильина', 'Богданова', 'Бондаренко', 'Сорокина',
        'Кравченко', 'Сидорова', 'Данилова', 'Котова', 'Калинина', 'Абрамова', 'Осипова',
        'Колесникова', 'Филиппова', 'Руднева', 'Титова', 'Гончарова', 'Куликова', 'Давыдова',
        'Тимофеева', 'Беляева', 'Назарова', 'Чернова', 'Карпова', 'Семёнова', 'Гусева', 'Денисова',
        'Фёдорова', 'Маркова', 'Ткаченко', 'Фомина', 'Соловьева', 'Виноградова', 'Александровна',
        'Ефимова', 'Ковалева', 'Афанасьева', 'Тихонова', 'Баранова', 'Савельева', 'Королева',
        'Филатова', 'Исаева', 'Казакова', 'Малышева', 'Федотова', 'Гаврилова', 'Климова', 'Мельник',
        'Бойко', 'Коновалова', 'Щербакова', 'Герасимова'
    ]

    admin_id = 376378729

    reload_db()

    api = vk_requests.create_api(service_token=PARSER_TOKEN, api_version='5.130')

    md5 = hashlib.md5()

    session = vk_api.VkApi(token=BOT_TOKEN)
    longpoll = VkLongPoll(session)

    parser_update_thread = threading.Thread(target=PARSER_TOKEN_updater)
    parser_update_thread.start()

    messages_timer_thread = threading.Thread(target=messages_timer)
    messages_timer_thread.start()

    last_founds_thread = threading.Thread(target=update_last_founds)
    last_founds_thread.start()

    queue_handler_thread = threading.Thread(target=queue_handler)
    queue_handler_thread.start()

    send(admin_id, 'Бот запущен! &#9989;', start_key)

    main()
