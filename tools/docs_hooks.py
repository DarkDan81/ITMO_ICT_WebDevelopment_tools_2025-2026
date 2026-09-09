from pathlib import Path
import re
from mkdocs.exceptions import PluginError


def on_pre_build(config):
    """Не публиковать текст, испорченный при сохранении кириллицы."""
    files = [Path(config.config_file_path), *Path(config.docs_dir).rglob('*.md'),
             *Path(config.docs_dir).rglob('*.html')]
    for file in files:
        if re.search(r'\?{3,}|\ufffd', file.read_text(encoding='utf-8')):
            raise PluginError(f'Повреждённая кодировка в {file}; восстановите текст перед сборкой')


def on_post_build(config):
    """Убираем хвостовые пробелы шаблона из генерируемых HTML-файлов."""
    for file in Path(config.site_dir).rglob("*.html"):
        content = file.read_text(encoding="utf-8")
        file.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")
