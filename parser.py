import os
import requests
from bs4 import BeautifulSoup
from androguard.misc import AnalyzeAPK
from urllib.parse import urlparse

def get_apk_info(apk_path):
    """Извлекает информацию о пакете и версии из APK-файла"""
    try:
        a, _, _ = AnalyzeAPK(apk_path)
        return a.get_package(), a.get_androidversion_name()
    except Exception as e:
        print(f"Ошибка анализа {apk_path}: {str(e)}")
        return None, None

def search_apkmirror(package_name):
    """Поиск приложения на APKMirror по названию пакета"""
    try:
        url = f"https://www.apkmirror.com/?s={package_name}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')

        if "We couldn't find any" in soup.text:
            return None

        result = soup.find('a', class_='fontBlack')
        return f"https://www.apkmirror.com{result['href']}" if result else None
    except Exception as e:
        print(f"Ошибка поиска: {str(e)}")
        return None

def get_latest_version(url):
    """Получает последнюю версию приложения"""
    try:
        # Если это прямая ссылка на APK
        if url.endswith('.apk'):
            return extract_version_from_filename(url)

        # Если это страница APKMirror
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        version_div = soup.find('div', class_='infoSlide-value')
        return version_div.text.strip() if version_div else None
    except Exception as e:
        print(f"Ошибка получения версии: {str(e)}")
        return None

def extract_version_from_filename(url):
    """Извлекает версию из имени файла"""
    filename = os.path.basename(urlparse(url).path)
    parts = filename.split('-')
    for part in parts:
        if part.replace('.', '').isdigit():
            return part
    return 'unknown'

def download_apk(url, filename):
    """Скачивает APK-файл"""
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Ошибка загрузки: {str(e)}")
        return False

def manual_search(package_name, apk_name):
    """Интерактивный поиск приложения"""
    print(f"\nПриложение '{apk_name}' ({package_name}) не найдено на APKMirror")
    print("Вы можете:")
    print("1. Ввести URL страницы приложения на APKMirror")
    print("2. Ввести прямую ссылку на APK-файл")
    print("3. Пропустить обновление")

    choice = input("Ваш выбор (1/2/3): ").strip()

    if choice == '1':
        url = input("Введите URL страницы APKMirror: ").strip()
        return url, 'page'
    elif choice == '2':
        url = input("Введите прямую ссылку на APK: ").strip()
        return url, 'direct'
    else:
        return None, 'skip'

def main():
    apk_files = [f for f in os.listdir() if f.lower().endswith('.apk')]
    with open('apk_list.txt', 'w') as f:
        f.write('\n'.join(apk_files))

    results = {'Обновлено': [], 'Не найдено': [], 'Нет обновлений': [], 'Ошибка загрузки': []}

    for apk in apk_files:
        package, version = get_apk_info(apk)
        if not package:
            results['Не найдено'].append(apk)
            continue

        app_page = search_apkmirror(package)

        # Если не найдено на APKMirror
        if not app_page:
            custom_url, url_type = manual_search(package, apk)
            if not custom_url:
                results['Не найдено'].append(apk)
                continue

            app_page = custom_url

        latest_ver = get_latest_version(app_page)
        if not latest_ver:
            results['Не найдено'].append(apk)
            continue

        if latest_ver > version:
            # Скачивание новой версии
            if url_type == 'direct':
                dl_status = download_apk(app_page, f"new_{apk}")
            else:
                # Здесь можно добавить парсинг страницы для получения ссылки на скачивание
                dl_status = False

            if dl_status:
                results['Обновлено'].append(apk)
            else:
                results['Ошибка загрузки'].append(apk)
        else:
            results['Нет обновлений'].append(apk)

    print("\nРезультаты обновления:")
    for status in results:
        print(f"{status}: {len(results[status])}")

if __name__ == '__main__':
    main()