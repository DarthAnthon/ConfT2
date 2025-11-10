import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import os

class DependencyError(Exception):
    pass

class MavenDependencyResolver:
    
    def __init__(self, repository_url, test_mode = False):
        self.repository_url = repository_url
        self.test_mode = test_mode
        self.dependencies_cache = {}
    
    def _download_pom(self, group_id, artifact_id, version):
        try:
            if self.test_mode:
                return self._load_test_dependencies(group_id, artifact_id, version)
            else:
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
    
    def _load_test_dependencies(self, group_id, artifact_id, version):
        try:
            package_name = artifact_id
            
            if not os.path.exists(self.repository_url):
                raise DependencyError(f"Тестовый файл не найден: {self.repository_url}")
            
            dependencies_map = {}
            with open(self.repository_url, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        source_package = parts[0]
                        deps = parts[1:]
                        dependencies_map[source_package] = deps
            
            if package_name in dependencies_map:
                deps = dependencies_map[package_name]
                pom_content = self._create_test_pom_content(package_name, deps)
                return pom_content
            else:
                return self._create_test_pom_content(package_name, [])
                
        except Exception as e:
            raise DependencyError(f"Ошибка загрузки тестовых зависимостей: {e}")

    def _create_test_pom_content(self, package_name, dependencies):
        deps_xml = ""
        for dep in dependencies:
            deps_xml += f"""
            <dependency>
                <groupId>test</groupId>
                <artifactId>{dep}</artifactId>
                <version>1.0</version>
                <scope>compile</scope>
            </dependency>"""
        
        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
                        <project>
                            <modelVersion>4.0.0</modelVersion>
                            <groupId>test</groupId>
                            <artifactId>{package_name}</artifactId>
                            <version>1.0</version>
                            <dependencies>
                                {deps_xml}
                            </dependencies>
                        </project>"""
        return pom_content

    def _parse_dependencies_from_pom(self, pom_content):
        try:

            root = ET.fromstring(pom_content)

            dependencies = []
            dependencies_elem = root.find('.//dependencies')
            if dependencies_elem is None:
                ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                dependencies_elem = root.find('.//maven:dependencies', ns)
            
            if dependencies_elem is not None:
                dep_elems = dependencies_elem.findall('dependency')
                if not dep_elems:
                    dep_elems = dependencies_elem.findall('maven:dependency', ns) if 'ns' in locals() else []
                
                for dep_elem in dep_elems:
                    group_id_elem = dep_elem.find('groupId')
                    artifact_id_elem = dep_elem.find('artifactId')
                    version_elem = dep_elem.find('version')
                    scope_elem = dep_elem.find('scope')
                    
                    if group_id_elem is None or artifact_id_elem is None:
                        group_id_elem = dep_elem.find('maven:groupId', ns) if 'ns' in locals() else None
                        artifact_id_elem = dep_elem.find('maven:artifactId', ns) if 'ns' in locals() else None
                        version_elem = dep_elem.find('maven:version', ns) if 'ns' in locals() else None
                        scope_elem = dep_elem.find('maven:scope', ns) if 'ns' in locals() else None
                    
                    if group_id_elem is None or artifact_id_elem is None:
                        continue
                    
                    group_id = group_id_elem.text.strip() if group_id_elem.text else ""
                    artifact_id = artifact_id_elem.text.strip() if artifact_id_elem.text else ""
                    
                    version = None
                    if version_elem is not None and version_elem.text:
                        version = version_elem.text.strip()
                    
                    if not version:
                        continue
                    
                    scope = 'compile'
                    if scope_elem is not None and scope_elem.text:
                        scope = scope_elem.text.strip()
                    
                    if scope == 'test':
                        continue
                    
                    if self.test_mode:
                        full_name = f"test:{artifact_id}:1.0"
                    else:
                        full_name = f"{group_id}:{artifact_id}:{version}"

                    dependency = {
                        'group_id': group_id,
                        'artifact_id': artifact_id,
                        'version': version,
                        'scope': scope,
                        'full_name': full_name
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