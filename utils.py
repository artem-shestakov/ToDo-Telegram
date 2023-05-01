async def get(session, url, headers=None):
    """Send GET request"""
    async with session.get(url, headers=headers) as response:
        return {
            "code": response.status,
            "response": await response.json()
        }

async def post(session, url, headers=None, data=None, json=None):
    """Send POST requests"""
    async with session.post(url, headers=headers, data=data, json=json) as response:
        return {
            "code": response.status,
            "response": await response.json()
        }