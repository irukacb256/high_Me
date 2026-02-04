import os
import re

REPLACEMENTS = {
    # Days array fix
    "['（日）, '（月）, '（火）, '（水）, '（木）, '（金）', '（土）]": "['（日）', '（月）', '（火）', '（水）', '（木）', '（金）', '（土）']",
    
    # New patterns from user feedback
    "繧貞。": "を元",
    "ぁE": "え",
    "譌･": "日",
    "窶。": "を元に",
    "窶ｼ": "！",
    "並び替ぁ": "並び替え",
    
    # Fragments from worker_review_list
    "、昴ｌ、槭ｌ": "それぞれ",
    "繝ｬ繝薙Η繝ｼ": "レビュー",
    "邨ゆ了＠た": "終了した",
    "繧帝∽ｿ｡": "を送信",
    "選抁E": "選択",
    "選抁": "選択",
    "梱匁E": "梱包",
    "梱匁": "梱包",
    "莉募。う": "仕分け",
    "莉募。": "仕分け",
    "決宁E": "決定",
    "決宁": "決定",
    "保孁E": "保存",
    "保孁": "保存",
    "すめE": "する",
    "∵･ｭ蜍吶′": "業務が",
    "Ρ繝ｼ繧ｫ繝ｼ": "ワーカー",
    "繝ｫ繝ｼ繝礼ｮ｡逅）": "グループ管理",
    
    # Fragments from message_list
    "、ｨ。√": "と",
    "Γ繝。そ繝ｼ繧ｸ": "メッセージ",
    "繝｡繝。そ繝ｼ繧ｸ": "メッセージ",
    "をｊ、ｨ繧翫〒きます": "やり取りできます",
    "をｊ、ｨ繧翫〒きる": "やり取りできる",
    "蛟句挨": "個別",
    
    # Fragments from template_list
    "、ｲ、ｪ蠖｢": "ひな形",
    "励◆": "した",
    "瑚｡ｨ遉ｺ": "表示",
    "、輔ｌ": "され",
    "、ｾう": "ます",
    "繧呈眠隕丈ｽ懈。": "を新規作成",
    "繧呈ｱゅａ、ｦいるたａ": "を求めているため",
    "、必要": "が必要",
    "、梧眠、励＞": "が新しい",
    "、≠繧翫∪、帙ｓ": "ありません",
    "、≠繧翫∪、吶": "あります",
    "、ｸ申込繧、薙→": "に申し込むこと",
    "、悟庄閭ｽに、ｪ繧翫∪、吶": "が可能になります",
    "、悟ｮ御了＠、ｦ": "が完了して",
    "、御ｿ晁ｨｼ": "保証",
    "、顔筏、苓ｾｼみ": "お申し込み",
    "ます九↑う≠を": "まかないあり",
    "、ｲ、ｪ": "ひな",
    "蠖｢": "形",
    "、梧眠": "が新し",
    "、励＞": "い",
    "並び替ぁE": "並び替え",
    "作成譌･": "作成日",
    
    # Fragments from job_posting_detail
    "莨第。": "休憩",
    "譎る俣": "時間",
    "業蜍吶。条件": "業務上の条件",
    "業蜍咏ｵゆ了凾": "業務終了時",
    "業蜍吶↓": "業務に",
    "業蜍吶": "業務",
    "繧堤｢ｺ隱）。": "を確認",
    "莨第。譎る俣": "休憩時間",
    
    # Fragments from checkin_management
    "繧｢繧ｦ繝育畑": "アウト用",
    "鮟。牡": "黄色",
    "コープ": "コード",
    "隐ｭみ霎ｼ繧薙〒": "読み込んで",
    "隱ｭみ霎ｼ繧薙〒": "読み込んで",
    "繧偵い繝励Μ": "をアプリ",
    
    # Common Patterns (Bulk from previous investigations)
    "譁ｰ隕丈ｽ懈。": "新規作成",
    "繝槭ャ繝√Φ繧ｰ": "マッチング",
    "菴懈。": "作成",
    "編雁E": "編集",
    "荳€隕ｧ": "一覧",
    "譛蛻昴。": "最初の",
    "笘・": "※",
    "窶ｻ": "※",
    "蜷郁ｨ": "合計",
    "蠕。∞": "待遇",
    "迺ｰ蠅。": "環境",
    "鬆。岼": "項目",
    "蜿肴丐": "反映",
    "蟶ｾ": "幅",
    "莉伜､画峩邱壹。": "日付変更線",
    "荳ｭ螟ｮ謠。∴": "中央揃え",
    "邵ｮ、ｾなし": "縮小なし",
    "蟄倥。": "存",
    "蟄倥": "存",
    "はぁE": "はい",
    "う＞う": "いいえ",
    "莉募。": "付帯",
    "菴菴": "全体",
    "逕ｻ髱｢": "画面",
    "蠢。★": "必ず",
    "蠢懷供": "応募",
    "驕。綾": "遅刻",
    "蟒ｶ髟ｷ": "延長",
    "譌ｩ一翫′繧": "早上がり",
    "蝣ｱ驟ｬ": "報酬",
    "悟ｿ。ｦ。": "必要",
    "一願ｨ倥。": "一括",
    "蝣ｴ名医": "場合",
    "御ｿｮ豁｣萓晞ｼ": "修正依頼",
    "阪′螻翫″ます吶。": "が届きます。",
    "譛ｪ邨碁ｨ楢。ｭ楢ｿ。": "未経験者歓迎",
    "繝舌う繧ｯ。剰ｻ企壼共蜿ｯ": "バイク・車通勤可",
    "譛崎｣）逕ｱ": "服装自由",
    "髮・梛": "集計",
    "雉。ｼ": "資格",
    "險ｼ譏取嶌": "証明書",
    "譛牙柑諤ｧ": "有効性",
    "判蜒上。": "判断",
    "豁｣確諤ｧ": "正確性",
    "陬懆ｶｳ": "補足",
    "蜈ｷ菴鍋噪": "具体的",
    "荳榊庄": "不可",
    "蜃ｺ蜍､": "出勤",
    "譌･莉": "日付",
    "。井ｾ具ｼ": "（例：",
    "繝帙。繝ｫ": "ホール",
    "繧ｭ繝。メ繝ｳ": "キッチン",
    "繝ｬ繧ｹ繝医Λ繝ｳ": "レストラン",
    "荳€": "一",
    "閾ｴ": "致",
    "隕ｧ": "覧",
    "隱ｿ逅": "調理",
    "｣懷勧": "補助",
    "繝。Μ繝舌Μ繝ｼ": "デリバリー",
    "莉募。、代。繝斐ャ繧ｭ繝ｳ繧ｰ": "仕分け・ピッキング",
    "繝輔か繝ｼ繝": "フォーム",
    "繝懊ャ繧ｯ繧ｹ": "ボックス",
    "繝ｯ繝ｼ繧ｫ繝ｼ": "ワーカー",
    "繝九・繧ｺ": "ニーズ",
    "繝・し繝ｼ": "ユーザー",
    "繝€繝・す繝･繝懊・繝・": "ダッシュボード",
    "繝√ぉ繝・け": "チェック",
    "繧､繝ｳ": "イン",
    "繝ｭ繧ｰ": "ログ",
    "繧｢繧ｦ繝・": "アウト",
    "繝帙・繝": "ホーム",
    "繝医ャ繝・": "トップ",
    "繝輔ぅ繝ｫ繧ｿ": "フィルタ",
    "繝懊ち繝ｳ": "ボタン",
    "繧ｹ繧ｿ繧､繝ｫ": "スタイル",
    "繧ｰ繝ｬ繝ｼ": "グレー",
    "閭梧勹": "背景",
    "繧ｿ繧､繝溘・": "High Me",
    "繝薙Ν": "ビル",
    "繝翫ン繧ｲ繝ｼ繧ｷ繝ｧ繝ｳ": "ナビゲーション",
    "繝倥ャ繝€": "ヘッダー",
    "繝輔ャ繧ｿ": "フッター",
    "逋ｽ縺・": "白い",
    "醫医き繝ｼ繝会ｼ。": "（カード形状）",
    "繧ｰ繧ｯ繧ｹ": "ボックス",
    "繝。け繧ｹ": "ボックス",
    "蜈ｱ騾壹。": "共通の",
    "医き繝ｼ繝會ｼ。": "（カード形状）",
    "繝ｻ": "・",
    "る白い。": "る白い",
    "繝ｬ繧レ": "レジ",
    "繧ｹ繝ｼ繝代": "スーパー",
    "繝ｭ繧ｰ繧｢繧ｦ繝": "ログアウト",
    "菴。": "。 ",
    "\u0080": "",
}

def repair_structural_errors(content):
    # Fix missing < for common tags
    # Handle cases like >i class=, >a class=, etc.
    tags = ['i', 'a', 'div', 'span', 'label', 'input', 'select', 'p', 'h1', 'h2', 'h3', 'strong', 'button', 'ul', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'form', 'img', 'template']
    for tag in tags:
        # Pattern 1: >tag (followed by space, newline, or >)
        content = re.sub(r'>(?<!<)(' + tag + r'[\s\n>])', r'><\1', content)
        # Pattern 2: " tag
        content = re.sub(r'\"\s+(?<!<)(' + tag + r'[\s\n>])', r'" <\1', content)
        # Pattern 3: "tag
        content = re.sub(r'\"(?<!<)(' + tag + r'[\s\n>])', r'\"<\1', content)

    # Legacy repairs
    content = re.sub(r'([^<])\/([a-zA-Z0-9]+)>', r'\1</\2>', content)
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
    # Fix specific "Job Template List" broken icons if structural repair misses
    content = content.replace('btn-action">i\n', 'btn-action"><i\n')
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
