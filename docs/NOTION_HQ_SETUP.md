## 概要  
このドキュメントでは、Notion HQ 自動更新Botを利用するために必要な設定手順をまとめています。  

## Notion側の設定  
- Notion Integration を作成し、必要な権限を付与する（databases.read, databases.write, data_sources.read, data_sources.write など）  
- HQ を管理するデータベースを作成し、FinalGoal, NearGoal, Progress, NextAction, UpdatedAt, ManualOverride, LastRunStatus, LastRunAt, LastRunError など必要なプロパティを追加する  
- 作成した Integration をデータベースに接続する  
- データベース設定画面の data_sources ペインから data source を作成し、ID を掴える  

## GitHub Secrets  
以下のキー名で Secrets を登録し、値にはそれぞれのトークンや ID を設定する（値は書きません）。  
- NOTION_TOKEN  
- NOTION_DATABASE_ID  
- NOTION_DATA_SOURCE_ID  
- NOTION_VERSION  
- OPENAI_API_KEY  
- OPENAI_MODEL  
- SLACK_WEBHOOK_URL  

## 手動実行の手順  
- GitHub リポジトリの Actions タブを開き、「Notion HQ Auto Update」ワークフローを選択する  
- 「Run workflow」をクリックし、必要に応じてブランチを選択して実行する  

## 新機能と運用  
- NextAction の出力は具体的なタスク形式に固定されています。run.py は「今日やること」「成果物」「完了条件」「所要：X 分」のフォーマットで NextAction を生成します。  
- HQ データベースに LastRunStatus（Select：SUCCE FAIL）、LastRunAt（Date）、LastRunError（Text）プロパティを追加すると、実行結果のログが保存されます。プロパティが存在しない場合は更新をスキップします。  
- ワークフロー成功時には Slack に NextAction の概要と Notion ページのリンクを通知します。失敗時には実行 URL とエラー要約を Slack に送信します。Slack 通知のために `SLACK_WEBHOOK_URL` を GitHub Secrets に追加してください。  

## 失敗時の見方  
- GitHub Actions のログでエラー詳細を確認します。  
- Notion 側では LastRunError プロパティに 200 文字以内のエラー要約が保存されます。  
- Slack 通知には Workflow Run URL が含まれるので、リンク先から詳細ログを確認できます。  

## トラブルシュート  
- 403 エラー: Notion Integration の権限が不足しているか、データベースへの接続が行われていない可能性があります。Integration の権限と接続状態を確認してください。  
- 401 エラー: Database ID または Data Source ID が誤っている可能性があります。ID を再確認し、Secrets の値を見直してください。 
