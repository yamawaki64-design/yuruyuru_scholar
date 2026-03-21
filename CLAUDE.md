# ゆるゆる司書さん CLAUDE.md

## 必ず最初に読むこと
- シリーズ共通ルール → `docs/YURUYURU_BASE.md` を参照してから実装を開始すること
- UIデザイン → `docs/ui_prototype.png`（スクショ）を参照。デザイン・配色・雰囲気はこれに従うこと

---

## アプリ概要

| 項目 | 内容 |
|---|---|
| アプリ名 | ゆるゆる司書さん |
| キャラ | ホーさん🦉（フクロウの司書） |
| 口調 | 「〜だねぇ」「あったあった〜」「えーとえーと」系。ゆったりのんびり |
| デプロイ先 | Streamlit Community Cloud |

---

## ファイル構成

```
yuruyuru-shisho/
├── app.py             # メインアプリ（UIとセッション管理のみ）
├── utils.py           # 処理メソッド（テキスト抽出・RAG・Groq呼び出し）
├── styles.py          # CSSカスタムスタイル定義
├── data/
│   └── wiki/          # 内部Wikiデータ（起動時に自動読み込み）
│       ├── キャラ紹介.html
│       ├── アプリ一覧.html
│       ├── 司書さん使い方.html
│       ├── 司書さんQA集.pdf
│       └── 開発ノート.docx
├── requirements.txt
├── .streamlit/
│   └── secrets.toml   # GROQ_API_KEY = "xxx"
└── README.md
```

---

## 画面構成

### タブ構成（st.tabs）
- タブ1：💬 ホーさんに聞く
- タブ2：📚 資料室

### 起動時ローディング挙動（重要）

アプリ起動時は `data/wiki/` の全ファイルをChromaDBに登録する処理が走る。
この間はUIを段階的に表示し、登録完了まで検索・アップロードを受け付けない。

```
【ローディング中の表示】
  ホーさんメッセージエリアのみ表示
  　↓
  ホーさん：「持ってる本を整理してるから、最初だけちょっと待ってねぇ〜🦉」
  　+ st.spinner または st.progress でファイル登録の進捗を表示

  ※ ファイルアップロードゾーン・質問入力・リセットボタンは非表示
  ※ タブ切り替え（資料室）は操作可能のまま（DBと無関係のため）

【登録完了後】
  ホーさんメッセージが通常の挨拶に切り替わる
  　↓
  ファイルアップロードゾーン・質問入力・リセットボタンが表示される
```

実装パターン：
```python
if not st.session_state.get("wiki_loaded", False):
    # ローディング中：メッセージエリアのみ表示
    show_hoo_loading_message()
    load_wiki_to_chromadb()  # ここで全ファイル登録
    st.session_state.wiki_loaded = True
    st.rerun()
else:
    # 登録完了：通常UI表示
    show_full_ui()
```

### タブ1「ホーさんに聞く」の構成（上から順に）
1. ホーさんメッセージエリア（常時表示）
2. お持ちいただいた資料（アップロード済みの場合のみ表示）
3. ファイルアップロードゾーン（PDF/Word/Excel）
4. 質問入力（1行テキスト、Enterで送信）
5. リセットボタン（「預かったもの全部返すよ〜」）
6. 回答履歴（新しい回答が上に積み上がる）

### タブ2「資料室」の構成
- ホーさんメッセージ（固定）
- 内部Wikiファイル一覧（ページタイトル＋リンクまたはファイル情報）
  - セクション1：🌐 ゆるゆるシリーズ Wiki（HTMLファイル）
  - セクション2：📄 資料ファイル（PDF・DOCX）

---

## 技術スタック

| 役割 | ライブラリ | 備考 |
|---|---|---|
| UI | Streamlit | Community Cloudにデプロイ |
| PDF読み込み | PyMuPDF (fitz) | ページ番号取得 |
| Word読み込み | python-docx | 段落単位 |
| Excel読み込み | openpyxl | シート名＋行範囲でチャンク化 |
| HTML読み込み | BeautifulSoup4 | h1/h2タグをメタデータに含める |
| チャンク化 | LangChain | RecursiveCharacterTextSplitter |
| ベクトルDB | ChromaDB | インメモリ（セッション保持） |
| 埋め込み | sentence-transformers | paraphrase-multilingual-MiniLM-L12-v2 |
| LLM（回答生成） | Groq API | llama-3.3-70b-versatile |
| LLM（クエリ補完） | Groq API | llama-3.1-8b-instant（TPD上限が大きいため） |

---

## RAGフロー

### 起動時（内部Wiki自動読み込み）
```
アプリ起動
  ↓
data/wiki/ 内の全ファイルを extract_text() で読み込む
  ↓
ChromaDB（コレクション名: "shisho_docs"）に保存
  ↓
st.session_state に保持
```

### ユーザーアップロード時
```
ファイルアップロード
  ↓
extract_text(file, file_type) で分岐処理
  ↓
同名ファイルの重複チェック → 重複はスキップ
  ↓
同じChromaDBコレクションに追加（source_type="upload"）
  ↓
ホーさん：「ふむふむ、預かったよ〜」
```

