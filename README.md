# ConfT2
# Этап 2. Сбор данных 
## 1. Общее описание. 
Минимальное CLI-приложение для визуализации графа зависимостей пакетов.

## 2. Описание всех функций и настроек. 

### Методы класса MavenDependencyResolver:

__init__(self, repository_url) - инициализация с указанием url адреса

_download_pom(self, group_id, artifact_id, version) - скачивание pom файла

_parse_dependencies_from_pom(self, pom_content) - парсинг pom файла

get_dependencies(self, package_name) - получение зависимостей 

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

package_name = org.springframework.boot:spring-boot-starter-web:2.7.0 - Имя анализируемого пакета

repository_url = https://repo1.maven.org/maven2 - URL-адрес репозитория

test_mode = false - Режим работы с тестовым репозиторием (true/false)

output_filename = dependency_graph.png - Имя сгенерированного файла с изображением графа

filter_substring =  - Подстрока для фильтрации пакетов (опционально)
## 3. Описание команд для сборки проекта и запуска тестов. 

python t2.py config.ini - Запуск с указанием конфиг-файла
## 4. Примеры использования.
<img width="1204" height="380" alt="image" src="https://github.com/user-attachments/assets/bc50c6e0-2a75-4bde-9079-2280eab52b63" />

