find . custom modules webpreview -maxdepth 1 -name '*.py' | xargs isort
find . custom modules webpreview -maxdepth 1 -name '*.py' | xargs black
