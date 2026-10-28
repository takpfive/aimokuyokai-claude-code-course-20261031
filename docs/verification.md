# 実演と検証の記録

確認日：2026-10-29 / Mac、Claude Desktop Code、Claude Code CLI 2.1.308、Google Chrome。

## 実際に行ったこと

| 内容 | 実行方法 | 確認結果 |
|---|---|---|
| 教材フォルダーを選ぶ | Claude DesktopをComputer Useで操作 | 専用のmaterialsフォルダーで開始 |
| 整理案→コピー | Desktopへプロンプト入力、1回ずつ操作許可 | 原本6件保持、コピー6件、対応表あり。全SHA-256一致 |
| 問い合わせアプリ生成 | DesktopでBRIEF.mdからHTMLを生成 | 初期8件、未対応5・対応中2・完了1、期限超過R03のみ |
| ブラウザ操作 | ChromeをComputer Useで操作 | 「そら」検索でR01の1件、R03を完了→再読込後も完了、件数4/2/2・超過0、教材リセット後5/2/1・超過1 |
| 日報Skill | Desktopで`/course-daily-report`を送信 | 日報生成、E01〜E09を参照。予定・未送信・本番未確認を区別 |
| Gmail連携 | Claude Codeから既存MCPで1回検索 | 検索成功、教材語句に一致0件 |
| Google Calendar連携 | Claude Codeから既存MCPで1回検索 | 検索成功、教材語句に一致0件 |
| 三点照合 | Claude Code CLIでPython生成・実行 | 請求7行中6行が要確認。独立したverify.pyでも確認 |
| メール分析 | Claude Code CLIでPython生成・実行 | A/B生クリック9/4、人間ユニーク2/3、直接申込2/2、未帰属2。独立再計算と一致 |
| 並列レビュー | CLIのAgentで2担当を並列起動 | 運用・費用の独立調査、SendMessageで相互指摘、メインが統合 |

## 未実施・限定した範囲

- DriveとNotion：このClaude Codeセッションにコネクタがなく、検索・書き込みは未実施。認証や権限追加も行っていない。接続手順は公式資料に基づく説明。
- Agent Teams：環境変数を有効にしたCLIで専用ツールを探したが、TeamCreate/TeamDeleteが提供されなかった。チームは作成していない。実演したのは名前付きサブエージェント。
- ブラウザ検証：検索・保存・リセットの主導線をChromeで操作。状態/優先度フィルタ全組合せ、CSV特殊文字の往復、モバイル幅、Safari/Firefoxは未実施。詳細は`output/app/verification.md`。そのファイルはClaude自身の初期確認時点の記録で、講座側が後から行った操作確認は本書を参照。
- `verify.py`は今回の固定教材の確認。日報やレビューの意味が正しいかは本文を目視確認した。将来のあらゆるデータに対する保証ではない。
- 実在の顧客データ・私的な会話ログ・社内資料をGitHubに入れていない。外部送信・支払・契約・本番公開の演習はしていない。

## 画面の読み方

Claudeの許可画面・入力欄・コネクタ欄と、生成アプリを操作した画面は実際のスクリーンショットを切り出したものです。保存確認のスライドは同じ画面の件数と行を2か所切り出しています。

CSV・日報・CLIレビュー結果は、読みやすくするため`review/`の閲覧ページに実出力の抜粋を表示して収録しています。Claude CodeのUIを再現したものではありません。原本CSV/Markdownも同梱しています。

## 再確認

```sh
python3 output/04-match/match.py
python3 output/05-campaign/campaign.py
python3 verify.py
```

スライドはMicrosoft PowerPointでPDFを書き出し、全ページを画像にして目視確認。機械チェックはFAIL 0。本文は編集可能で、画面の切り出しは画像です。