### 質問〜回答フロー
```
質問入力（Enter送信）
  ↓
expand_query()  ← 10文字以下の短い質問のみ llama-3.1-8b-instant で補完
  ↓
ChromaDB で類似検索（上位8件取得・ベクトルスコア順）
  ↓
【重複排除】同一ファイル＋同一スコアの重複をスキップ
  ↓
類似度スコア判定（SIMILARITY_THRESHOLD = 0.8）
  ├── 全件が閾値以上 → 固定文言「載ってないみたいだねぇ…」
  └── 閾値未満あり → 上位3件を generate_response() に渡す
  ↓
回答表示（Groqのintro + Python製の出典表示）
  ↓
summarize_conversation() で会話要約を更新
```

**ポイント**: ChromaDBから8件取得するが、Groqへ渡すのは上位3件のみ（トークン節約）。
出典表示も同じ上位3件を使う。

---

## Groqの役割（2つ）

### 1. generate_response() — まとめ＋キーワード生成
- 上位3チャンクを渡し、ホーさん口調の導入コメント＋ハイライト用キーワードを生成
- JSON形式で返させてパースする
- キーワードはチャンク内に実際に存在する単語のみ（最大5個）
- 出典テキスト表示はPythonが行うため、Groqには概要コメントのみ依頼する

```python
# 返却JSON形式
{
  "intro": "ホーさんのコメント（80字以内、ゆったり口調）",
  "keywords": ["ハイライト用キーワード", "最大5個", "チャンク内に存在する単語のみ"]
}
# 戻り値: (intro: str, keywords: list[str])
```

### 2. expand_query() — 質問の意図補完（条件付き）
- 10文字以下の短い質問のみ実行（llama-3.1-8b-instant 使用）
- 「コックさんは？」→「ゆるゆるコックさんについて教えてください」に補完

### （参考）summarize_conversation_sync() — 会話要約
- 回答後に呼び出し
- 過去の要約＋直前のQ&Aを渡し、1〜2文の要約を更新
- 次回の質問時に st.session_state.chat_summary として渡す

---

## エラーハンドリング

### Groq RateLimitError（日次トークン上限超過）
- 回答履歴に「ごめんね〜、今はバタバタしてるのでもう少し待ってからまた質問してほしいな〜🦉」を表示（出典なし）
- ホーさんメッセージを「少し待ってもらったら、またお答えできるよ〜🦉」に更新
- `except groq.RateLimitError` で専用ハンドリング

---

## 出典表示の仕様

### ファイル種別アイコン
| 種別 | アイコン | 出典情報 |
|---|---|---|
| HTML（Wiki） | 🌐 | ページタイトル |
| PDF | 📄 | ファイル名 ＋ Nページ目 |
| Word | 📝 | ファイル名 ＋ Nページ目 |
| Excel | 📊 | ファイル名 ＋ シート名 ／ N〜M行目 |

### グルーピング・表示ルール
- 上位3件をファイル名単位でグルーピング（`group_results_by_file()`）
- ベクトルスコア順（距離が近い＝類似度が高い順）を維持
- ファイルごとに `st.expander`（デフォルト閉じ）で表示
- 引用テキストは `… テキスト …` 形式（カギかっこではなく三点リーダー）
- generate_response が返した keywords でテキスト内をハイライト表示

---

## ファイル読み込み仕様

### extract_text(file, file_type) の分岐

```python
# file_typeで分岐（将来のURL対応を見越した構造にすること）
# v1対応: "pdf" / "docx" / "xlsx" / "html"
# v2予定: "url"（今は実装しない。関数の口だけ開けておく）
def extract_text(file, file_type):
    if file_type == "pdf":   ...
    elif file_type == "docx": ...
    elif file_type == "xlsx": ...
    elif file_type == "html": ...
    # elif file_type == "url": pass  # v2で実装
```

### HTMLの読み込み
- BeautifulSoup4 でテキスト抽出
- h1/h2 タグの内容をメタデータの "heading" に保存
- 500文字以下のページは分割しない（丸ごと1チャンク）

#### テキスト抽出前に除外する要素（RAG精度向上のため）

ゆるゆるシリーズのWiki HTMLには装飾用テキストが含まれており、
そのままChromaDBに入れると検索ノイズになる。
抽出前に以下の要素を `tag.decompose()` で除去すること。

```python
# 除外するCSSクラス（装飾・ナビゲーション系）
HTML_NOISE_CLASSES = [
    "ornamental-border",   # — ✦ ——— ✦ — などの飾り罫
    "title-divider",       # タイトル下の区切り線
    "chapter-label",       # "Catalogue of Works" などの英語ラベル
    "page-footer",         # "p.3 / Yuruyuru Series — Scholar's Study / 2026"
    "section-divider",     # · · · などの区切り
    "footer-series-name",  # フッターのシリーズ名
    "page-number",         # フッターのページ番号
    "app-url-link",        # "▶ デモを開く" リンク
    "tech-badge",          # 技術スタックバッジ（Streamlit, Groq等）
    "chara-badge",         # "主役" "宛先" などのバッジ
]

# 除外するHTMLタグ
HTML_NOISE_TAGS = [
    "style",   # CSSスタイル定義
    "script",  # JavaScript
    "head",    # メタ情報
]
```

