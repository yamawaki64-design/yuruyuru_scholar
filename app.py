import re
import shutil
from pathlib import Path

import groq
import streamlit as st
import streamlit.components.v1 as components

from styles import apply_styles
from utils import (
    EXT_MAP,
    MAX_FILE_SIZE_MB,
    MAX_UPLOAD_FILES,
    QUERY_EXPAND_THRESHOLD,
    expand_query,
    format_source_item,
    generate_response,
    get_wiki_file_info,
    group_results_by_file,
    init_chromadb,
    load_wiki_to_chromadb,
    search_documents,
    store_chunks,
    extract_text,
    summarize_conversation_sync,
)

# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ゆるゆる司書さん",
    page_icon="🪔",
    layout="centered",
)
apply_styles()

# ── 静的ファイル同期（data/wiki/ の HTML を static/wiki/ にコピー） ────────────
def _sync_wiki_static():
    """data/wiki/ の HTML ファイルを static/wiki/ にコピーして静的配信に対応する"""
    src_dir = Path("data/wiki")
    dst_dir = Path("static/wiki")
    if not src_dir.exists():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in src_dir.iterdir():
        if f.is_file() and f.suffix.lower() in {".html", ".htm"}:
            shutil.copy2(f, dst_dir / f.name)

_sync_wiki_static()

# ── セッション初期化（重いモデルロードはしない） ──────────────────────────────
def _init_session():
    if "wiki_loaded" not in st.session_state:
        st.session_state.chroma_client = None
        st.session_state.collection = None
        st.session_state.wiki_loaded = False
        st.session_state.uploaded_files = []
        st.session_state.chat_history = []
        st.session_state.chat_summary = ""
        st.session_state.last_exchange = None
        st.session_state.hoo_message = (
            "やあやあ、いらっしゃい〜。\n資料を預けてくれたら、なんでも調べてあげるよ〜📚"
        )


_init_session()

groq_client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── タイトルバー ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-bar">
  <span class="title-main">🪔 ゆるゆる司書さん</span>
  <span class="title-sub"> — Scholar's Study</span>
</div>
""", unsafe_allow_html=True)


# ── ホーさんメッセージ表示 ────────────────────────────────────────────────────
def _render_hoo_message(message: str):
    st.markdown(f"""
<div class="hoo-card">
  <div class="hoo-avatar">🦉</div>
  <div class="hoo-body">
    <div class="hoo-name">ホーさん / Scholar Hoo</div>
    <div class="hoo-text">{message}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── reason からキーワードを抽出してハイライト ─────────────────────────────────
def _highlight_text(text: str, phrases: list[str]) -> str:
    """phrases の文字列を text 内でハイライトする。
    改行・連続スペースを単一スペースに正規化してからマッチする。例外時はプレーンテキストを返す。"""
    import html as html_mod
    try:
        if not phrases:
            return html_mod.escape(text)
        mark = '<mark style="background:#c8922a; color:#2c1f0e; padding:1px 3px;">'
        # テキスト・フレーズともに改行と連続空白を単一スペースに正規化
        escaped = re.sub(r'\s+', ' ', html_mod.escape(text)).strip()
        for phrase in sorted(phrases, key=len, reverse=True):
            phrase_norm = re.sub(r'\s+', ' ', html_mod.escape(phrase)).strip()
            if phrase_norm and phrase_norm in escaped:
                escaped = escaped.replace(phrase_norm, f"{mark}{phrase_norm}</mark>")
        return escaped
    except Exception:
        return html_mod.escape(text)


# ── 回答履歴の 1 件を表示 ────────────────────────────────────────────────────
def _render_answer_entry(entry: dict):
    query_text = entry.get("query", "")
    intro = entry.get("intro", "")
    highlight = entry.get("highlight", [])
    sources = entry.get("sources", [])

    st.markdown(f"""
<div class="answer-card">
  <div class="answer-question">Q.  {query_text}</div>
  <div class="answer-intro">💬 {intro}</div>
</div>
""", unsafe_allow_html=True)

    if sources:
        groups = group_results_by_file(sources)
        for src, items in groups.items():
            first = format_source_item(items[0])
            expander_label = f'{first["icon"]} {first["label"]}'
            with st.expander(expander_label, expanded=False):
                for item in items:
                    info = format_source_item(item)
                    detail_html = (
                        f'<div class="source-detail">📎 {info["detail"]}</div>'
                        if info.get("detail") else ""
                    )
                    highlighted = _highlight_text(info["text"], highlight)
                    highlighted = highlighted.replace("\n", "<br>")
                    st.markdown(f"""
<div class="source-quote">
  … {highlighted} …
  {detail_html}
</div>
""", unsafe_allow_html=True)


