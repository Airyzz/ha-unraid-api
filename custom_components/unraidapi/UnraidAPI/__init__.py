import aiohttp
import asyncio
import json
import logging
import base64

class Unraid:
    host = ""
    port = ""
    token = None
    credentials = dict()

    def __init__(self, host, port, credentials):
        self.host = str(host)
        self.port = str(port)
        self.credentials = credentials

    def url(self):
        return "http://" + self.host + ":" + self.port

    def get_b64(self, user, password):
        usrPass = user + ":" + password
        return base64.b64encode(usrPass.encode()).decode()

    async def get(self, path):
        url = "http://" + self.host + ":" + self.port + "/" + path 

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return [response.status, await response.text()]
        except Exception as e:
            return str(e)

    async def post(self, path, payload):
        url = "http://" + self.host + ":" + self.port + "/" + path

        user = self.credentials[payload["server"]]["user"]
        password = self.credentials[payload["server"]]["pass"]

        payload["auth"] = self.get_b64(user, password)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=json.dumps(payload)) as response:
                    return [response.status, await response.text()]
        except Exception as e:
            return str(e)

    async def get_servers(self):
        result = await self.get("api/getServers")
        if result[0] == 200:
            return json.loads(result[1])
        return None

    async def docker_status(self, server, docker_id, action):
        result = await self.post("api/dockerStatus", {
            "id": docker_id,
            "action": action,
            "server": server
        })

        return result


    async def vm_status(self, server, vm_id, action):
        result = await self.post("api/vmStatus", {
            "id": vm_id,
            "action": action,
            "server": server
        })

        return result





