import streamlit as st


def apply_styles():
    """ゆるゆる司書さん のカスタム CSS を適用する"""

    # ── Streamlit 標準 UI の非表示（YURUYURU_BASE 共通ルール） ──────────────
    st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

    # ── カスタムスタイル ───────────────────────────────────────────────────
    st.markdown("""
<style>
/* ── ページ全体 ── */
.stApp {
    background-color: #0d0a06;
}

/* ── メインコンテナの上部余白を除去（タイトルバーを最上部に密着） ── */
[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
}

/* ── タイトルバー ── */
.title-bar {
    text-align: center;
    padding: 10px 0 8px;
    border-bottom: 1px solid #3d2e18;
    margin-bottom: 4px;
    letter-spacing: 0.05em;
}
.title-main {
    font-size: 1.15rem;
    color: #d4a843;
    font-weight: 600;
}
.title-sub {
    font-size: 0.78rem;
    color: #7a6040;
    margin-left: 6px;
}

/* ── タブ ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #3d2e18;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #7a6040;
    border-radius: 6px 6px 0 0;
    padding: 6px 16px;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background-color: #1a1208 !important;
    color: #d4a843 !important;
    border-bottom: 2px solid #d4a843;
}
.stTabs [data-baseweb="tab-panel"] {
    background-color: transparent;
    padding-top: 12px;
}

/* ── ホーさんメッセージカード ── */
.hoo-card {
    background-color: #1a1208;
    border: 1px solid #3d2e18;
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 12px;
}
.hoo-avatar {
    font-size: 2.2rem;
    line-height: 1;
    flex-shrink: 0;
}
.hoo-body {}
.hoo-name {
    font-size: 0.72rem;
    color: #7a6040;
    margin-bottom: 4px;
    letter-spacing: 0.04em;
}
.hoo-text {
    font-size: 0.95rem;
    color: #c8a87a;
    line-height: 1.6;
    white-space: pre-line;
}

/* ── お持ちいただいた資料ラベル ── */
.section-label {
    font-size: 0.78rem;
    color: #7a6040;
    margin: 8px 0 6px;
    letter-spacing: 0.04em;
}

/* ── ファイルタグ ── */
.file-tag {
    display: inline-block;
    background-color: #1e1608;
    border: 1px solid #4a3820;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.8rem;
    color: #c8a87a;
    margin: 2px 4px 2px 0;
}

/* ── アップロードゾーン ── */
[data-testid="stFileUploader"] {
    background-color: #1a1208;
    border: 1.5px dashed #4a3820 !important;
    border-radius: 8px;
    padding: 4px 8px;
}
[data-testid="stFileUploader"] label {
    color: #7a6040 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #7a6040;
}

/* ── テキスト入力 ── */
[data-testid="stTextInput"] > div > div > input {
    background-color: #1a1208;
    border: 1px solid #4a3820;
    border-radius: 8px;
    color: #c8a87a;
    font-size: 0.92rem;
    padding: 8px 12px;
}
[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #d4a843;
    box-shadow: 0 0 0 1px #d4a84340;
}
[data-testid="stTextInput"] > div > div > input::placeholder {
    color: #5a4830;
}

/* ── フォームのボーダー非表示 ── */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}

/* ── ボタン全般 ── */
.stButton > button {
    background-color: #1a1208;
    border: 1px solid #4a3820;
    border-radius: 8px;
    color: #c8a87a;
    font-size: 0.85rem;
    padding: 6px 14px;
    transition: background-color 0.15s, border-color 0.15s;
}
.stButton > button:hover {
    background-color: #251a0c;
    border-color: #d4a843;
    color: #d4a843;
}

/* ── 送信ボタン（検索アイコン） ── */
[data-testid="stFormSubmitButton"] button {
    background-color: #2a1e0c;
    border: 1px solid #6b4f2a;
    color: #d4a843;
    border-radius: 8px;
    font-size: 1rem;
    padding: 6px 10px;
    width: 100%;
}
[data-testid="stFormSubmitButton"] button:hover {
    background-color: #3a2a10;
    border-color: #d4a843;
}

/* ── リセットボタン ── */
.reset-btn > button {
    background-color: transparent;
    border: 1px solid #4a3820;
    border-radius: 20px;
    color: #7a6040;
    font-size: 0.8rem;
    padding: 4px 14px;
}
.reset-btn > button:hover {
    border-color: #c8783c;
    color: #c8783c;
}

/* ── 回答履歴カード ── */
.answer-card {
    background-color: #141008;
    border: 1px solid #3d2e18;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.answer-question {
    font-size: 0.8rem;
    color: #7a6040;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
}
.answer-reason {
    font-size: 0.85rem;
    color: #a08060;
    margin-bottom: 6px;
    font-style: italic;
}
.answer-intro {
    font-size: 0.95rem;
    color: #c8a87a;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── 出典チップ ── */
.source-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background-color: #1e1608;
    border: 1px solid #4a3820;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.8rem;
    color: #c8a87a;
    margin-bottom: 6px;
    cursor: default;
}

/* ── 出典テキスト引用 ── */
.source-quote {
    background-color: #1a1208;
    border-left: 2px solid #4a3820;
    border-radius: 0 4px 4px 0;
    padding: 7px 12px;
    font-size: 0.82rem;
    color: #9a8060;
    margin: 4px 0 8px 2px;
    line-height: 1.55;
}
.source-detail {
    font-size: 0.73rem;
    color: #5a4830;
    margin-top: 3px;
}

/* ── 資料室 セクションヘッダー ── */
.room-section-header {
    font-size: 0.78rem;
    color: #7a6040;
    letter-spacing: 0.06em;
    margin: 14px 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── 資料室 ファイル行 ── */
.wiki-file-row {
    background-color: #1a1208;
    border: 1px solid #3d2e18;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.wiki-file-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: #c8a87a;
}
.wiki-file-badge {
    font-size: 0.72rem;
    color: #7a6040;
    background-color: #251a0c;
    border-radius: 4px;
    padding: 2px 7px;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── 資料室 HTML リンクバッジ ── */
a.wiki-file-badge {
    text-decoration: none;
    cursor: pointer;
    color: #7a6040;
}
a.wiki-file-badge:hover {
    border-color: #d4a843 !important;
    color: #d4a843 !important;
}

/* ── スピナー ── */
.stSpinner > div {
    color: #d4a843 !important;
}

/* ── プログレスバー ── */
.stProgress > div > div > div {
    background-color: #d4a843;
}

/* ── ステータステキスト ── */
.stText, .stCaption {
    color: #7a6040;
}

/* ── スクロールバー ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0a06; }
::-webkit-scrollbar-thumb { background: #3d2e18; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)
