# ConfT2
# Этап 1: Минимальный прототип с конфигурацией
## 1. Общее описание. 
Минимальное CLI-приложение для визуализации графа зависимостей пакетов.

## 2. Описание всех функций и настроек. 

### Методы класса PackageManagerVisualizer:
__init__ - инициализация с указанием конфиг-файла

load_config() - загрузка конфигурации из INI-файла

parse_parameters() - парсинг и валидация параметров

display_parameters() - вывод параметров в формате ключ-значение

run() - основной метод запуска приложения

validate_package_name(package_name) - проверка корректности имени пакета

validate_repository_url(url) - проверка корректности URL репозитория

validate_test_mode(mode) - проверка корректности режима тестирования

validate_filename(filename) - проверка корректности имени файла

validate_filter_substring(substring) - проверка корректности подстроки фильтра

### Конфигурационные параметры

package_name = requests - Имя анализируемого пакета

repository_url = https://pypi.org/simple/ - URL-адрес репозитория или путь к файлу тестового репозитория

test_mode = false - Режим работы с тестовым репозиторием (true/false)

output_filename = dependency_graph.png - Имя сгенерированного файла с изображением графа

filter_substring =  - Подстрока для фильтрации пакетов (опционально)
## 3. Описание команд для сборки проекта и запуска тестов. 

python t2.py config.ini - Запуск с указанием конфиг-файла
## 4. Примеры использования.
<img width="622" height="151" alt="image" src="https://github.com/user-attachments/assets/695e1fb2-132b-4325-8589-cb670d2e3793" />
