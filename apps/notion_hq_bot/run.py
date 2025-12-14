import os
import datetime
import requests
from openai import OpenAI



def extract_text(prop):
    """Extract plain text from a Notion property."""
    if not prop:
        return ''
    # handle rich_text property
    if isinstance(prop, dict):
        if 'rich_text' in prop:
            return ''.join(part.get('plain_text', '') for part in prop['rich_text'])
        if 'title' in prop:
            return ''.join(part.get('plain_text', '') for part in prop['title'])
        if 'checkbox' in prop:
            return prop.get('checkbox', False)
    return str(prop)



def main():
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    data_source_id = os.getenv('NOTION_DATA_SOURCE_ID')
    notion_version = os.getenv('NOTION_VERSION', '2025-09-03')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    if not notion_token or not database_id or not openai_api_key:
        raise ValueError('Missing required environment variables.')

    client = OpenAI(api_key=openai_api_key)

    # Determine data source ID if not provided
    if not data_source_id:
        db_url = f'https://api.notion.com/v1/databases/{database_id}'
        db_headers = {
            'Authorization': f'Bearer {notion_token}',
            'Notion-Version': notion_version,
        }
        db_resp = requests.get(db_url, headers=db_headers)
        db_resp.raise_for_status()
        db_data = db_resp.json()
        data_sources = db_data.get('data_sources', [])
        if not data_sources:
            raise RuntimeError('No data sources found in database.')
        first_ds = data_sources[0]
        if isinstance(first_ds, dict):
            data_source_id = first_ds.get('id')
        else:
            data_source_id = first_ds

    # Query the data source for HQ entry
    query_url = f'https://api.notion.com/v1/data_sources/{data_source_id}/query'
    query_headers = {
        'Authorization': f'Bearer {notion_token}',
        'Notion-Version': notion_version,
        'Content-Type': 'application/json',
    }
    # Filter by Name == HQ
    filter_payload = {
        'filter': {
            'property': 'Name',
            'operator': 'equals',
            'value': 'HQ'
        }
    }
    query_resp = requests.post(query_url, headers=query_headers, json=filter_payload)
    if query_resp.status_code == 400:
        # Fallback to first entry if filter unsupported
        query_resp = requests.post(query_url, headers=query_headers, json={})
    query_resp.raise_for_status()
    query_data = query_resp.json()
    results = query_data.get('results', [])
    if not results:
        print('No results found in data source.')
        return
    entry = results[0]
    page_id = entry.get('id') or entry.get('page_id')
    properties = entry.get('properties', {})

    # Check manual override
    manual_override = False
    if 'ManualOverride' in properties:
        manual_override = extract_text(properties['ManualOverride'])
    if manual_override:
        print('Manual override enabled; skipping update.')
        return

    final_goal = extract_text(properties.get('FinalGoal'))
    near_goal = extract_text(properties.get('NearGoal'))
    progress = extract_text(properties.get('Progress'))

    status = 'SUCCESS'
    error_summary = ''
    next_action_text = ''

    # Build prompt for OpenAI
    prompt = (
        'あなたは目標達成をサポートするアシスタントです。'
        '次のアクションは1つだけ、30〜60分で終わる具体的なタスクにしてください。'
        '成果物（例：Notionに〇〇を記入、Issueを1つ作る、PRを1つ出す 等）を含み、完了条件を1行で記入してください。'
        '以下の形式で日本語で出力してください：\n'
        '今日やること：…\n'
        '成果物：…\n'
        '完了条件：…\n'
        '所要：…分\n'
        f'FinalGoal: {final_goal}\n'
        f'NearGoal: {near_goal}\n'
        f'Progress: {progress}'
    )

    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        ai_message = response.choices[0].message.content.strip()
        next_action_text = ai_message
    except Exception as exc:
        status = 'FAIL'
        error_summary = str(exc)[:200]

    updated_at = datetime.datetime.utcnow().isoformat()

    # Build properties for Notion update
    update_props = {}

    if status == 'SUCCESS' and next_action_text:
        update_props['NextAction'] = {
            'rich_text': [
                {
                    'text': {
                        'content': next_action_text
                    }
                }
            ]
        }
        update_props['UpdatedAt'] = {
            'date': {
                'start': updated_at
            }
        }

    # Always log run status if corresponding properties exist
    if 'LastRunStatus' in properties:
        update_props['LastRunStatus'] = {
            'select': {
                'name': status
            }
        }
    if 'LastRunAt' in properties:
        update_props['LastRunAt'] = {
            'date': {
                'start': updated_at
            }
        }
    if 'LastRunError' in properties:
        update_props['LastRunError'] = {
            'rich_text': [
                {
                    'text': {
                        'content': error_summary
                    }
                }
            ]
        }

    # If there are properties to update, send the patch
    if update_props:
        update_url = f'https://api.notion.com/v1/pages/{page_id}'
        update_headers = {
            'Authorization': f'Bearer {notion_token}',
            'Notion-Version': notion_version,
            'Content-Type': 'application/json',
        }
        update_payload = {
            'properties': update_props
        }
        try:
            update_resp = requests.patch(update_url, headers=update_headers, json=update_payload)
            update_resp.raise_for_status()
            if next_action_text:
                print(next_action_text)
            else:
                print('Notion page updated.')
        except Exception as exc:
            print(f'Failed to update Notion page: {exc}')
    else:
        print('No properties to update.')


if __name__ == '__main__':
    main()
