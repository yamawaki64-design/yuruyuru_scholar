# ゆるゆるシリーズ 共通実装ルール（YURUYURU_BASE.md）

このファイルはゆるゆるシリーズ全アプリで共通のルールをまとめたものです。
各アプリの CLAUDE.md の冒頭で「このファイルを参照すること」と明記してください。

---

## Streamlit UI 共通設定

### メニュー・タイトルバーの非表示
アプリ起動時に以下のCSSを必ず適用すること。

```python
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
```

### タイトルバーは上部固定で小さく表示
- `st.markdown` でカスタムHTMLタイトルバーを実装する
- フォントサイズは小さめ（スマホで半分がタイトルで埋まらないよう）
- 背景色・デザインは各アプリのテーマに合わせる

### サイドバーのデフォルトメニューを非表示
```python
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)
```

### ページ構成
- ページは1つ（マルチページ構成にしない）
- タブ切り替えが必要な場合は `st.tabs()` を使用する

### スマホ対応方針
- 横スクロールが発生しないレイアウトにすること
- 横並びブロックが縦に崩れるのは許容
- `use_container_width=True` を基本とする
- ボタンは常時表示（hover時のみ表示は不可）
- iPhone Safari（Streamlit Community Cloud）での動作確認を想定

---

## ファイル構成

```
app_name/
├── app.py          # メインアプリ（UIとセッション管理のみ）
├── utils.py        # 処理メソッド（API呼び出し・データ処理など）
├── styles.py       # CSSカスタムスタイル定義
├── requirements.txt
├── .streamlit/
│   └── secrets.toml  # APIキーはここに記載
└── README.md
```

- `app.py` にロジックを書かない。処理は `utils.py` に分離する
- スタイル定義は `styles.py` にまとめる
- ページ数が増える場合も `app.py` を1ファイルに保つ（st.tabsで対応）

---

## Groq API

### シークレットの記載方法
```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_xxxxxxxxxxxx"
```

### コード内での参照方法
```python
import groq
client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])
```

### 使用モデル
```python
GROQ_MODEL = "llama-3.3-70b-versatile"
```

### Groqへの指示方針（重要）
- **複数の制約を同時に与えない**（口調・文字数・出典・判定を全部頼むと抜け落ちる）
- **出典表示はGroqに任せない**（Pythonで確実に表示する）
- **JSON形式で返させる**（パースして確実に使う）
- Groqが担当するのは「まとめ・要約・補完」など、多少ブレても致命的でない部分のみ

```python
# JSON形式で返させる例
prompt = """
以下を読んで、JSONのみで返してください（前置き・マークダウン不要）。
{"intro": "50字以内のコメント"}
"""
```

### レート制限対策
- 1回の質問でのGroq呼び出しは最大2回まで
- 会話要約などの非優先処理は非同期または次回呼び出し時に実行

---

## ChromaDB（RAGアプリ共通）

### インメモリで使用
```python
import chromadb
client = chromadb.Client()  # インメモリ（永続化しない）
```

- Streamlit Community Cloudの制約上、永続化しない
- サーバー再起動でセッションが消えるのは許容仕様
- `st.session_state` にクライアントとコレクションを保持する

### セッション初期化パターン
```python
if "chroma_client" not in st.session_state:
    st.session_state.chroma_client = chromadb.Client()
    st.session_state.collection = st.session_state.chroma_client.create_collection("app_docs")
```

### 埋め込みモデル
```python
# sentence-transformers（多言語対応）
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
```

---

## デプロイ（Streamlit Community Cloud）

- `requirements.txt` に全依存ライブラリを記載する
- `secrets.toml` は `.gitignore` に追加し、GitHubにpushしない
- Community CloudのSecretsにAPIキーを設定する
- ChromaDBはインメモリ運用（上記参照）

---

## キャラクター設計方針

- キャラ口調はシステムプロンプトに「few-shot例」を含めると安定する
- Groqに口調の完全な維持を期待しない（多少崩れても許容する設計にする）
- ユーザー向けの固定メッセージ（エラー・状態通知）はPythonで出力する

---

## 過去のゆるゆるシリーズ参考アプリ

| アプリ名 | URL | 参考ポイント |
|---|---|---|
| ゆるゆる報告書 | https://yuruyuru-report.streamlit.app/ | Streamlit Community Cloudデプロイ構成 |
| ゆるゆるコックさん | （Community Cloud） | ChromaDB・RAG構成・sentence-transformers |
| ゆるゆる道案内 | （Community Cloud） | 複数API統合・Claude Code実装フロー |

---

_ゆるゆるシリーズ共通ルール / 2026年3月_
