import os
import json
import requests
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
repo_url = 'https://github.com/kawasaji/avocado-user-bot/releases/latest'  # Замените на URL вашего репозитория

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

# Проверка на наличие обновлений
def check_for_updates():
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release['tag_name']

        # Проверяем, не обновлен ли уже бот до последней версии
        if config.get('version') != latest_version:
            print_color(f"Доступна новая версия: {latest_version}", Fore.YELLOW)
            update = input("Обновить? (y/n): ")
            if update.lower() == 'y':
                if perform_update():
                    config['version'] = latest_version
                    save_config(config)
                    print_color("Обновление завершено. Перезапуск...", Fore.GREEN)
                    restart_program()
    except Exception as e:
        print_color(f"Ошибка при проверке обновлений: {e}", Fore.RED)

# Функция для выполнения обновления
def perform_update():
    try:
        result = subprocess.run(["git", "pull"], check=True)
        print_color("Код обновлен успешно!", Fore.GREEN)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_color(f"Ошибка обновления: {e}", Fore.RED)
        return False

# Функция для перезапуска программы
def restart_program():
    print_color("Перезапуск бота...", Fore.CYAN)
    os.execv(sys.executable, ['python'] + sys.argv)

async def main():
    print_color("Запуск Telegram user бота...", Fore.CYAN)

    # Подключение и обработка ошибок авторизации
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
            check_for_updates()

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

# Запускаем клиент
with client:
    client.loop.run_until_complete(main())
