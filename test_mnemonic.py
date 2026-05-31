import requests

mnemonic = "ugly lucky spoon sad clock decide roast hundred clerk notice agree oval"
res = requests.post('http://localhost:5001/api/wallet/import/mnemonic', json={'mnemonic': mnemonic})
print('Import Mnemonic:', res.text)
