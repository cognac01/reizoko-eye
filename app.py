import streamlit as st
import datetime
import pandas as pd
import json
from PIL import Image
import google.genai as genai

# ========================================================
# ⚙️ 準備：アプリの基本設定（Nano-Banana ダークテーマ）
# ========================================================
st.set_page_config(page_title="れいぞうこアイ", layout="centered")

# ========================================================
# 🔑 安全な金庫（Secrets）からAPIキーを自動で読み込む仕組み
# ========================================================
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
elif "api_key" in st.secrets:
    API_KEY = st.secrets["api_key"]
else:
    API_KEY = ""

# 🎨 Nano-Banana 専用スタイル：黒背景、黄所のアクセント、見やすいデジタルグリッド
st.markdown("""
    <style>
    /* 全体の背景を高級感のある黒に */
    .stApp { background-color: #0f1115; color: #ffffff; }
    
    /* 文字の色調整：見出しを鮮やかなバナナイエローに */
    h1, h2, h3 { color: #FFE135 !important; font-weight: 800 !important; }
    p, span, label { color: #e5e7eb !important; }
    
    /* タブのデザインをイエローのアクティブバーに */
    div[data-testid="stTabs"] button { font-size: 18px !important; font-weight: bold; color: #9ca3af !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #FFE135 !important; border-bottom-color: #FFE135 !important; }
    
    /* データ表（グリッド）をダークモードに調和させて丸角に */
    .stDataFrame { border-radius: 12px; overflow: hidden; background-color: #1a1d23; border: 1px solid #2d3139; }
    
    /* 折りたたみボックス（Expander）のデザイン */
    div[data-testid="stExpander"] { background-color: #1a1d23; border: 1px solid #2d3139; border-radius: 12px; }
    
    /* 注意アラート（ダークモードに馴染む落ち着いた赤） */
    .alert-box { background-color: #2c1a1a; padding: 15px; border-radius: 12px; border-left: 5px solid #ff6b6b; color: #ff8c8c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 🎨 ロゴ部分（Nano-Bananaのシャープな枠線デザイン）
st.markdown("""
    <div style="background-color: #1a1d23; padding: 20px; border-radius: 16px; border-left: 8px solid #FFE135; margin-bottom: 25px; box-shadow: 0 10px 15px rgba(0,0,0,0.3);">
        <h1 style="color: #FFE135; margin: 0; font-size: 28px; font-weight: 800;">れいぞうこアイ</h1>
        <p style="color: #9ca3af; margin: 5px 0 0 0; font-size: 12px; font-weight: 600;">Nano-Banana | 高精度画像解析・在庫システム</p>
    </div>
""", unsafe_allow_html=True)

# アクセスしたスマホごとにデータを完全に独立
if "ai_table_data" not in st.session_state:
    st.session_state.ai_table_data = None
if "ai_alert" not in st.session_state:
    st.session_state.ai_alert = "まだ写真が送信されていません。右側の「📸 お家でパシャリ」から写真を送ってください。"
if "custom_dates" not in st.session_state:
    st.session_state.custom_dates = {}
if "user_images" not in st.session_state:
    st.session_state.user_images = []

# 📱 2画面切り替えタブ
tab1, tab2 = st.tabs(["🛒 在庫を確認", "📸 写真をスキャン"])

# ----------------------------------------------------------------
# 【画面1】🛒 在庫を確認（売り場や手元でパッと見る画面）
# ----------------------------------------------------------------
with tab1:
    # 🛍️ 最優先：AIが弾き出した「重複・残りわずか」のアラート
    st.markdown("### 🚨 AIアラート：重複注意・残りわずか")
    st.markdown(f'<div class="alert-box">{st.session_state.ai_alert}</div>', unsafe_allow_html=True)

    # 📊 メイン：AIが自動作成した「現在あるもの一覧（表形式）」
    st.markdown("### 🟢 現在あるもの一覧（AI解析）")
    if st.session_state.ai_table_data is not None:
        try:
            # AIから届いたデータを綺麗な表（グリッド）にして画面最上部に表示
            df = pd.DataFrame(st.session_state.ai_table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        except:
            st.info("データ表の読み込み中、またはデータが空っぽです。")
    else:
        st.info("💡 写真を送信すると、AIがスキャンして、ここに「品名・数量・保存場所・状態」の綺麗な一覧表を自動生成します。")

    # 📅 手動追加された期限リスト
    st.markdown("### 📅 自分で追加した消費期限")
    if st.session_state.custom_dates:
        for food, d_val in st.session_state.custom_dates.items():
            st.markdown(f"・ **{food}** : `📅 期限: {d_val}`")
    else:
        st.caption("手動で追加したリストはここに表示されます")

    # 手動の入力フォーム
    with st.expander("➕ 手動で期限リストを追加・変更する"):
        col1, col2 = st.columns(2)
        with col1:
            food_input = st.text_input("食材名を入力", placeholder="例：たまご、牛乳")
        with col2:
            date_input = st.date_input("消費期限", datetime.date.today())
        if st.button("リストに追加"):
            if food_input:
                st.session_state.custom_dates[food_input] = date_input.strftime('%Y/%m/%d')
                st.toast(f"「{food_input}」を追加しました！")
                st.rerun()

    # 送信された元の写真は、確認の邪魔にならないよう一番下に配置
    if st.session_state.user_images:
        st.markdown("---")
        st.markdown("### 📸 スキャンに使用した元の写真")
        cols = st.columns(len(st.session_state.user_images))
        for idx, img in enumerate(st.session_state.user_images):
            with cols[idx]:
                st.image(img, caption=f"{idx+1}枚目のアングル", use_container_width=True)

# ----------------------------------------------------------------
# 【画面2】📸 写真をスキャン（高画質でまとめて送る画面）
# ----------------------------------------------------------------
with tab2:
    st.markdown("### 📱 高画質でまとめて送る（最大5枚）")
    st.info("💡 スマホのいつもの高性能カメラアプリで、全体や各段、ドアポケットなどを綺麗に撮影し、以下からまとめて選択してください。")
    
    # 複数ファイル一括アップローダー
    uploaded_files = st.file_uploader(
        "解析する写真をまとめて選択（複数OK）", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    # 写真が選択され、かつAPIキーが存在する場合に解析スタート
    if uploaded_files:
        if not API_KEY:
            st.error("🔑 APIキーが設定されていません。StreamlitのSecrets設定を行ってください。")
        else:
            # 選択された画像をすべてリストに読み込む（最大5枚）
            loaded_images = []
            for f in uploaded_files[:5]:
                loaded_images.append(Image.open(f))
            
            # セッションに記憶
            st.session_state.user_images = loaded_images
            
            st.info(f"🤖 AIが {len(loaded_images)} 枚の写真を同時に精密スキャン中... 重複を排除して一覧表を組み立てています。")
            
            try:
                client = genai.Client(api_key=API_KEY)
                
                # 画像を表（JSON構造）に変形させるためのプロンプト
                prompt = """
                あなたは高性能な在庫管理AI『れいぞうこアイ』です。
                ユーザーから送られた複数枚の写真をすべて同時に、詳しく解析してください。
                何の商品が、どこに、どのくらいあるのかを完全にリスト化し、重複買いを防ぐための統合在庫リストを1つ作成してください。

                【解析の注意点】
                - 写真が複数に分かれているので、同じ食材が別々のアングルに写っている場合は、重複して数えずに同一のものとして正しくカウントしてください。
                - 食材が入り乱れて重なっていたり、奥に隠れて見えにくくなっている場合も、形状や影から何があるかを見抜いてください。
                - 残量が少ない調味料は「残り約20%」のように記載してください。

                【出力ルール】
                必ず以下のJSONフォーマットのみで返答してください。余計な挨拶や解説の文章は一切含めないでください。

                {
                  "alert": "一番注意すべきダブり危険食材や買い足し推奨品を簡潔に（例：野菜室の奥にキャベツが半分眠っていました！ダブり注意です。卵は残り3個なので買い足し推奨です）",
                  "inventory": [
                    {"品名": "たまご(パック)", "数量": "2パック", "保存場所": "1段目の奥と手前", "ステータス": "奥に隠れて見えにくい"},
                    {"品名": "牛乳", "数量": "残り約20%", "保存場所": "ドアポケット", "ステータス": "買い足し推奨"}
                  ]
                }
                """

                # AIに画像と指示書を渡して解析
                content_inputs = loaded_images + [prompt]

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=content_inputs,
                    config={"response_mime_type": "application/json"}
                )
                
                # AIの解答（JSON）を読み込んでグリッドにセット
                result_json = json.loads(response.text)
                st.session_state.ai_alert = result_json.get("alert", "特になし")
                st.session_state.ai_table_data = result_json.get("inventory", [])
                
                st.success("🎉 スキャンと一覧表の作成が完了しました！『在庫を確認』タブを開いてください！")
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"AI解析中にエラーが発生しました。鍵の設定を確認してください: {e}")
