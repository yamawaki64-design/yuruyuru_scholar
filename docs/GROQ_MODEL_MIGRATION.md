# Groqモデル移行時の注意事項

Groqのモデルを変更する際は以下を確認すること。ゆるゆるシリーズ共通。

---

## 推論モデル（reasoning model）固有の挙動

`openai/gpt-oss-*` などの推論モデルは、通常モデルと **レスポンス構造が異なる**。

| 項目 | 通常モデル（llama等） | 推論モデル（gpt-oss等） |
|---|---|---|
| 思考プロセス | なし | `message.reasoning` フィールドに出力 |
| 最終回答 | `message.content` | `message.content`（同じ） |
| トークン消費 | `max_tokens` = 回答分のみ | `max_tokens` = 推論＋回答の合計 |

---

## max_tokens の設定（重要）

推論モデルは `max_tokens` を推論と回答の両方で消費する。
**小さい値（200 等）では推論だけでトークンを使い切り、`content` が空になる。**

```python
# NG: 推論モデルでは推論だけで消費してしまい content が空になる
max_tokens=200

# OK: 推論 + 回答分を確保する
max_tokens=1024
```

---

## 症状と診断方法

`content` が空のまま返ってきてフォールバック文言しか出ない場合は以下をログで確認する。

```python
choice = resp.choices[0]
print(f"finish_reason: {choice.finish_reason!r}")
print(f"message fields: {vars(choice.message)}")
print(f"raw content: {choice.message.content!r}")
```

| ログの内容 | 原因 | 対処 |
|---|---|---|
| `finish_reason: 'length'` かつ `content: ''` | max_tokens 不足 | max_tokens を増やす（1024以上） |
| `reasoning` フィールドに思考が入っている | 推論モデル確認 | max_tokens を増やす |
| `finish_reason: 'content_filter'` | コンテンツフィルタ | プロンプトを見直す |

---

## レスポンスのクリーニング

モデルによって JSON 以外のテキストが混入する場合がある。以下の除去処理を入れておくこと。

```python
# thinkingブロック除去
cleaned = re.sub(r"<think(?:ing)?>.*?</think(?:ing)?>", "", raw, flags=re.DOTALL)
# バッククォートブロック・jsonプレフィックス除去
cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
cleaned = cleaned.replace("```", "").strip()
# JSONを抽出
m = re.search(r"\{.*\}", cleaned, re.DOTALL)
```
