import requests
r = requests.post('http://localhost:5004/matches/list', json={'game': 'all'})
result = r.json()
print(f"成功: {result.get('success')}")
print(f"总数: {result.get('total')}")
if result.get('matches'):
    print(f"\n前3场比赛:")
    for i, match in enumerate(result['matches'][:3]):
        print(f"{i+1}. {match['team1']} vs {match['team2']} - {match['start_time']}")
