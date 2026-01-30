import os
import re

REPLACEMENTS = {
    # Days array fix
    "['（日）, '（月）, '（火）, '（水）, '（木）, '（金）, '（土）]": "['（日）', '（月）', '（火）', '（水）', '（木）', '（金）', '（土）']",
    
    # Core Functional Patterns
    "玁E": "率", "琁E": "理", "囁E": "回", "頁E": "順", "想宁E": "想定", "チE": "プ", "庁E": "店",
    "画僁E": "画像", "掲輁E": "掲載", "事業形慁E": "事業形態", "なぁE": "なし", "荳€閾ｴ": "一致",
    
    # Prefectures
    "北海遁E": "北海道", "青森省E": "青森県", "秋田省E": "秋田県", "譬・惠逵・": "栃木県",
    "群馬省E": "群馬県", "蜊・痩逵・": "千葉県", "山梨省E": "山梨県", "富山省E": "富山県",
    "蟯宣・逵・": "岐阜県", "静岡省E": "静岡県", "愛知省E": "愛知県", "三重省E": "三重県",
    "滋賀省E": "滋賀県", "京都庁E": "京都府", "大阪庁E": "大阪府", "兵庫省E": "兵庫県",
    "奈良省E": "奈良県", "和歌山省E": "和歌山県", "島根省E": "島根県", "岡山省E": "岡山県",
    "店・ｳｶ逵・": "広島県", "山口省E": "山口県", "徳島省E": "徳島県", "高知省E": "高知県",
    "福岡省E": "福岡県", "佐賀省E": "佐賀県", "熊本省E": "熊本県", "螟ｧ蛻・恁": "大分県",
    "鹿児島省E": "鹿児島県", "豐也ｸ・恁": "沖縄県", "山形省E": "山形県", "福島省E": "福島県",
    
    # Common Fragments (Clean)
    "繝輔か繝ｼ繝": "フォーム", "繝懊ャ繧ｯ繧ｹ": "ボックス", "繝ｯ繝ｼ繧ｫ繝ｼ": "ワーカー",
    "繝九・繧ｺ": "ニーズ", "繝・し繝ｼ": "ユーザー", "繝€繝・す繝･繝懊・繝・": "ダッシュボード",
    "繝√ぉ繝・け": "チェック", "繧､繝ｳ": "イン", "繝ｭ繧ｰ": "ログ", "繧｢繧ｦ繝・": "アウト",
    "繝帙・繝": "ホーム", "繝医ャ繝・": "トップ", "邱ｨ髮・": "編集", "繝輔ぅ繝ｫ繧ｿ": "フィルタ",
    "繝懊ち繝ｳ": "ボタン", "繧ｹ繧ｿ繧､繝ｫ": "スタイル", "繧ｰ繝ｬ繝ｼ": "グレー", "閭梧勹": "背景",
    "繧ｿ繧､繝溘・": "タイミー", "繝薙Ν": "ビル", "繝翫ン繧ｲ繝ｼ繧ｷ繝ｧ繝ｳ": "ナビゲーション",
    "繝倥ャ繝€": "ヘッダー", "繝輔ャ繧ｿ": "フッター", "逋ｽ縺・": "白い",
    
    # Broken Fragments (From previous runs)
    "医き繝ｼ繝会ｼ。": "（カード形状）",
    "白い。": "白い",
    "ボックス。": "ボックス",
    "繝。け繧ｹ": "ボックス",
    "蜈ｱ騾壹。": "共通の",
    "\u0080": "",
}

def repair_structural_errors(content):
    content = re.sub(r'([^<])\/([a-zA-Z0-9]+)>', r'\1</\2>', content)
    for tag in ['input', 'select', 'div', 'span', 'label', 'i ', 'a ', 'p>', 'h1>', 'h2>', 'h3>']:
        content = content.replace(f'>{tag}', f'><{tag}')
        content = content.replace(f'" {tag}', f'" <{tag}')
        content = content.replace(f'"{tag}', f'"<{tag}')
    def fix_option(m):
        val = m.group(1); label = m.group(2)
        if not label: label = val
        return f'<option value="{val}">{label}</option>'
    content = re.sub(r'<option value="([^">]+)(?:>)?([^"<]*)?<\/option(?:"| )?>', fix_option, content)
    content = content.replace('</option">', '</option>').replace('</p">', '</p>').replace('</div">', '</div>')
    content = content.replace('">>', '">').replace('value=">', 'value="')
    content = re.sub(r'所.所在地', '所在地', content); content = re.sub(r'所.在地', '所在地', content)
    return content

def repair_broken_filters(content):
    return re.sub(r'\|default:"([^"]+)\s*}}', r'|default:"\1" }}', content)

def repair_title_tag(content):
    def fix_match(m):
        inner_text = m.group(1)
        try: fixed_text = inner_text.encode('cp932').decode('utf-8'); return f"<title>{fixed_text}</title>"
        except: return m.group(0)
    return re.sub(r'<title>(.*?)</title>', fix_match, content, flags=re.DOTALL)

def process_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f: content = f.read()
    except: return False
    original_content = content
    content = repair_title_tag(content); content = repair_broken_filters(content); content = repair_structural_errors(content)
    sorted_reps = sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)
    for old, new in sorted_reps: content = content.replace(old, new)
    content = content.replace('(ベータ版)', 'TEMP_BETA').replace('(ベータ版', '(ベータ版)').replace('TEMP_BETA', '(ベータ版)')
    if content != original_content:
        try:
            with open(path, 'w', encoding='utf-8') as f: f.write(content)
            print(f"Ultra-repaired: {path}"); return True
        except: return False
    return False

def main():
    root_dirs = ['business/templates/business', 'administration/templates', 'jobs/templates', 'accounts/templates', 'templates']
    repaired_count = 0
    for rdir in root_dirs:
        abs_rdir = os.path.join(os.getcwd(), rdir)
        if not os.path.exists(abs_rdir): continue
        for root, dirs, files in os.walk(abs_rdir):
            for file in files:
                if file.endswith('.html'):
                    if process_file(os.path.join(root, file)): repaired_count += 1
    print(f"\nUltra-repair completed. Total files touched: {repaired_count}")

if __name__ == "__main__":
    main()
