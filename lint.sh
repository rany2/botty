find . custom modules webpreview -maxdepth 1 -name '*.py' | xargs black
find . custom modules webpreview -maxdepth 1 -name '*.py' | xargs isort
