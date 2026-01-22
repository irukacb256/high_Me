import re
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader

def fix_django_template_syntax(content):
    """
    Djangoテンプレートタグ {% ... %} 内の演算子前後のスペース不足を補正する。
    例: {% if a==b %} -> {% if a == b %}
    """
    # 1. {% ... %} タグを抽出
    def normalize_tag(match):
        tag_content = match.group(0)
        
        # 1. タグ内の改行を削除し、複数のスペースを1つにまとめる
        processed = re.sub(r'\s+', ' ', tag_content)
        
        # 2. 演算子 (==, !=, <=, >=, <, >) の前後にスペースを挿入
        operators = ['==', '!=', '<=', '>=']
        for op in operators:
            pattern = rf'([^\s]){re.escape(op)}'
            processed = re.sub(pattern, rf'\1 {op}', processed)
            pattern = rf'{re.escape(op)}([^\s])'
            processed = re.sub(pattern, rf'{op} \1', processed)
            
        return processed

    return re.sub(r'(\{%[\s\S]*?%\}|\{\{[\s\S]*?\}\})', normalize_tag, content)

class FixSyntaxFilesystemLoader(FilesystemLoader):
    def get_contents(self, origin):
        content = super().get_contents(origin)
        return fix_django_template_syntax(content)

class FixSyntaxAppDirectoriesLoader(AppDirectoriesLoader):
    def get_contents(self, origin):
        content = super().get_contents(origin)
        return fix_django_template_syntax(content)
