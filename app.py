import streamlit as st
import os
import datetime
from PIL import Image
from google import genai

# ========================================================
# ⚙️ 準備：アプリの基本設定（スマホの見た目にする魔法）
# ========================================================
st.set_page_config(page_title="れいぞうこアイ", page_icon="👁️", layout="centered")

# ========================================================
# 🔑 【最重要】ここにあなたの「APIキー」を貼り付けてください！
# ========================================================
# 例: API_KEY = "AIzaSyAz1234567890..."
API_KEY = "AIzaSyDPtG3mGNGNBAVtMlsOO2TpPnVtV_PaNEg"

# ========================================================
# 🎨 デザイン：アプリの一番上のロゴ部分
# ========================================================
st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 12px; border-bottom: 3px solid #4a90e2; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h1 style="color: #4a90e2; margin: 0; font-size: 24px; font-weight: 800;">👁️ れいぞうこアイ</h1>
        <p style="color: #7f8c8d; margin: 5px 0 0 0; font-size: 11px; font-weight: 600;">● 重なり解析高精度モード稼働中</p>
    </div>
""", unsafe_allow_html=True)

# データの記憶装置（アプリを動かしている間、データを一時保存する場所）
if "ai_result" not in st.session_state:
    st.session_state.ai_result = "まだ冷蔵庫の写真が撮影されていません。右側の「📸 お家でパシャリ」から撮影してください。"
if "custom_dates" not in st.session_state:
    st.session_state.custom_dates = {}

# 📱 主婦のための2画面切り替えタブ
tab1, tab2 = st.tabs(["🛒 お店で確認", "📸 お家でパシャリ"])

# ----------------------------------------------------------------
# 【画面1】🛒 お店で確認（スーパーの売り場で見る画面）
# ----------------------------------------------------------------
with tab1:
    st.markdown("### 📸 最新の冷蔵庫カメラ実況")
    
    # 撮影された最新の画像があれば画面に表示する
    if os.path.exists("latest_fridge.jpg"):
        st.image("latest_fridge.jpg", caption="最後に撮影された冷蔵庫内の様子", use_container_width=True)
        st.success("✓ AIが重なり・隠れを自動判別しました")
    else:
        st.info("💡 まだ冷蔵庫の写真がありません。右側の『お家でパシャリ』から写真を撮影してください。")

    st.markdown("### 📝 AI解析・在庫状況")
    # AIが文章で出力した中身を綺麗に表示
    st.markdown(f'<div style="background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 5px solid #4a90e2; box-shadow: 0 2px 4px rgba(0,0,0,0.02); line-height: 1.6;">{st.session_state.ai_result}</div>', unsafe_allow_html=True)

    # 📅 主婦が自分で消費期限を追加・変更できるコーナー
    st.markdown("### 📅 消費期限の追加・管理")
    col1, col2 = st.columns(2)
    with col1:
        food_input = st.text_input("食材名を入力", placeholder="例：たまご、牛乳", key="food_in")
    with col2:
        date_input = st.date_input("消費期限", datetime.date.today())
    
    if st.button("期限リストに追加・変更する"):
        if food_input:
            st.session_state.custom_dates[food_input] = date_input.strftime('%Y/%m/%d')
            st.toast(f"「{food_input}」の期限を追加しました！")
        else:
            st.warning("食材名を入力してください。")

    # 手動追加された期限リストを表示する場所
    if st.session_state.custom_dates:
        st.markdown("<div style='background-color: #fff; padding: 10px; border-radius: 8px; margin-top: 10px;'>", unsafe_allow_html=True)
        for food, d_val in st.session_state.custom_dates.items():
            st.markdown(f"・ **{food}** : `📅 消費期限: {d_val}`")
        st.markdown("</div>", unsafe_allow_html=True)

    # 🛍️ ご近所スーパーの特売ニュースコーナー
    st.markdown("### 🛍️ まわりのスーパーのお買い得情報")
    st.markdown("""
        <div style="background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 12px; border-left: 5px solid #ff6b6b; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <span style="font-size: 16px;">🥩</span> <b>スーパーたなか（徒歩5分）</b><br>
            <span style="font-size: 13px; color: #2c3e50;">本日夕方市！国産豚細切れ肉が100g/98円の超特価！</span>
        </div>
        <div style="background-color: #ffffff; padding: 12px; border-radius: 12px; border-left: 5px solid #2ecc71; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <span style="font-size: 16px;">🥛</span> <b>毎日マート（駅前店）</b><br>
            <span style="font-size: 13px; color: #2c3e50;">【AI連動】冷蔵庫の牛乳や調味料が減っていませんか？当店本日調味料・乳製品フェア開催中！</span>
        </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# 【画面2】📸 お家でパシャリ（お家で冷蔵庫を撮る画面）
