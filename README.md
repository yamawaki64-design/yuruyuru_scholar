# 🦉 ゆるゆる司書さん

> PDFやWordやExcelをアップロードするだけで、ホーさんが内容を読んで質問に答えてくれるRAGアシスタント。

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://yuruyuru-scholar.streamlit.app/)

![スクリーンショット](docs/screenshot.jpg)

---

## 📋 アプリ概要

「資料の中に答えがあるはずなんだけど、どこに書いてあるかわからない」をAIで解決するツールです。

PDF・Word・Excelをアップロードするだけで、フクロウの司書・ホーさん🦉が内容を読んでベクトル検索。関連する箇所を見つけて、出典付きで回答してくれます。ゆるゆるシリーズの内部Wikiは起動時から自動で読み込まれているので、アップロードなしでもすぐに質問できます。

**🔗 デモ：https://yuruyuru-scholar.streamlit.app/ **

---

## ✨ 主な機能

| 機能 | 説明 |
|------|------|
| 📚 内部Wiki自動読み込み | 起動時にゆるゆるシリーズのWikiを自動でChromaDBに登録 |
| 📄 ファイルアップロード | PDF・Word（.docx）・Excel（.xlsx）に対応。最大5ファイル・1ファイル10MBまで |
| 🔍 ベクトル検索 | 意味的に近い箇所を検索（キーワード完全一致ではなく意味で探す） |
| 💬 RAG回答 | 検索結果をGroq AIに渡してホーさん口調の回答を生成 |
| 🗂️ 出典表示 | ファイル名・ページ番号・行番号など出典をアコーディオン表示 |
| 🖊️ キーワードハイライト | 回答に関連するキーワードを出典テキスト内でハイライト |
| 🔄 リセット機能 | アップロードファイルと会話履歴を一括リセット（内部Wikiは保持） |

---

## 🖥️ 画面構成

```
【起動時】
ホーさん：「持ってる本を整理してるから、最初だけちょっと待ってねぇ〜🦉」
　+ 内部WikiをChromaDBに登録中（プログレス表示）
　↓
【タブ1：ホーさんに聞く】
ファイルアップロードゾーン（PDF / Word / Excel）
質問入力（Enterで送信）
　↓
ホーさんのコメント ＋ 出典アコーディオン（ファイル名・ページ・引用テキスト）
　↓
【タブ2：資料室】
ゆるゆるシリーズ内部Wiki一覧（HTML閲覧）
PDF・Wordファイルのダウンロードリンク
```

---

## 🛠️ 技術スタック

| 要素 | 内容 |
|------|------|
| フレームワーク | [Streamlit](https://streamlit.io/) |
| AI（回答生成） | [Groq API](https://groq.com/)（llama-3.3-70b-versatile） |
| AI（クエリ補完） | [Groq API](https://groq.com/)（llama-3.1-8b-instant） |
| ベクトルDB | [ChromaDB](https://www.trychroma.com/)（インメモリ） |
| 埋め込みモデル | sentence-transformers（paraphrase-multilingual-MiniLM-L12-v2） |
| PDF読み込み | PyMuPDF（fitz） |
| Word読み込み | python-docx |
| Excel読み込み | openpyxl |
| HTML読み込み | BeautifulSoup4 |
| テキスト分割 | LangChain RecursiveCharacterTextSplitter |
| 言語 | Python 3.11 |
| デプロイ | Streamlit Community Cloud |

---

## 💡 工夫したポイント

### RAGの精度チューニング
- **チャンク設計**：`chunk_size=500 / overlap=50` に落ち着くまで、タグ単位分割・セマンティックチャンキングを試して廃止。重要キーワードを含むチャンクの親情報が失われる問題を避けるため固定サイズに戻した
- **HTMLノイズ除去**：装飾用CSSクラス（飾り罫・バッジ・フッターなど）を`decompose()`で除去してから埋め込み。検索ノイズを減らしてRAG精度を改善
- **リランキング廃止**：llama-3.1-8b-instantによるリランキングは精度が低く、Groq TPD上限（100,000トークン/日）にも頻繁に到達したため廃止。ベクトル検索上位3件をそのままLLMに渡す方式に変更

### Groq呼び出し設計
- 1回の質問でのGroq呼び出しは最大2回に制限（TPD上限対策）
  - `expand_query()`：10文字以下の短い質問のみ、軽量モデル（8b-instant）で補完
  - `generate_response()`：上位3チャンクを渡してホーさん口調のコメント＋ハイライト用キーワードをJSON形式で生成
- LLMに出典表示を任せず、Pythonで確実に生成（出典の正確性を担保）

### ファイル種別ごとの読み込み設計
- **PDF**：PyMuPDFでページ番号をメタデータに保存。テキスト量が少ない場合（100文字未満）はスキャンPDFと判定してホーさんが案内
- **Word**：Headingスタイルの見出しを親セクション情報としてメタデータに格納
- **Excel**：シート名を親セクション、10行ごとにチャンク化して行範囲をメタデータに格納

### セッション管理
- ChromaDBはインメモリ使用。アップロードファイルは同名重複チェックで二重登録を防止
- 起動時Wikiローディング中はUI入力を非表示にして不完全な状態での検索を防止

---

## 📁 ファイル構成

```
yuruyuru_scholar/
│
├── app.py                    # メインアプリ（UIとセッション管理）
├── utils.py                  # 処理メソッド（テキスト抽出・RAG・Groq呼び出し）
├── styles.py                 # CSSカスタムスタイル定義
├── data/
│   └── wiki/                 # 内部Wiki（起動時に自動読み込み）
│       ├── キャラ紹介.html
│       ├── アプリ一覧.html
│       ├── 司書さん使い方.html
│       └── ゆるゆるシリーズQA.html
├── static/
│   └── wiki/                 # Streamlit静的配信用（data/wikiと同内容）
├── docs/
│   └── screenshot.jpg
├── .streamlit/
│   ├── config.toml           # enableStaticServing = true
│   └── secrets.toml          # GROQ_API_KEY（GitHubには上げない）
└── requirements.txt
```

---

## 🚀 ローカルで動かす

```bash
# 1. リポジトリをクローン
git clone https://github.com/yamawaki64-design/yuruyuru_scholar.git
cd yuruyuru_scholar

# 2. 依存パッケージをインストール
pip install -r requirements.txt

# 3. APIキーを設定
#    .streamlit/secrets.toml を作成して以下を記載
#    GROQ_API_KEY = "your_groq_api_key"

# 4. 起動
streamlit run app.py
```

> **Groq API キーの取得**：https://console.groq.com/ から無料で取得できます。

> **初回起動時**：sentence-transformersのモデルダウンロードが走るため、数分かかる場合があります。

---

## 🔮 今後の検討事項

- [ ] `summarize_conversation()` の復活（会話コンテキストをGroqに渡して精度向上）
- [ ] URLスクレイピング対応（v2予定。`extract_text()`の口だけ開けてある）
- [ ] ハイライト精度の改善（質問文キーワードをフォールバックとして使う方式の検討）

---

## 👤 作者

RAGアシスタントの設計（チャンク戦略・ノイズ除去・Groq TPD管理）をポートフォリオとして開発しました。

<!-- TODO: 名前・SNSリンク・Zenn記事URLなどを追記してください -->
<!-- - Zenn: https://zenn.dev/yourname -->
<!-- - Twitter/X: @yourhandle -->
