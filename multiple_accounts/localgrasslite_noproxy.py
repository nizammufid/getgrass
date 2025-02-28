import asyncio
import random
import ssl
import json
import time
import uuid
import requests
import base64
import websockets
from loguru import logger
from fake_useragent import UserAgent
from datetime import datetime

async def connect_to_wss(user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID: {device_id}")
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg"
            }
        #Checkin
            headers_checkin = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "none",
                "User-Agent": custom_headers['User-Agent']
                }

            payload_checkin = {
                    "browserId": device_id,
                    "userId": user_id,
                    "version": "5.0.0",
                    "extensionId": "ilehaonighjijnmpnagapkhpcdbhclfg",
                    "userAgent": custom_headers['User-Agent'],
                    "deviceType": "extension"
                }

            response_checkin = requests.post("https://director.getgrass.io/checkin", headers=headers_checkin, data=json.dumps(payload_checkin))
            #checkin_data = response_checkin.content
            checkin_data = json.loads(response_checkin.content.decode())
            destination = checkin_data['destinations'][0]
            token = checkin_data['token']
            #print(checkin_data["destinations"][0])

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            #urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            #uri = random.choice(urilist)
            uri = f"wss://{destination}/?token={token}"
            logger.debug(uri)
            
            # Connect to WebSocket server
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers) as websocket:
                
                # Send ping every 5 seconds
                async def send_ping():
                    while True:
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}
                        })
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)
                
                # Start ping task
                await asyncio.sleep(1)
                asyncio.create_task(send_ping())
                
                # Listen for responses
                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")
                        
                    # Generate the current datetime in UTC
                    now = datetime.utcnow()
                    # Format the datetime as a string in the desired format
                    formatted_time = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "5.0.0",
                                "extension_id": "ilehaonighjijnmpnagapkhpcdbhclfg"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "HTTP_REQUEST":
                        #Fetching API DATA AND ENCODE base64
                        urlapi = message["data"]["url"]
                        responseurl = requests.get(urlapi)
                        contenturl = responseurl.content
                        encoded_content = base64.b64encode(contenturl).decode('utf-8')
                        httpreq_response = {
                            "id": message["id"],
                            "origin_action": "HTTP_REQUEST",
                            "result": {
                                "body" : encoded_content,
                                "url": message["data"]["url"],
                                "status": int(200),
                                "status_text": "",
                                "headers": {
                                    "content-type": "application/json; charset=utf-8",
                                    "date": formatted_time,
                                    "keep-alive": "timeout=5",
                                    "proxy-connection": "keep-alive",
                                    "x-powered-by": "Express",
                                }
                            }
                        }
                        logger.debug(httpreq_response)
                        await websocket.send(json.dumps(httpreq_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))

        except Exception as e:
            logger.error(f"Error with user ID {user_id}: {e}")

async def main():
    # Load user IDs from 'userid_list.txt' file
    try:
        with open('userid_list.txt', 'r') as file:
            user_ids = file.read().splitlines()

        # Create a task for each user ID
        tasks = [asyncio.ensure_future(connect_to_wss(user_id)) for user_id in user_ids]
        await asyncio.gather(*tasks)

    except FileNotFoundError:
        logger.error("File 'userid_list.txt' not found. Please create it and add user IDs.")
    except Exception as e:
        logger.error(f"Error loading user IDs: {e}")

if __name__ == '__main__':
    asyncio.run(main())