import os
import django
import sys

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import QualificationCategory, QualificationItem

# データ定義 (scripts/import_qualifications.py からコピー)
DATA = {
    "介護・福祉": [
        "介護職員初任者研修", "介護職員実務者研修", "介護福祉士", "社会福祉士",
        "精神保健福祉士", "ケアマネジャー（介護支援専門員）", "福祉用具専門相談員",
        "ガイドヘルパー（移動介護従事者）", "手話通訳士", "臨床心理士", "公認心理師"
    ],
    "医療": [
        "医師", "正看護師", "准看護師", "薬剤師", "診療放射線技師", "臨床検査技師",
        "理学療法士", "作業療法士", "視能訓練士", "言語聴覚士", "歯科医師", "歯科衛生士",
        "歯科技工士", "柔道整復師", "鍼灸師", "あん摩マッサージ指圧師", "登録販売者",
        "医療事務技能審査試験（メディカルクラーク）"
    ],
    "教育・保育": [
        "保育士", "幼稚園教諭", "小学校教諭", "中学校教諭", "高等学校教諭",
        "養護教諭", "特別支援学校教諭", "栄養教諭", "司書教諭", "学校図書館司書教諭",
        "日本語教師（登録日本語教員）", "チャイルドマインダー"
    ],
    "美容": [
        "美容師", "理容師", "ネイリスト技能検定", "JNAジェルネイル技能検定",
        "認定エステティシャン", "CIDESCOディプロマ", "アロマテラピー検定",
        "コスメ検定（日本化粧品検定）", "色彩検定", "パーソナルカラリスト検定"
    ],
    "飲食・栄養": [
        "調理師", "栄養士", "管理栄養士", "製菓衛生師", "食品衛生責任者",
        "フードコーディネーター", "食生活アドバイザー", "ソムリエ", "ふぐ調理師"
    ],
    "化学・薬品": [
        "危険物取扱者（甲種）", "危険物取扱者（乙種）", "危険物取扱者（丙種）",
        "毒物劇物取扱責任者", "高圧ガス製造保安責任者", "公害防止管理者"
    ],
    "自動車・機械": [
        "普通自動車第一種運転免許", "普通自動車第二種運転免許", 
        "中型自動車第一種運転免許", "中型自動車第二種運転免許",
        "大型自動車第一種運転免許", "大型自動車第二種運転免許",
        "大型特殊自動車免許", "けん引免許", "フォークリフト運転技能者",
        "玉掛技能者", "自動車整備士（1級）", "自動車整備士（2級）", "自動車整備士（3級）",
        "クレーン・デリック運転士", "移動式クレーン運転士"
    ],
    "IT・パソコン": [
        "ITパスポート", "基本情報技術者", "応用情報技術者", "情報セキュリティマネジメント",
        "ネットワークスペシャリスト", "データベーススペシャリスト", "プロジェクトマネージャ",
        "システムアーキテクト", "MOS（Microsoft Office Specialist）", "ウェブデザイン技能検定",
        "マクロ・VBAエキスパート"
    ],
    "法律・ビジネス": [
        "弁護士", "司法書士", "行政書士", "社会保険労務士", "中小企業診断士",
        "公認会計士", "税理士", "宅地建物取引士", "ファイナンシャルプランニング技能士（FP）",
        "日商簿記検定（1級）", "日商簿記検定（2級）", "日商簿記検定（3級）",
        "秘書検定", "TOEIC L&R", "実用英語技能検定（英検）"
    ],
    "建築・土木": [
        "一級建築士", "二級建築士", "木造建築士",
        "1級建築施工管理技士", "2級建築施工管理技士",
        "1級土木施工管理技士", "2級土木施工管理技士",
        "1級電気工事施工管理技士", "2級電気工事施工管理技士",
        "第一種電気工事士", "第二種電気工事士", "測量士", "測量士補",
        "インテリアコーディネーター"
    ],
    "その他": [
        "警備員指導教育責任者", "交通誘導警備業務検定", "施設警備業務検定",
        "クリーニング師", "旅行業務取扱管理者", "通関士", "学芸員"
    ]
}

def restore():
    print("Start restoring qualifications...")
    cat_count = 0
    item_count = 0
    
    for order, (cat_name, items) in enumerate(DATA.items(), 1):
        category, created = QualificationCategory.objects.get_or_create(
            name=cat_name,
            defaults={'display_order': order}
        )
        if created:
            cat_count += 1
            print(f"Created category: {cat_name}")
        else:
            category.display_order = order
            category.save()
            
        for item_name in items:
            item, i_created = QualificationItem.objects.get_or_create(
                category=category,
                name=item_name
            )
            if i_created:
                item_count += 1
                print(f"  - Created item: {item_name}")

    print(f"Restoration completed. Categories created: {cat_count}, Items created: {item_count}")

if __name__ == "__main__":
    restore()
