import os
import json
from requests import get, exceptions
import subprocess
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyUnregisteredError
from colorama import Fore, Style, init

# Инициализация colorama
init(autoreset=True)

# Путь к файлу сессии и конфигурации
session_name = 'my_userbot'
config_file = 'config.json'
repo_url = 'https://github.com/kawasaji/avocado-user-bot/releases'

# Функция для цветного вывода
def print_color(text, color=Fore.GREEN):
    print(color + text + Style.RESET_ALL)

# Функция для загрузки конфигурации из файла
def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

# Функция для сохранения конфигурации в файл
def save_config(config):
    with open(config_file, 'w') as f:
        json.dump(config, f)

# Функция для запроса API ID и API Hash
def request_api_credentials():
    print_color("Введите свои API_ID и API_HASH. Вы можете получить их на https://my.telegram.org", Fore.YELLOW)
    api_id = input("API_ID: ")
    api_hash = input("API_HASH: ")
    return api_id, api_hash

# Функция для выполнения обновления
def perform_update():
    try:
        # Получаем обновления из репозитория
        subprocess.run(["git", "fetch"], check=True)

        # Получаем список тегов и берем последний тег
        tags = subprocess.check_output(["git", "tag"]).decode('utf-8').strip().split('\n')

        if tags:
            latest_release = tags[-1]  # Предполагается, что теги отсортированы по времени
            print_color(f"Обновление до последнего релиза: {latest_release}", Fore.GREEN)

            # Переключаемся на последний релиз
            subprocess.run(["git", "checkout", latest_release], check=True)
            print_color("Код обновлен до последнего релиза!", Fore.GREEN)
            return True
        else:
            print_color("Нет доступных тегов для обновления.", Fore.YELLOW)
            return False
    except subprocess.CalledProcessError as e:
        print_color(f"Ошибка обновления: {e}", Fore.RED)
        return False

def restart_program():
    print_color("Перезапуск бота...", Fore.CYAN)
    os.execv(sys.executable, ['python'] + sys.argv)
# Проверка на наличие обновлений
async def check_for_updates() -> object:
    try:
        response = get('https://api.github.com/repos/kawasaji/avocado-user-bot/releases')
        response.raise_for_status()  # Проверяем, не возникла ли ошибка
        releases = response.json()  # Пробуем распарсить JSON

        if releases:  # Проверяем, есть ли релизы
            latest_version = releases[0]['tag_name']  # Берем первый релиз как последний

            if config.get('version') != latest_version:
                print_color(f"Доступна новая версия: {latest_version}", Fore.YELLOW)
                update = input("Обновить? (y/n): ")
                if update.lower() == 'y':
                    # Выполнение обновления
                    try:
                        result = subprocess.run(["git", "pull"], check=True)
                        print_color("Код обновлен успешно!", Fore.GREEN)

                        # Обновление конфигурации и перезапуск
                        config['version'] = latest_version
                        save_config(config)
                        print_color("Обновление завершено. Перезапуск...", Fore.GREEN)
                        restart_program()
                    except subprocess.CalledProcessError as e:
                        print_color(f"Ошибка обновления: {e}", Fore.RED)
        else:
            print_color("Нет доступных релизов.", Fore.YELLOW)

    except exceptions.HTTPError as http_err:
        print_color(f"HTTP ошибка: {http_err}", Fore.RED)
    except exceptions.RequestException as req_err:
        print_color(f"Ошибка запроса: {req_err}", Fore.RED)
    except ValueError as json_err:
        print_color(f"Ошибка при парсинге JSON: {json_err}", Fore.RED)
    except Exception as e:
        print_color(f"Ошибка при проверке обновлений: {e}", Fore.RED)

    except exceptions.HTTPError as http_err:
        print_color(f"HTTP ошибка: {http_err}", Fore.RED)
    except exceptions.RequestException as req_err:
        print_color(f"Ошибка запроса: {req_err}", Fore.RED)
    except ValueError as json_err:
        print_color(f"Ошибка при парсинге JSON: {json_err}", Fore.RED)
    except Exception as e:
        print_color(f"Ошибка при проверке обновлений: {e}", Fore.RED)

# Загрузка конфигурации
config = load_config()
api_id = config.get('api_id')
api_hash = config.get('api_hash')

# Проверяем наличие API ID и API Hash
if not api_id or not api_hash:
    api_id, api_hash = request_api_credentials()
    config['api_id'] = api_id
    config['api_hash'] = api_hash
    save_config(config)
    print_color("Конфигурация сохранена!", Fore.GREEN)

# Создаем клиент
client = TelegramClient(session_name, api_id, api_hash)

# Остальная часть вашего кода...

async def main():
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_color("Не авторизован. Введите свой номер телефона:", Fore.YELLOW)
            phone = input("Телефон: ")
            await client.send_code_request(phone)

            code = input(Fore.YELLOW + "Введите код из Telegram: ")
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input(Fore.RED + "Введите пароль для двухфакторной авторизации: ")
                await client.sign_in(password=password)
            print_color("Успешно авторизован!", Fore.GREEN)
        else:
            print_color("Уже авторизован.", Fore.GREEN)
            # Проверка обновлений после успешной авторизации
            await check_for_updates()

    except AuthKeyUnregisteredError:
        print_color("Ошибка: Неверные API_ID или API_HASH. Повторите ввод.", Fore.RED)
        os.remove(config_file)
        api_id, api_hash = request_api_credentials()
        config['api_id'] = api_id
        config['api_hash'] = api_hash
        save_config(config)
        print_color("Конфигурация обновлена. Перезапустите скрипт.", Fore.GREEN)

    # Пример использования клиента
    if await client.is_user_authorized():
        me = await client.get_me()
        print_color(f"Привет, {me.first_name}!", Fore.CYAN)

        print_color("Бот запущен", Fore.CYAN)

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