# ----------------------------------------------------------------
with tab2:
    st.markdown("### 冷蔵庫を開けてそのまま撮影")
    
    # スマホのカメラを起動させる特別なボタン
    enable_camera = st.checkbox("スマホのカメラを起動する")
    if enable_camera:
        uploaded_file = st.camera_input("シャッターを押してください")
    else:
        uploaded_file = st.file_uploader("または、スマホで撮った冷蔵庫の写真をアップロード", type=["jpg", "jpeg", "png"])

    # 写真がパシャリと撮られたら、自動的に本物のAI解析がスタート
    if uploaded_file is not None:
        # 撮影された画像をパソコンに一度保存
        img = Image.open(uploaded_file)
        img.save("latest_fridge.jpg")
        
        st.info("🤖 「入り乱れ・重なり」をAIが透過解析中... 奥の隠れた食材をマッピングしています。")
        
        # 本物のGemini AIを呼び出して、主婦目線で解析させる
        try:
            client = genai.Client(api_key=API_KEY)
            
            # AIへの詳しい指示書（プロンプト）
            prompt = """
            あなたは家庭用冷蔵庫の在庫管理に特化した、超高性能な画像認識AIアシスタント『れいぞうこアイ』です。
            
            【目的】
            一般家庭の主婦が買い物の直前に確認し、「重複買い（ダブり）」を完全に防ぐための在庫リストを作成してください。

            【解析の注意点】
            - 食材が入り乱れて重なっていたり、奥に隠れて見えにくくなっている場合も、容器の形状や影、前後の並びから「何がいくつあるか（例：たまごが手前と奥に2パック、など）」を人間の目で見たように見抜いてください。
            - マヨネーズやケチャップ等のチューブ類、ドレッシング等は、ボトルの凹み具合やシワから大体の残量（例：残り15%など）を推測してください。
            - パックの印字や食材の状態から、おおよその「消費期限・賞味期限」も予測、または安全な目安を算出してください。

            【出力フォーマット】
            主婦がパッと見て秒でわかるよう、以下の項目で改行を多く使い、読みやすい日本語で出力してください。マークダウン（**等）を使って重要な食材を強調してください。
            
            🚨【重複注意・残りわずかなもの】（一番注意すべきダブり危険食材や買い足し推奨品）
            🟢【現在あるもの一覧】（商品名、数量、重なりや隠れの状況、推測される消費期限）
            💡【主婦へのワンポイントアドバイス】（例：「奥にある卵パックの方が期限が早そうなので手前に出してください」など）
            """

            # AIに画像と指示書を渡して、考えてもらう
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[img, prompt]
            )
            
            # 解析結果を保存し、画面に反映する
            st.session_state.ai_result = response.text.replace("\n", "<br>")
            st.success("🎉 解析が完了しました！『お店で確認』タブを開いてみてください！")
            st.balloons() # お祝いの風船を飛ばす演出
            
        except Exception as e:
            st.error(f"AI解析中にエラーが発生しました。APIキー（鍵）が正しく入力されているか確認してください: {e}")