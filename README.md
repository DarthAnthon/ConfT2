# ConfT2
# Этап 5. Визуализация
## 1. Общее описание. 
Минимальное CLI-приложение для визуализации графа зависимостей пакетов. Включает реализацию основной логики получения данных о зависимостях для их 
дальнейшего анализа и визуализации, а также построение и визуализация графа и основные операции над ним.

## 2. Описание всех функций и настроек. 

### Методы класса MavenDependencyResolver:

__init__(self, repository_url) - инициализация с указанием url адреса

_download_pom(self, group_id, artifact_id, version) - скачивание pom файла

_load_test_dependencies(self, group_id, artifact_id, version) - загрузка зависимостей из тестового файла

_create_test_pom_content(self, package_name, dependencies) - создание имитации pom файла для тестового режима

_parse_dependencies_from_pom(self, pom_content) - парсинг pom файла

get_dependencies(self, package_name) - получение зависимостей 

### Методы класса PackageManagerVisualizer:
__init__ - инициализация с указанием конфиг-файла

load_config() - загрузка конфигурации из INI-файла

parse_parameters() - парсинг и валидация параметров

display_dependencies(self, dependencies) - вывод зависимостей

apply_filter(self, dependencies, filter_substring) - применение фильтра к зависимостям

build_transitive_dependency_graph(self, root_package) - построение графа транзитивных зависимостей

display_dependency_statistics(self, dependency_graph) - вывод графа

display_back_dependencies(self, dependency_graph, target_package) - получение и вывод обратных зависимостей

create_dependency_graph(self, dependency_graph, output_filename) - визуализация графа

run() - основной метод запуска приложения

validate_package_name(package_name) - проверка корректности имени пакета

validate_repository_url(url) - проверка корректности URL репозитория

validate_test_mode(mode) - проверка корректности режима тестирования

validate_filename(filename) - проверка корректности имени файла

validate_filter_substring(substring) - проверка корректности подстроки фильтра

### Конфигурационные параметры

package_name - Имя анализируемого пакета

repository_url - URL-адрес репозитория

test_mode - Режим работы с тестовым репозиторием (true/false)

output_filename - Имя сгенерированного файла с изображением графа

filter_substring - Подстрока для фильтрации пакетов (опционально)
## 3. Описание команд для сборки проекта и запуска тестов. 

python t2.py config.ini - Запуск с указанием конфиг-файла

python t2.py config_test.ini - Запуск с указанием конфиг-файла для тестирования
## 4. Примеры использования.
<img width="1611" height="883" alt="image" src="https://github.com/user-attachments/assets/c0aa4580-cdf2-411a-8bf1-cf04752a879b" />



