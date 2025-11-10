import os
import sys
import PackageManagerVisualizer

def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    
    if not os.path.exists(config_file):
        print(f"Конфигурационный файл '{config_file}' не найден.")
        sys.exit(1)
    
    visualizer = PackageManagerVisualizer.PackageManagerVisualizer(config_file)
    visualizer.run()


if __name__ == "__main__":
    main()
