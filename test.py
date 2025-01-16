import requests
url = 'http://cyberfrost.net/'
username = 'user-spgps23cve-country-my-city-george_town'
password = '70yyXJcoscQd3bQ~7o'
proxy = f"http://{username}:{password}@gate.smartproxy.com:10001"
result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)