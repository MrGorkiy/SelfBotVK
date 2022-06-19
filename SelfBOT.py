import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from time import sleep
import requests
import json


from confing import token


# Переопределим класс лонгпула, исключим вылеты бота при перезапуске серверов ВК
class MyLongSelfPool(VkLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print(f'Ошибка соединения: ' + e)


vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
longpoll = MyLongSelfPool(vk_session)


print('Запустил бота, работаем')  # удобно отследить, работает бот или нет


def send_peer(peer_id: int, text: str, keyboard=None, attachment=None,
              forward=None):  # Функция отправки сообщения
    """Функция отправляет сообщения в чаты по peer_id.

    https://dev.vk.com/method/messages.send

    :param peer_id: Обязательно поле с id чата
    :type peer_id: int
    :param text: Обязательное поле с текстом сообщения для отправки
    :type text: str
    :param keyboard: json с клавиатурой (необязательно)
    :param attachment: json с вложениями: фото, файлы и тд (необязательно)
    :param forward: Параметр для отправки сообщения в качестве ответа
    :return: После успешного выполнения возвращает идентификатор отправленного сообщения.
    """
    post = {
        'peer_id': peer_id,
        'message': text,
        'random_id': get_random_id(),
        'disable_mentions': 1
    }

    if keyboard != None:
        post['keyboard'] = keyboard
    if attachment != None:
        post['attachment'] = attachment
    if forward != None:
        post['forward'] = [
            json.dumps(
                {"peer_id": peer_id, "conversation_message_ids": [forward],
                 "is_reply": True})]
    return vk_session.method('messages.send', post)


def message_edit(peer_id: int, message: str, message_id: int):
    """Редактирование сообщения."""
    post = {
        "peer_id": peer_id,
        "message": message,
        "keep_forward_messages": 1,
        "message_id": message_id,
    }
    return vk_session.method("messages.edit", post)


def get_name(user_id: int):
    """Получает имя пользователя или группы и создаем обращение к нему в виде кликабельной ссылки."""
    try:
        name = vk_session.method('users.get', {
            'user_ids': user_id})  # получение данных о пользователе
        return f"@id{name[0]['id']} ({name[0]['first_name']} {name[0]['last_name']})"  # имя пользователя
    except:
        name = vk_session.method('groups.getById', {
            'group_id': str(user_id)[1:]})  # получение данных о группе
        return f"id{name[0]['id']} ({name[0]['name']}) | @{name[0]['screen_name']}"  # имя группы


def events(event):
    """Основная логика бота"""
    if event.type == VkEventType.MESSAGE_NEW:  # Ивент, если пришло новое сообщение

        # Переменные команд и аргуметов
        # ---------------------------------------------------------------------
        message = event.text.lower()  # Преобразует полученное сообщение (с маленьких букв)
        message_type = vk.messages.getById(
            message_ids=event.message_id)  # Возвращает сообщения по их идентификаторам.
        conversation_message_id = message_type['items'][0][
            'conversation_message_id']  # id сообщения


        # Шпаргалка, можно ниже раскоментировать и потестировать и посмотреть
        # ответы и как они выглядят
        # ---------------------------------------------------------------------
        # print(event)  # Ивент который мы получили с его данными, но не стоит
        # забывать что тут будет только event с новыми сообщениями, хочешь
        # ловить все ивенты, такой принт надо выводить выше 87 строки
        # print(message_type)  # Данные по сообщению https://dev.vk.com/method/messages.getById


        """Тут логика программы для примера
        
        1. Например получаем id пользователя по команде !ид,
        сработает если команду отправляем только указанный пользователь
        
        2. Отредактируем команду на нужное сообщение, при команде !редакт
        сработает если команду отправляем только указанный пользователь
        
        3. Ответим на сообщение с командой !ответ
        сработает если команду отправляем только указанный пользователь
        """
        # Создам переменную arg, чтобы записать в неё аргументы будущих команд
        arg = message[1:].split()[0]  # Убрал восклицательный знак и разделил сообщение по пробелам, взял первый элемент
        # Так же можно поступить с peer_id и создать другие переменные, для удобства и сокращения однотипоного кода
        # arg = message[1:].split() если создать переменную так, то можно ловить все параметры передаваемые в команде
        # например мы захотим передать несколько параметров !прогноз Нижний Новгород - нам нужно получить команду
        # она будет равна arg[0] (прогноз) и параметры переданные при написании команды arg[1] (нижний) и arg[2] (новгород) или arg[1:] (['нижний', 'новгород'])

        if message:  # Проверка на пустое сообщение, если пустое (стикер или файл, без текста) то возвращает False и не выполняется
            if message[0] == "!":  # Ловим только команды начинающиеся с восклицательного знака

                # Для примера не будем применять переменную созданную выше (arg), а ниже применим, удобно? не правда ли!
                if message[1:].split()[0] == "ид":  # От сообщения отсекнем первый символ [0] = !,
                    # разделим по пробелам и возьмем первое слово, оно будет командой,
                    # к примеру сообщение: !ид, будет ['ид']
                    # а сообщение: !ид @mrgorkiy, будет ['ид', '@mrgorkiy']
                    if message_type["items"][0]["from_id"] == 25429876:  # Проверим что отправитель сообщения это мы (наш id: 25429876)
                        send_peer(
                            message_type["items"][0]["peer_id"],  # Получим peer_id чата, откуда пришло сообщение, чтобы ответить в него
                            f"id: {message_type['items'][0]['peer_id']}",  # Отпрвляем текст, в нем будет peer_id, в основном в нем содержится просто id пользователя
                        )  # Отправим сообщение в этот чат, откуда пришло сообщение


                elif arg == "редакт":  # Ловим команды которые равны !редакт
                    if message_type["items"][0]["from_id"] == 25429876:  # если убрать, сработает на любого пользователя
                        message_edit(
                            message_type["items"][0]["peer_id"],
                            f'Я в своем познании настолько преисполнился...',
                            event.message_id,  # Получим id сообщения, которое нам пришло в ивенте, чтобы его отредактировать
                        )  # Редактируем отправленное сообщение


                elif arg == "ответ":  # Ловим команды которые равны !ответ
                    if message_type["items"][0]["from_id"] in [25429876, 561142571]:  # Или можно реагировать на нескольких пользователей
                        send_peer(
                            message_type["items"][0]["peer_id"],
                            f"Я ответил на это сообщение",
                            forward=conversation_message_id,  # Получаю conversation_message_id сообщения для ответа на него
                        )  # Отправляем ответ на полученную команду


while True:  # Бесконечный цикл
    try:  # Ловим ошибки, в случае возникновения
        for event in longpoll.listen():  # Ловим ивенты от vk_api
            events(event)  # Передаем все полученные ивенты в функцию
    except requests.exceptions.ReadTimeout:  # Обрабатываем ошибки
        print("\n Переподключение к серверам ВК \n")
        sleep(10)
    except Exception as e:
        print('Возникла неизвестная ошибка:', e)
        sleep(5)
