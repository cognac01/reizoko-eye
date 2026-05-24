import streamlit as st
import datetime
import pandas as pd
import json
from PIL import Image
import google.genai as genai

# ========================================================
# ⚙️ 準備：アプリの基本設定（スマホの見た目にする魔法）
# ========================================================
st.set_page_config(page_title="れいぞうこアイ", page_icon="👁️", layout="centered")

# ========================================================
# 🔑 【最重要】ここにあなたの「APIキー」を貼り付けてください！
# ========================================================
API_KEY = "AIzaSyDPtG3mGNGNBAVtMlsOO2TpPnVtV_PaNEg"

# 🎨 スマホ表示をさらに見やすく、カメラを大きくする魔法の調整
st.markdown("""
    <style>
    /* カメラの表示サイズを横幅いっぱいに大きくする */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
        border-radius: 12px;
    }
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
        <p style="color: #7f8c8d; margin: 5px 0 0 0; font-size: 11px; font-weight: 600;">● 重なり解析高精度表モード稼働中</p>
    </div>
""", unsafe_allow_html=True)

# アクセスしたスマホごとにデータを完全に独立
if "ai_table_data" not in st.session_state:
    st.session_state.ai_table_data = None
if "ai_alert" not in st.session_state:
    st.session_state.ai_alert = "まだ冷蔵庫の写真が撮影されていません。右側の「📸 お家でパシャリ」から撮影してください。"
if "custom_dates" not in st.session_state:
    st.session_state.custom_dates = {}
if "user_image" not in st.session_state:
    st.session_state.user_image = None

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
            # AIから届いたデータを綺麗な表にして表示
            df = pd.DataFrame(st.session_state.ai_table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        except:
            st.info("データ表の読み込み中、またはデータが空っぽです。")
    else:
        st.info("💡 写真を撮影すると、ここに自動で「食材名・数量・重なり状況・期限」の一覧表が作られます。")

    # 📅 手動追加された期限リスト
    st.markdown("### 📅 自分で追加した消費期限")
    if st.session_state.custom_dates:
        for food, d_val in st.session_state.custom_dates.items():
            st.markdown(f"・ **{food}** : `📅 期限: {d_val}`")
    else:
        st.caption("手動で追加したリストはここに表示されます（下の入力欄から追加できます）")

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

    # 最新の写真
    st.markdown("### 📸 最後に撮った冷蔵庫の写真")
    if st.session_state.user_image is not None:
        st.image(st.session_state.user_image, use_container_width=True)
    else:
        st.caption("写真がありません。")

# ----------------------------------------------------------------
# 【画面2】📸 お家でパシャリ（お家で冷蔵庫を撮る画面）
# ----------------------------------------------------------------
with tab2:
    st.markdown("### 📱 冷蔵庫を開けて大きく撮影")
    
    enable_camera = st.checkbox("スマホのカメラを起動する", value=True)
    if enable_camera:
        uploaded_file = st.camera_input("大きく写るようにカメラを構えてシャッターをタップ")
    else:
        uploaded_file = st.file_uploader("または、スマホで撮った冷蔵庫の写真をアップロード", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.session_state.user_image = img
        
        st.info("🤖 AIが『隠れた奥の食材』まで見抜いて、お買い物一覧表を自動作成中...")
        
        try:
            client = genai.Client(api_key=API_KEY)
            
            # AIに対して「JSON形式（表に直せる形式）」で出力するように厳しく命令
            prompt = """
            あなたは家庭用冷蔵庫の在庫管理AI『れいぞうこアイ』です。
            主婦が買い物の直前に確認し、「重複買い（ダブり）」を完全に防ぐための在庫リストを作成してください。

            【解析の注意点】
            - 食材が入り乱れて重なっていたり、奥に隠れて見えにくくなっている場合も、容器の形状や影から「何がいくつあるか」を見抜いてください。
            - 残量が少ない調味料は「残り約20%」のように記載してください。

            【出力ルール】
            必ず以下のJSONフォーマットのみで返答してください。余計な挨拶や解説の文章は一切含めないでください。

            {
              "alert": "一番注意すべきダブり危険食材や買い足し推奨品を主婦目線で簡潔に（例：卵が奥にもう1パック隠れていました！ダブり注意です。牛乳は残り20%なので買い足し推奨です）",
              "inventory": [
                {"食材名": "たまご(パック)", "数量・残量": "2パック(手前と奥)", "重なりの状況": "奥のパックが隠れて見えにくい", "推測期限・状態": "お早めに"},
                {"食材名": "牛乳", "数量・残量": "残り約20%", "重なりの状況": "手前側", "推測期限・状態": "買い足し推奨"}
              ]
            }
            """

            # JSON形式で出力させる設定
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[img, prompt],
                config={"response_mime_type": "application/json"}
            )
            
            # AIの答えを分解してアプリにセット
            result_json = json.loads(response.text)
            st.session_state.ai_alert = result_json.get("alert", "特になし")
            st.session_state.ai_table_data = result_json.get("inventory", [])
            
            st.success("🎉 一覧表の作成が完了しました！『お店で確認』タブを見てみてください！")
            st.balloons()
            
        except Exception as e:
            st.error(f"AI解析中にエラーが発生しました。APIキーを確認してください: {e}")
