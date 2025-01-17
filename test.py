import requests
url = 'http://wynd.network'
username = 'user-spgps23cve-country-my-city-george_town'
password = '70yyXJcoscQd3bQ~7o'
proxy = f"http://nizammufid1dc56:4c0939bf1bc9_country-my_session-5f906630_lifetime-1h@proxy.speedproxies.net:12321"
result = requests.get(url, proxies = {
    'http': proxy,
    'https': proxy
})
print(result.text)