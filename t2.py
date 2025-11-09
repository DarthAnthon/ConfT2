import configparser
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
import urllib.request
import urllib.error


class ConfigError(Exception):
    pass

class DependencyError(Exception):
    pass

class MavenDependencyResolver:
    
    def __init__(self, repository_url):
        self.repository_url = repository_url
        self.dependencies_cache = {}
    
    def _download_pom(self, group_id, artifact_id, version):
        try:
            group_path = group_id.replace('.', '/')
            pom_url = f"{self.repository_url}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
            
            print(f"Загрузка POM: {pom_url}")
            
            with urllib.request.urlopen(pom_url) as response:
                pom_content = response.read().decode('utf-8')
            
            return pom_content
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DependencyError(f"POM файл не найден для {group_id}:{artifact_id}:{version}")
            else:
                raise DependencyError(f"Ошибка HTTP при загрузке POM: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise DependencyError(f"Ошибка URL при загрузке POM: {e.reason}")
        except Exception as e:
            raise DependencyError(f"Неожиданная ошибка при загрузке POM: {e}")
    
    def _parse_dependencies_from_pom(self, pom_content):
        try:
            root = ET.fromstring(pom_content)

            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            dependencies = []

            dependencies_elem = root.find('.//maven:dependencies', ns)
            if dependencies_elem is not None:
                for dep_elem in dependencies_elem.findall('maven:dependency', ns):
                    group_id_elem = dep_elem.find('maven:groupId', ns)
                    artifact_id_elem = dep_elem.find('maven:artifactId', ns)
                    version_elem = dep_elem.find('maven:version', ns)
                    scope_elem = dep_elem.find('maven:scope', ns)
                    
                    if group_id_elem is None or artifact_id_elem is None:
                        continue
                    
                    group_id = group_id_elem.text.strip()
                    artifact_id = artifact_id_elem.text.strip()
                    
                    version = None
                    if version_elem is not None:
                        version = version_elem.text.strip()
                    
                    if not version:
                        continue
                    
                    scope = 'compile'
                    if scope_elem is not None:
                        scope = scope_elem.text.strip()
                    
                    if scope == 'test':
                        continue
                    
                    dependency = {
                        'group_id': group_id,
                        'artifact_id': artifact_id,
                        'version': version,
                        'scope': scope,
                        'full_name': f"{group_id}:{artifact_id}:{version}"
                    }
                    
                    dependencies.append(dependency)
            
            return dependencies
            
        except ET.ParseError as e:
            raise DependencyError(f"Ошибка парсинга POM XML: {e}")
        except Exception as e:
            raise DependencyError(f"Ошибка при разборе POM: {e}")
    
    def get_dependencies(self, package_name):
        if package_name in self.dependencies_cache:
            return self.dependencies_cache[package_name]
        
        try:
            parts = package_name.split(':')
            if len(parts) != 3:
                raise DependencyError("Имя пакета должно быть в формате group:artifact:version")
            
            group_id, artifact_id, version = parts
            
            pom_content = self._download_pom(group_id, artifact_id, version)
            
            dependencies = self._parse_dependencies_from_pom(pom_content)
            
            self.dependencies_cache[package_name] = dependencies
            
            return dependencies
            
        except DependencyError:
            raise
        except Exception as e:
            raise DependencyError(f"Ошибка получения зависимостей: {e}")
        
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
            package_name = self.config['DEFAULT'].get('package_name', '')
            self.params['package_name'] = self.validate_package_name(package_name)
            
            repository_url = self.config['DEFAULT'].get('repository_url', '')
            self.params['repository_url'] = self.validate_repository_url(repository_url)
            
            test_mode = self.config['DEFAULT'].get('test_mode', 'false')
            self.params['test_mode'] = self.validate_test_mode(test_mode)
            
            output_filename = self.config['DEFAULT'].get('output_filename', 'dependency_graph.png')
            self.params['output_filename'] = self.validate_filename(output_filename)
            
            filter_substring = self.config['DEFAULT'].get('filter_substring', '')
            self.params['filter_substring'] = self.validate_filter_substring(filter_substring)
            
            self.dependency_resolver = MavenDependencyResolver(self.params['repository_url'])

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
            if filter_substring.lower() in dep['full_name'].lower():
                filtered.append(dep)
        
        return filtered
    
    def run(self):
        try:
            self.load_config()
            self.parse_parameters()

            dependencies = self.dependency_resolver.get_dependencies(self.params['package_name'])
            filtered_dependencies = self.apply_filter(dependencies, self.params['filter_substring'])
            self.display_dependencies(filtered_dependencies)
            
        except ConfigError as e:
            print(f"Ошибка конфигурации: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    
    if not os.path.exists(config_file):
        print(f"Конфигурационный файл '{config_file}' не найден.")
        sys.exit(1)
    
    # Запуск визуализатора
    visualizer = PackageManagerVisualizer(config_file)
    visualizer.run()


if __name__ == "__main__":
    main()

