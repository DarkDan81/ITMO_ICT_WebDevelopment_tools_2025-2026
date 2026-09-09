# Дущенко Даниил, К3341

Лабораторные по средствам Web-программирования.

- [ЛР1: FastAPI и авторизация](Lr1/REPORT.md)
- [ЛР2: потоки, процессы и asyncio](Lr2/REPORT.md)
- [ЛР3: запуск всех сервисов в Docker](Lr3/README.md)
- [Отчёт на сервере](https://darkdan.ru/web-labs/)

Сборка документации из корня репозитория:

```bash
pip install -r requirements-docs.txt
python tools/update_report.py
mkdocs build --strict
```

Исходники документации находятся в docs этой папки. Готовый сайт — в папке docs в корне репозитория;
эту папку можно использовать как источник GitHub Pages.
