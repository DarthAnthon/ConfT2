import configparser
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import MavenDependencyResolver as MDR
from collections import deque
#import graphviz

class ConfigError(Exception):
    pass

class PackageManagerVisualizer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.params = {}
        self.dependency_resolver = None

    def load_config(self):
        if not os.path.exists(self.config_file):
            raise ConfigError(f"Конфигурационный файл '{self.config_file}' не найден")
        
        try:
            self.config.read(self.config_file, encoding='utf-8')
        except Exception as e:
            raise ConfigError(f"Ошибка чтения конфигурационного файла: {e}")
        
        if 'DEFAULT' not in self.config:
            raise ConfigError("Секция [DEFAULT] не найдена в конфигурационном файле")
    
    def validate_package_name(self, package_name):
        if not package_name or not isinstance(package_name, str):
            raise ConfigError("Имя пакета не может быть пустым")
        
        package_name = package_name.strip()
        if self.params.get('test_mode', False):
            parts = package_name.split(':')
            if len(parts) != 3:
                raise ConfigError("В тестовом режиме имя пакета должно быть в формате test:X:1.0")
            
            group_id, artifact_id, version = parts
            if group_id != 'test':
                raise ConfigError("В тестовом режиме group_id должен быть 'test'")
            if not artifact_id.isupper() or len(artifact_id) != 1:
                raise ConfigError("В тестовом режиме artifact_id должен быть одной большой латинской буквой")
            if version != '1.0':
                raise ConfigError("В тестовом режиме version должен быть '1.0'")
        else:
            parts = package_name.split(':')
            if len(parts) != 3:
                raise ConfigError("Имя пакета должно быть в формате group:artifact:version")
            
            group_id, artifact_id, version = parts
            
            if not group_id or not artifact_id or not version:
                raise ConfigError("Все части имени пакета (group, artifact, version) должны быть указаны")
            
        forbidden_chars = ['/', '\\', '*', '?', '"', '<', '>', '|']
        for char in forbidden_chars:
            if char in package_name:
                raise ConfigError(f"Имя пакета содержит запрещенный символ: '{char}'")
        
        return package_name
    
    def validate_repository_url(self, url):
        if not url or not isinstance(url, str):
            raise ConfigError("URL репозитория не может быть пустым")
        
        url = url.strip()
        
        try:
            if self.params.get('test_mode', False):
                if not os.path.exists(url):
                    raise ConfigError(f"Тестовый файл не найден: {url}")
            else:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    if not os.path.exists(url):
                        raise ConfigError(f"Некорректный URL или путь к файлу: {url}")
        except Exception as e:
            raise ConfigError(f"Ошибка валидации URL репозитория: {e}")
        
        if url.endswith('/'):
            url = url[:-1]
        
        return url
    
    def validate_test_mode(self, mode):
        valid_modes = ['true', 'false', '1', '0', 'yes', 'no']
        mode_str = str(mode).lower().strip()
        
        if mode_str not in valid_modes:
            raise ConfigError(f"Некорректный режим работы: {mode}. Допустимые значения: {valid_modes}")
        
        return mode_str in ['true', '1', 'yes']
    
    def validate_filename(self, filename):
        if not filename or not isinstance(filename, str):
            raise ConfigError("Имя файла не может быть пустым")
        
        filename = filename.strip()
        
        valid_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.pdf']
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in valid_extensions:
            raise ConfigError(f"Неподдерживаемое расширение файла: {file_ext}. Допустимые: {valid_extensions}")
        
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in forbidden_chars:
            if char in filename:
                raise ConfigError(f"Имя файла содержит запрещенный символ: '{char}'")
        
        return filename
    
    def validate_filter_substring(self, substring):
        if substring is None:
            return ""
        
        if not isinstance(substring, str):
            raise ConfigError("Подстрока фильтра должна быть строкой")
        
        return substring.strip()
    
    def parse_parameters(self):
        try:
            test_mode = self.config['DEFAULT'].get('test_mode', 'false')
            self.params['test_mode'] = self.validate_test_mode(test_mode)

            package_name = self.config['DEFAULT'].get('package_name', '')
            self.params['package_name'] = self.validate_package_name(package_name)
            
            repository_url = self.config['DEFAULT'].get('repository_url', '')
            self.params['repository_url'] = self.validate_repository_url(repository_url)
            
            output_filename = self.config['DEFAULT'].get('output_filename', 'dependency_graph.png')
            self.params['output_filename'] = self.validate_filename(output_filename)
            
            filter_substring = self.config['DEFAULT'].get('filter_substring', '')
            self.params['filter_substring'] = self.validate_filter_substring(filter_substring)
            
            self.dependency_resolver = MDR.MavenDependencyResolver(self.params['repository_url'], self.params['test_mode'])

        except KeyError as e:
            raise ConfigError(f"Отсутствует обязательный параметр в конфигурации: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка парсинга параметров: {e}")
    
    def display_dependencies(self, dependencies):
        if not dependencies:
            print("Прямые зависимости не найдены")
            return
        
        print("\n")
        print("ПРЯМЫЕ ЗАВИСИМОСТИ")
        
        for i, dep in enumerate(dependencies, 1):
            scope_display = f" [{dep['scope']}]" if dep['scope'] != 'compile' else ""
            print(f"{i:2}. {dep['full_name']}{scope_display}")
        
        print(f"Всего зависимостей: {len(dependencies)}")
    
    def apply_filter(self, dependencies, filter_substring):
        if not filter_substring:
            return dependencies
        
        filtered = []
        for dep in dependencies:
            if filter_substring.lower() not in dep['full_name'].lower():
                filtered.append(dep)
        
        return filtered
    
    def build_transitive_dependency_graph(self, root_package):
        print(f"\nПостроение графа транзитивных зависимостей для: {root_package}")
        dependency_graph = {}
        visited = set()
        path = ""
        
        stack = deque([(root_package, path)])
        cycles_detected = []
        
        while stack:
            current_package = stack.pop()
            if current_package[0] in current_package[1]:
                cycle = current_package[1]+"->"+current_package[0]
                print(f"Обнаружена циклическая зависимость: {cycle}")
                continue
            if current_package in visited:
                continue
            visited.add(current_package)
            print(f"Анализ пакета: {current_package[0]}")
            
            try:
                dependencies = self.dependency_resolver.get_dependencies(current_package[0])

                filtered_dependencies = self.apply_filter(dependencies, self.params['filter_substring'])
                
                dependency_graph[current_package[0]] = filtered_dependencies
                for dep in filtered_dependencies:
                    dep_name = dep['full_name']
                    stack.append((dep_name, current_package[1] + "->" + current_package[0]))
                        
            except Exception as e:
                print(f"Ошибка при анализе пакета {current_package}: {e}")
                dependency_graph[current_package] = []

        if cycles_detected:
            print(f"\nОбнаружено циклических зависимостей: {len(cycles_detected)}")
            for cycle in cycles_detected:
                print(f"   {cycle}")
        return dependency_graph
    
    """
    def create_dependency_graph(self, dependency_graph, output_filename):
        try:
            dot = graphviz.Digraph(comment='Dependency Graph')
            dot.attr(rankdir='TB', size='12,8')
            
            for package, dependencies in dependency_graph.items():
                if package == self.params['package_name']:
                    dot.node(package, package, shape='ellipse', style='filled', 
                            color='lightblue2', fontsize='12', fontname='Arial')
                else:
                    dot.node(package, package, shape='box', style='filled',
                            color='lightgreen', fontsize='10', fontname='Arial')
                
                for dep in dependencies:
                    dep_name = dep['full_name']
                    dot.edge(package, dep_name)
            
            file_format = Path(output_filename).suffix[1:].lower()
            base_name = Path(output_filename).stem
            
            output_path = dot.render(filename=base_name, format=file_format, cleanup=True)
            
            print(f"\nПолный граф зависимостей сохранен в файл: {output_filename}")
            print(f"Полный путь: {output_path}")
            
        except Exception as e:
            print(f"Ошибка при создании графа: {e}", file=sys.stderr)
            raise
    """

    def display_dependency_statistics(self, dependency_graph):
        total_packages = len(dependency_graph)
        total_dependencies = 0
        
        for package, deps in dependency_graph.items():
            total_dependencies += len(deps)
        
        print(f"\n=== СТАТИСТИКА ГРАФА ЗАВИСИМОСТЕЙ ===")
        print(f"Всего пакетов в графе: {total_packages}")
        print(f"Всего зависимостей: {total_dependencies}")
        print(f"Фильтр подстроки: '{self.params['filter_substring']}'")
        
        print(f"\n=== СТРУКТУРА ГРАФА ===")
        print(dependency_graph)
        for package, deps in dependency_graph.items():
            print(f"{package} -> {[d['full_name'] for d in deps]}")

    def display_back_dependencies(self, dependency_graph, target_package):
        if not dependency_graph:
            print("Граф зависимостей еще не построен. Сначала выполните анализ пакета.")
            return []
        
        reverse_deps = []
        
        for package, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep['full_name'] == target_package:
                    reverse_deps.append(package)
                    break

        if not reverse_deps:
            print(f"Обратные зависимости для пакета '{target_package}' не найдены")
            return
        
        print(f"\nОБРАТНЫЕ ЗАВИСИМОСТИ ДЛЯ: {target_package}")
        
        for i, package in enumerate(reverse_deps, 1):
            print(f"{i:2}. {package}")
        
        print(f"Всего обратных зависимостей: {len(reverse_deps)}")

    def run(self):
        try:
            self.load_config()
            self.parse_parameters()

            dependencies = self.dependency_resolver.get_dependencies(self.params['package_name'])
            filtered_dependencies = self.apply_filter(dependencies, self.params['filter_substring'])
            self.display_dependencies(filtered_dependencies)
            
            full_dependency_graph = self.build_transitive_dependency_graph(self.params['package_name'])
            self.display_dependency_statistics(full_dependency_graph)

            name = "test:F:1.0"
            self.display_back_dependencies(full_dependency_graph, name)

        except ConfigError as e:
            print(f"Ошибка конфигурации: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            sys.exit(1)

            
            
        