# ── タブ ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["💬 ホーさんに聞く", "📚 資料室"])

# ════════════════════════════════════════════════════════════════════════════
# タブ1：ホーさんに聞く
# ════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── ローディング（Wiki 読み込み中） ──────────────────────────────────────
    if not st.session_state.wiki_loaded:
        # ① まずホーさんメッセージを表示
        _render_hoo_message("持ってる本を整理してるから、最初だけちょっと待ってねぇ〜🦉")

        # ② ChromaDB + 埋め込みモデル初期化（重い処理、メッセージ表示後に実行）
        if st.session_state.collection is None:
            with st.spinner("司書さんの準備中…"):
                client, collection = init_chromadb()
            st.session_state.chroma_client = client
            st.session_state.collection = collection

        # ③ Wiki ファイル読み込み
        wiki_files = []
        if Path("data/wiki").exists():
            wiki_files = [
                f for f in sorted(Path("data/wiki").iterdir())
                if f.is_file() and not f.name.startswith(".")
                and f.suffix.lower() in EXT_MAP
            ]

        if wiki_files:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def _on_progress(done, total, name):
                progress_bar.progress(done / total)
                status_text.caption(f"「{name}」を読み込んでるよ〜")

            load_wiki_to_chromadb(st.session_state.collection, progress_callback=_on_progress)
            progress_bar.empty()
            status_text.empty()

        st.session_state.wiki_loaded = True
        st.rerun()

    # ── 通常 UI ──────────────────────────────────────────────────────────────
    else:
        # ホーさんメッセージ
        _render_hoo_message(st.session_state.hoo_message)

        # お持ちいただいた資料
        if st.session_state.uploaded_files:
            st.markdown('<div class="section-label">📁 お持ちいただいた資料</div>', unsafe_allow_html=True)
            tags_html = "".join(
                f'<span class="file-tag">📄 {name}</span>'
                for name in st.session_state.uploaded_files
            )
            st.markdown(f'<div style="margin-bottom:8px">{tags_html}</div>', unsafe_allow_html=True)

        # ── ファイルアップロード ──────────────────────────────────────────────
        uploaded = st.file_uploader(
            "PDF / Word / Excel をここに\nクリックして選択してねぇ〜",
            type=["pdf", "docx", "xlsx"],
            accept_multiple_files=True,
            label_visibility="visible",
        )

        if uploaded:
            processed_names = set(st.session_state.uploaded_files)
            new_files = [f for f in uploaded if f.name not in processed_names]
            newly_added = []

            for uf in new_files:
                if len(st.session_state.uploaded_files) >= MAX_UPLOAD_FILES:
                    st.warning("ちょっと多すぎるねぇ〜、5冊まで預かれるよ〜🦉")
                    break

                file_bytes = uf.read()
                uf.seek(0)
                if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
                    st.warning(f"「{uf.name}」はちょっと大きすぎるねぇ〜（{MAX_FILE_SIZE_MB}MBまでだよ）")
                    continue

                ext = Path(uf.name).suffix.lower()
                file_type = EXT_MAP.get(ext)
                if not file_type:
                    continue

                chunks = extract_text(uf, file_type, source_name=uf.name)

                if chunks and chunks[0]["text"] == "__SCAN_PDF__":
                    st.warning(f"「{uf.name}」はテキストが読み取れないよぉ〜。スキャンの資料は苦手なんだぁ🦉")
                    continue

                store_chunks(st.session_state.collection, chunks, source_type="upload")
                st.session_state.uploaded_files.append(uf.name)
                newly_added.append(uf.name)

            if newly_added:
                names = "、".join(newly_added)
                st.session_state.hoo_message = (
                    f"ふむふむ〜、{names}、預かったよ〜📚\nなにか知りたいこと、聞いてみてねぇ"
                )
                st.rerun()

        # ── 質問入力 ─────────────────────────────────────────────────────────
        st.caption("💬 ホーさんに聞く（Enter で送信）")
        with st.form("query_form", clear_on_submit=True, border=False):
            cols = st.columns([9, 1])
            with cols[0]:
                query_input = st.text_input(
                    "",
                    placeholder="なにか知りたいことがあれば…",
                    label_visibility="collapsed",
                )
            with cols[1]:
                submitted = st.form_submit_button("🔍", use_container_width=True)

        # ── リセットボタン ────────────────────────────────────────────────────
        _, col_reset = st.columns([3, 4])
        with col_reset:
            st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
            if st.button("🦉 預かったもの全部返すよ〜", use_container_width=True):
                if st.session_state.uploaded_files:
                    try:
                        st.session_state.collection.delete(where={"source_type": "upload"})
                    except Exception:
                        pass

                st.session_state.chat_history = []
                st.session_state.chat_summary = ""
                st.session_state.last_exchange = None
                st.session_state.uploaded_files = []
                st.session_state.hoo_message = (
                    "やあやあ、いらっしゃい〜。\n資料を預けてくれたら、なんでも調べてあげるよ〜📚"
                )
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── 質問処理 ─────────────────────────────────────────────────────────
        if submitted and query_input.strip():
            query = query_input.strip()
            try:
                # ① クエリ補完（10文字以下のみ）
                expanded_query = query
                if len(query) <= QUERY_EXPAND_THRESHOLD:
                    expanded_query = expand_query(query, groq_client)

                # ② 類似検索（ベクトルスコア上位5件）
                search_results = search_documents(st.session_state.collection, expanded_query)

                # ③ 回答生成
                if search_results is None:
                    intro = "載ってないみたいだねぇ…もしかして別の資料にあるかも？🦉"
                    keywords: list[str] = []
                    st.session_state.hoo_message = "うーんと…ちょっとわからなかったねぇ〜🦉"
                    st.session_state.chat_history.insert(0, {
                        "query": query, "intro": intro, "sources": []
                    })
                else:
                    top3 = search_results[:3]
                    intro, keywords = generate_response(
                        expanded_query, top3, st.session_state.chat_summary, groq_client
                    )
                    st.session_state.last_exchange = {"q": query, "a": intro}
                    st.session_state.hoo_message = "見つかったよぉ〜📚 下に書いておいたねぇ"
                    st.session_state.chat_history.insert(0, {
                        "query": query, "intro": intro,
                        "highlight": keywords, "sources": top3,
                    })

            except groq.RateLimitError as e:
                print(f"[Groq] RateLimitError caught in app: {e}")
                intro = "ごめんね〜、今はバタバタしてるのでもう少し待ってからまた質問してほしいな〜🦉"
                st.session_state.hoo_message = "少し待ってもらったら、またお答えできるよ〜🦉"
                st.session_state.chat_history.insert(0, {
                    "query": query, "intro": intro, "sources": []
                })

        # ── 回答履歴 ─────────────────────────────────────────────────────────
        for entry in st.session_state.chat_history:
            _render_answer_entry(entry)

