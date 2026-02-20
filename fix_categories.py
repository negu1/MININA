#!/usr/bin/env python3
"""Fix skill categories"""
import json
from core.SkillVault import vault

# Fix manifests for Discord and Slack
skills_to_fix = [
    ('discord_bot', 'bots'),
    ('slack_bot', 'bots')
]

for skill_id, category in skills_to_fix:
    manifest_path = vault.live_dir / skill_id / 'manifest.json'
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text())
        data['category'] = category
        if 'tags' not in data:
            data['tags'] = []
        if category == 'bots':
            data['tags'].extend(['discord' if 'discord' in skill_id else 'slack', 'mensajeria'])
        manifest_path.write_text(json.dumps(data, indent=2))
        print(f'✅ Fixed {skill_id} -> category: {category}')

# Verify
print('\n📊 Current status:')
result = vault.list_skills_by_category()
print(f'Total: {result.get("total_skills", 0)}')
for cat, skills in result.get('categories', {}).items():
    print(f'  {cat}: {len(skills)} skills')
    for s in skills:
        print(f'    - {s["id"]} (cat: {s.get("category", "?")})')
