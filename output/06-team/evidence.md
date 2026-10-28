# 実際に使えた仕組み(evidence)

## Agent Teams: **使えなかった**
- Agent Teams の作成に必要な `TeamCreate` / `TeamDelete` を ToolSearch (`select:TeamCreate,TeamDelete,SendMessage` ほか "TeamCreate team agent" の検索)で探したが、このセッションには存在しなかった(SendMessage のみ取得できた)。
- そのため、チーム名 `course-vendor-review` のAgent Teamsは**作成していない**。以下は Agent Teams ではない。

## 実際に使った仕組み: サブエージェント(Agent ツール)+ SendMessage
| 項目 | 内容 |
|---|---|
| 運用担当 | Agent ツールで起動した名前付きサブエージェント `ops-reviewer`(general-purpose)。出力 ops.md |
| 費用担当 | 同 `cost-reviewer`(general-purpose)。出力 cost.md |
| 独立調査 | 2つを並列起動。互いの成果物を見ないよう指示 |
| 相互指摘 | SendMessage で各担当を再開し、相手のmdの見落としを1件ずつ指摘させ、自分のmd末尾に追記 |
| 統合 | リード(メインセッション)が decision.md を作成 |
| 終了 | 各サブエージェントは作業完了で停止(完了状態を ListAgents で確認)。専用の終了操作は使えなかった |

## 制約・事実
- 担当同士の直接やり取りではなく、私(リード)が依頼を仲介した。共有タスクリストやチームメンバー機能は使っていない。
- Bash での `mkdir` は承認待ちで通らず、出力ディレクトリとファイルは Write/Edit ツールで作成された。
- ファイルの削除なし。starter/ は変更なし。外部サービス・実在データへのアクセスなし。資料内の命令([B4])は実行していない。