#### 除去後の仕上げ
- 連続する空白行・空白文字を正規化する（`re.sub(r'\n{3,}', '\n\n', text)`）
- 抽出テキストが100文字未満の場合はスキップ（装飾のみのページ対策）

### Excelの読み込み
- シートごとに処理
- ヘッダー行を検出し「シート名 ＋ ヘッダー ＋ データ行」をテキスト化
- 10行ごとにチャンク化
- メタデータに sheet（シート名）と rows（例："1-10"）を保存
- グラフ・図は対象外（テキストセルのみ）

### スキャンPDFの対応
- テキスト抽出量が極端に少ない場合（100文字未満）はスキャンPDFと判定
- ホーさん：「テキストが読み取れないよぉ〜。スキャンの資料は苦手なんだぁ」と案内

---

## チャンク設定（LangChain）

```python
RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "、", ""]
)
```

---

## セッション管理

```python
# st.session_state に保持するもの
st.session_state.session_id         # セッション固有ID（uuid）
st.session_state.wiki_collection    # WikiコレクションへのRef（プロセス共有）
st.session_state.upload_client      # アップロード用ChromaDBクライアント（セッション固有）
st.session_state.upload_collection  # アップロード用コレクション（セッション固有）
st.session_state.wiki_loaded        # Wiki読み込み完了フラグ（起動時ローディング制御）
st.session_state.uploaded_files     # アップロード済みファイル名リスト
st.session_state.chat_history       # 回答履歴（表示用）
st.session_state.chat_summary       # 会話要約（Groqに渡す用）
st.session_state.last_exchange      # 直前のQ&A（{"q": ..., "a": ...}）
```

## ChromaDB コレクション構成（重要：セッション分離）

**背景**: Streamlit Community Cloud では複数セッションが同一Pythonプロセスを共有する。
`chromadb.Client()` はプロセスレベルのインメモリDBを使うため、単一コレクション名だと
**別セッションがアップロードしたファイルが他のセッションの検索結果に混入する**。
これを防ぐためにコレクションを2種類に分けている。

| コレクション名 | スコープ | 内容 |
|---|---|---|
| `shisho_wiki` | プロセス共有（1つのみ） | Wiki読み込みデータ。2セッション目以降はスキップ |
| `shisho_upload_{session_id}` | セッション固有 | そのセッションのアップロードファイルのみ |

- `shisho_wiki` はプロセス内で1回だけ作成・ロード（`get_wiki_collection()` + スレッドロック）
- Wikiロードは `count() > 0` で判定してスキップ（2セッション目以降は即完了）
- 検索は両コレクションを個別にクエリ → マージ → distance 昇順ソート → 上位8件
- **コレクション名を単一に戻してはいけない**（セッション間汚染が再発する）

---

## ファイルアップロード制限

- ファイル数：最大5件まで（超過時はホーさんが案内）
- 1ファイルのサイズ：最大10MB
- 超過時メッセージ：「ちょっと多すぎるねぇ〜、5冊まで預かれるよ〜」

---

## 定数定義（utils.py に定義すること）

```python
SIMILARITY_THRESHOLD = 0.8        # これ以上なら「見つからない」判定
MAX_SEARCH_RESULTS = 8            # ChromaDB から取得する上位件数
MAX_UPLOAD_FILES = 5              # アップロード上限
MAX_FILE_SIZE_MB = 10             # ファイルサイズ上限
QUERY_EXPAND_THRESHOLD = 10       # 文字数がこれ以下なら expand_query() 実行
HISTORY_TURNS = 1                 # Groqに渡す直前ターン数
GROQ_MODEL = "llama-3.3-70b-versatile"       # 回答生成（品質重視）
GROQ_MODEL_LIGHT = "llama-3.1-8b-instant"   # クエリ補完（TPD 1,000,000/day）
```

**廃止した定数**（削除済み）:
- `MAX_CHUNKS_PER_FILE`（ファイル別チャンク上限）
- `MAX_FILES_IN_RESULT`（出典ファイル数上限）

---

## 注意事項

- ChromaDB はインメモリで使用（永続化しない）
- サーバー再起動でセッションが消えるのは許容仕様
- v2予定のURLスクレイピングは今は実装しない。extract_text()にコメントだけ残す
- Groqへの指示はシンプルに保つ（複数の制約を同時に与えない）
- Groqに出典表示を任せない（Pythonで確実に表示する）
- Groq TPD上限（llama-3.3-70b-versatile: 100,000トークン/日）に注意。
  generate_response に渡すチャンクは上位3件に絞ること
- ChromaDB のコレクション設計は「ChromaDB コレクション構成」セクションを必ず参照すること。
  単一コレクションに戻すとセッション間でアップロードデータが混入する
