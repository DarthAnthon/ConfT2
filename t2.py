import configparser
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


class ConfigError(Exception):
    pass


class PackageManagerVisualizer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.params = {}
        
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
        
        if len(package_name.strip()) == 0:
            raise ConfigError("Имя пакета не может состоять только из пробелов")
        
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in forbidden_chars:
            if char in package_name:
                raise ConfigError(f"Имя пакета содержит запрещенный символ: '{char}'")
        
        return package_name.strip()
    
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
            
        except KeyError as e:
            raise ConfigError(f"Отсутствует обязательный параметр в конфигурации: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка парсинга параметров: {e}")
    
    def display_parameters(self):
        print("ПАРАМЕТРЫ КОНФИГУРАЦИИ")
        
        for key, value in self.params.items():
            print(f"{key:25}: {value}")
    
    def run(self):
        try:
            self.load_config()
            self.parse_parameters()
            self.display_parameters()
            
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