# Notion HQ Setup  

## 概要  
このドキュメントでは、Notion HQ 自動更新Botを利用するために必要な設定手順をまとめています。  

## Notion側の設定  
- Notion Integration を作成し、必要な権限を付与する（databases.read, databases.write, data_sources.read, data_sources.write など）  
- HQ を管理するデータベースを作成し、FinalGoal、NearGoal、Progress、NextAction、UpdatedAt、ManualOverride など必要なプロパティを追加する  
- 作成した Integration をデータベースに接続する  
- データベース設定画面の data_sources ペインから data source を作成し、ID を掳える  

## GitHub Secrets  
以下のキー名で Secrets を登録し、値にはそれぞれのトークンやIDを設定します。値は書きません。  
- NOTION_TOKEN  
- NOTION_DATABASE_ID  
- NOTION_DATA_SOURCE_ID  
- NOTION_VERSION  
- OPENAI_API_KEY  
- OPENAI_MODEL  

## 手動実行の手順  
- GitHub リポジトリの Actions タブを開き、「Notion HQ」ワークフローを選択する  
- 「Run workflow」をクリックし、必要に応じてブランチを選択して実行する  

## トラブルシュート  
- 403 エラー: Notion Integration の権限が不足しているか、データベースへの接続が行われていない可能性があります。Integration の権限と接続設定を確認してください。  
- 400 エラー: Database ID または Data Source ID が誤っている可能性があります。ID を再確認し、Secrets の値を見直してください。 
