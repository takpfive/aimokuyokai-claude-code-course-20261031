# セットアップ

確認日：2026-10-29。画面と提供機能は変更されます。

## Desktopで始める

1. https://claude.com/download から公式アプリを入れる。
2. Claude Codeを利用できるアカウントでログインする。公式案内ではPro/Max/Team/Enterpriseが対象。組織の許可も確認する。
3. Codeタブ → 新規セッション → 自分のコンピューター → 展開した教材フォルダーを選ぶ。
4. `CLAUDE.md`と`starter/`が見えることを確認する。
5. 手動の許可モードで、実行対象・保存先を確認して進める。

今回の画面はMacです。Windowsでも教材のCSV/Markdown/HTMLは共通です。ホームフォルダー全体を作業場所にせず、教材だけを選びます。

## Skill

プロジェクトの`.claude/skills/course-daily-report/SKILL.md`を同梱しています。`/course-daily-report`を送信すると日報を作ります。候補に出ない場合は教材ルートを選び直した新規セッションで確認してください。スケジュール実行機能ではありません。

## 外部連携

Desktopの＋メニューやコネクタ一覧からGmail・Google Calendar・Drive・Notionなどの対象を確認します。接続ごとに機能と権限が異なります。組織管理者の許可や本人の認証が必要な場合は本人が行います。

接続がなければ、演習03のCSVを使って日報の抽出・分類を練習できます。MCP接続成功と外部書き込み成功は別の確認です。

## CLIとAgent Teams（上級の補足）

CLIのインストール手順は https://code.claude.com/docs/en/quickstart を確認してください。講座の基本操作はDesktopで進められます。

Mac/Linuxの例：

```sh
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
```

Windows PowerShellの例：

```powershell
$env:CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1"
claude
```

設定後にチーム作成・共有タスク・メンバーの実行状態まで確かめます。環境変数を設定しただけで成功とはしません。今回のCLI 2.1.308ではTeamCreate/TeamDeleteが提供されず、Agent Teamsは未実演でした。代わりにAgentツールで2担当を起動し、SendMessageで相互レビューを行いました。

権限確認を無効化するオプションは使いません。並列実行は利用量が増えるため、小さく独立した仕事から試します。