# ════════════════════════════════════════════════════════════════════════════
# タブ2：資料室
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    _render_hoo_message(
        "ここにある資料は、ぜんぶ読んであるよ〜。質問タブで聞いてみてねぇ📚"
    )

    files_info = get_wiki_file_info()

    if not files_info:
        st.markdown(
            '<div style="color:#5a4830;font-size:0.85rem;margin-top:12px;">'
            'えーと…まだ資料がないねぇ〜。data/wiki/ にファイルを入れてねぇ🦉'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        html_files = [f for f in files_info if f["file_type"] == "html"]
        other_files = [f for f in files_info if f["file_type"] != "html"]

        # セクション1：Wiki（HTML）
        if html_files:
            st.markdown(
                '<div class="room-section-header">🌐 ゆるゆるシリーズ Wiki</div>',
                unsafe_allow_html=True,
            )
            for f in html_files:
                title = f.get("title", f["name"])
                with st.expander(f"🌐  {title}　　HTML"):
                    static_path = Path("static/wiki") / f["name"]
                    if static_path.exists():
                        html_content = static_path.read_text(encoding="utf-8")
                        components.html(html_content, height=600, scrolling=True)
                    else:
                        st.caption("ファイルが見つからないよぉ〜🦉")

        # セクション2：資料ファイル（PDF・DOCX・XLSX）
        if other_files:
            st.markdown(
                '<div class="room-section-header">📄 資料ファイル</div>',
                unsafe_allow_html=True,
            )
            dl_icon_map = {"pdf": "📄", "docx": "📝", "xlsx": "📊"}
            mime_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
            for f in other_files:
                ft = f["file_type"]
                icon = dl_icon_map.get(ft, "📎")
                pages = f.get("pages")
                badge_extra = f" · {pages}p" if pages else ""
                col_title, col_btn = st.columns([7, 2])
                with col_title:
                    st.markdown(
                        f'<div class="wiki-file-row" style="border-right:none;border-radius:8px 0 0 8px;">'
                        f'<div class="wiki-file-title">{icon} {f["name"]}</div>'
                        f'<div class="wiki-file-badge">{ft.upper()}{badge_extra}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    file_path = Path(f["path"])
                    if file_path.exists():
                        st.download_button(
                            label=f"{icon} ダウンロード",
                            data=file_path.read_bytes(),
                            file_name=f["name"],
                            mime=mime_map.get(ft, "application/octet-stream"),
                            use_container_width=True,
                        )
