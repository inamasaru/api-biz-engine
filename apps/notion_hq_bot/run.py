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

    # Build prompt for OpenAI
    prompt = f"現在の進捗状況に基づいて次のアクションを提案してください。\nFinalGoal: {final_goal}\nNearGoal: {near_goal}\nProgress: {progress}\n次のアクションは120文字以内で、箇条書きでも構いません。"

    # Call OpenAI to get next action
    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {'role': 'system', 'content': 'あなたは目標達成をサポートするアシスタントです。'},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        ai_message = response.choices[0].message.content.strip()
    except Exception as exc:
        print(f'OpenAI API error: {exc}')
        return

    # Truncate to 120 characters
    next_action_text = ai_message[:120]

    # Update the page with NextAction and UpdatedAt
    update_url = f'https://api.notion.com/v1/pages/{page_id}'
    update_headers = {
        'Authorization': f'Bearer {notion_token}',
        'Notion-Version': notion_version,
        'Content-Type': 'application/json',
    }
    updated_at = datetime.datetime.utcnow().isoformat()
    update_payload = {
        'properties': {
            'NextAction': {
                'rich_text': [
                    {
                        'text': {
                            'content': next_action_text
                        }
                    }
                ]
            },
            'UpdatedAt': {
                'date': {
                    'start': updated_at
                }
            }
        }
    }
    update_resp = requests.patch(update_url, headers=update_headers, json=update_payload)
    try:
        update_resp.raise_for_status()
    except Exception as exc:
        print(f'Failed to update Notion page: {exc}')
        return
    print('Notion page updated successfully.')


if __name__ == '__main__':
    main()
