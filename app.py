import streamlit as st
import datetime
import pandas as pd
import json
from PIL import Image
import google.genai as genai

# ========================================================
# ⚙️ 準備：アプリの基本設定
# ========================================================
st.set_page_config(page_title="れいぞうこアイ", page_icon="👁️", layout="centered")

# ========================================================
# 🔑 安全な金庫（Secrets）からAPIキーを自動で読み込む仕組み
# ========================================================
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
elif "api_key" in st.secrets:
    API_KEY = st.secrets["api_key"]
else:
    API_KEY = ""

# 🎨 デザインの調整（タブの文字を大きく、スマホ最適化）
st.markdown("""
    <style>
    div[data-testid="stTabs"] button {
        font-size: 16px !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 🎨 ロゴ部分
st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 12px; border-bottom: 3px solid #4a90e2; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h1 style="color: #4a90e2; margin: 0; font-size: 24px; font-weight: 800;">👁️ れいぞうこアイ</h1>
        <p style="color: #7f8c8d; margin: 5px 0 0 0; font-size: 11px; font-weight: 600;">● 複数写真・高画質解析モード稼働中</p>
    </div>
""", unsafe_allow_html=True)

# アクセスしたスマホごとにデータを完全に独立
if "ai_table_data" not in st.session_state:
    st.session_state.ai_table_data = None
if "ai_alert" not in st.session_state:
    st.session_state.ai_alert = "まだ冷蔵庫の写真が送信されていません。右側の「📸 お家でパシャリ」から写真を送ってください。"
if "custom_dates" not in st.session_state:
    st.session_state.custom_dates = {}
if "user_images" not in st.session_state:
    st.session_state.user_images = []

# 📱 2画面切り替えタブ
tab1, tab2 = st.tabs(["🛒 お店で確認", "📸 お家でパシャリ"])

# ----------------------------------------------------------------
# 【画面1】🛒 お店で確認（スーパーの売り場で見る画面）
# ----------------------------------------------------------------
with tab1:
    # 🛍️ 最優先：買い足しアラート
    st.markdown("### 🚨 重複注意・残りわずか")
    st.markdown(f'<div style="background-color: #fff0f0; padding: 15px; border-radius: 12px; border-left: 5px solid #ff6b6b; color: #c0392b; font-weight: bold; line-height: 1.6;">{st.session_state.ai_alert}</div>', unsafe_allow_html=True)

    # 📊 メイン：AIが自動作成した在庫一覧表
    st.markdown("### 🟢 現在あるもの一覧（AI解析）")
    if st.session_state.ai_table_data is not None:
        try:
            df = pd.DataFrame(st.session_state.ai_table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        except:
            st.info("データ表の読み込み中、またはデータが空っぽです。")
    else:
        st.info("💡 写真を送信すると、複数枚の写真をAIが同時に分析し、ここにドッキングした一覧表を作ります。")

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

    # 送信された写真のプレビュー
    if st.session_state.user_images:
        st.markdown("### 📸 解析した写真")
        cols = st.columns(len(st.session_state.user_images))
        for idx, img in enumerate(st.session_state.user_images):
            with cols[idx]:
                st.image(img, caption=f"{idx+1}枚目", use_container_width=True)

# ----------------------------------------------------------------
# 【画面2】📸 お家でパシャリ（お家で冷蔵庫を撮る画面）
# ----------------------------------------------------------------
with tab2:
    st.markdown("### 📱 高画質でまとめて送る")
    st.info("💡 スマホのいつものカメラアプリで、冷蔵庫の「棚」「ドアポケット」「野菜室」などを綺麗に撮影し、以下からまとめて選んでください（最大5枚）。")
    
    # 複数ファイルアップローダー（スマホのフォトライブラリから複数選択可能）
    uploaded_files = st.file_uploader(
        "冷蔵庫の写真をまとめて選択（複数OK）", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    # 写真が選択され、かつAPIキーが存在する場合に解析スタート
    if uploaded_files:
        if not API_KEY:
            st.error("🔑 APIキーが設定されていません。StreamlitのSecrets設定を行ってください。")
        else:
            # 選択された画像をすべてリストに読み込む
            loaded_images = []
            for f in uploaded_files[:5]: # 最大5枚まで
                loaded_images.append(Image.open(f))
            
            # 最後に撮影された画像として記憶
            st.session_state.user_images = loaded_images
            
            st.info(f"🤖 AIが {len(loaded_images)} 枚の「高画質写真」を同時にスキャン中... すべての情報を1つに統合しています。")
            
            try:
                client = genai.Client(api_key=API_KEY)
                
                # 複数枚の写真を前提とした指示書にパワーアップ
                prompt = """
                あなたは家庭用冷蔵庫の在庫管理AI『れいぞうこアイ』です。
                ユーザーから送られた【複数枚の冷蔵庫内の写真】（棚、ドアポケット、野菜室などがバラバラに写っています）をすべて同時に、詳しく解析してください。
                主婦が買い物の直前に確認し、「重複買い（ダブり）」を完全に防ぐための統合在庫リストを1つ作成してください。

                【解析の注意点】
                - 写真が複数に分かれているので、同じ食材（例：牛乳が1枚目にも2枚目にも写っているなど）がある場合は、重複して数えずに同一のものとして正しくカウント、または残量を合算してください。
                - 食材が入り乱れて重なっていたり、奥に隠れて見えにくくなっている場合も、形状や影から「何がいくつあるか」を見抜いてください。
                - 残量が少ない調味料は「残り約20%」のように記載してください。

                【出力ルール】
                必ず以下のJSONフォーマットのみで返答してください。余計な挨拶や解説の文章は一切含めないでください。

                {
                  "alert": "一番注意すべきダブり危険食材や買い足し推奨品を主婦目線で簡潔に（例：野菜室の奥にキャベツが半分眠っていました！ダブり注意です。卵はドアポケットに4個だけなので買い足し推奨です）",
                  "inventory": [
                    {"食材名": "たまご(個数)", "数量・残量": "4個", "重なりの状況": "ドアポケット", "推測期限・状態": "お早めに"},
                    {"食材名": "キャベツ", "数量・残量": "半玉", "重なりの状況": "野菜室の奥に隠れ気味", "推測期限・状態": "新鮮なうちに使用"}
                  ]
                }
                """

                # AIに「画像リスト」と「指示書」をまとめて渡す
                content_inputs = loaded_images + [prompt]

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=content_inputs,
                    config={"response_mime_type": "application/json"}
                )
                
                result_json = json.loads(response.text)
                st.session_state.ai_alert = result_json.get("alert", "特になし")
                st.session_state.ai_table_data = result_json.get("inventory", [])
                
                st.success("🎉 全写真の統合・在庫表作成が完了しました！『お店で確認』タブを見てみてください！")
                st.balloons()
                
            except Exception as e:
                st.error(f"AI解析中にエラーが発生しました。鍵の設定を確認してください: {e}")
