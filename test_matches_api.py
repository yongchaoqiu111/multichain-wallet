import requests
import json

r = requests.post('http://localhost:5004/matches/list', json={'game': 'all', 'page': 1})
result = r.json()

if result.get('success'):
    matches = result.get('matches', [])
    print(f"总共 {len(matches)} 场比赛")
    for i, match in enumerate(matches[:5]):
        print(f"\n第{i+1}场:")
        print(f"  时间: {match.get('start_time')}")
        print(f"  游戏: {match.get('game')}")
        print(f"  队伍: {match.get('team1')} vs {match.get('team2')}")
        print(f"  联赛: {match.get('league_name')}")
else:
    print(f"错误: {result.get('message')}")
