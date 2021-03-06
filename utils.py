import json
import os
import random
import time
import uuid
from urllib.parse import urljoin

from aiohttp import ClientSession
import asyncio


# Read configuration from env
SERVER_URL = os.getenv(
    'URL_SERVER',
    'https://screenshots.stage.mozaws.net').rstrip('/')

text_strings = """\
Example strings like apple orange banana some stuff like whatever and whoever
 and bucket blanket funky etc keyboard screen house window tree leaf leaves
 feather feathers""".split()


def get_example_images():
    """
    Load a set of example images from disk.
    """
    example_images = {}
    with open('./exercise_images.py') as f:
        exec(f.read(), example_images)
        example_images = example_images["example_images"]
    return example_images


def get_random_text(word_count):
    """
    Create a random word jumble based on the specified word count.
    """
    text = []
    for i in range(word_count):
        text.append(random.choice(text_strings))
    return " ".join(text)


def make_device_info():
    """
    Create some dummy device info.
    """
    return dict(
        addonVersion='0.1.2014test',
        platform='test')


def make_example_shot(keywords=None):
    """
    Create a dummy JSON payload of shot data.
    """
    image = random.choice(exampleImages)
    docTitle = "Load test page"
    if keywords:
        docTitle += " " + keywords

    return dict(
        deviceId=deviceId,
        url="http://test.com/?" + make_uuid(),
        docTitle=docTitle,
        createdDate=int(time.time() * 1000),
        favicon=None,
        siteName="test site",
        isPublic=True,
        showPage=False,
        clips={
            make_uuid(): dict(
                createdDate=int(time.time() * 1000),
                sortOrder=100,
                image=dict(
                    url=image["url"],
                    captureType="selection",
                    text=get_random_text(10),
                    location=dict(
                        top=100,
                        left=100,
                        bottom=100 + image["height"],
                        right=100 + image["width"],
                    ),
                    dimensions=dict(
                        x=image["width"],
                        y=image["height"],
                    ),
                ),
            ),
        },
    )


def make_uuid():
    """
    Create a random UUID.
    """
    return str(uuid.uuid1()).replace("-", "")


def make_random_id():
    return make_uuid()[:16]


def run_in_fresh_loop(coro):
    """
    Create a new async event loop.
    """
    loop = asyncio.new_event_loop()
    task = loop.create_task(coro(loop))
    res = loop.run_until_complete(task)
    loop.close()
    return res


def login(args):
    """
    Log in or register a new Screenshots "account".
    """
    global _COOKIES

    async def _login(loop):
        data = {'deviceId': deviceId,
                'secret': secret,
                'deviceInfo': json.dumps(deviceInfo)}

        login_url = urljoin(SERVER_URL, "/api/login")
        register_url = urljoin(SERVER_URL, "/api/register")

        async with ClientSession(loop=loop) as session:
            async with session.post(login_url, data=data) as resp:
                if resp.status == 404:
                    async with session.post(register_url, data=data) as resp:
                        status = resp.status
                else:
                    status = resp.status

        if status > 399:
            raise AssertionError("Could not login or register")
        return resp.cookies

    _COOKIES = run_in_fresh_loop(_login)
    return {'cookies': _COOKIES}


def logout():
    """
    Delete your Screenshots "account" and delete all your stored images (if any).
    """
    async def _logout(loop):
        delete_url = urljoin(SERVER_URL, "/leave-screenshots/leave")
        async with ClientSession(cookies=_COOKIES, loop=loop) as session:
            async with session.post(delete_url, data={}) as resp:
                assert resp.status < 400

    run_in_fresh_loop(_logout)


def setup_worker(worker_id, args):
    return {'cookies': _COOKIES}


async def create_shot(session=None, loop=None, keywords=None):
    """
    Create/upload a new Page Shot shot.
    """
    if session is None:
        session = ClientSession(cookies=_COOKIES, loop=loop)
        fresh_session = True
    else:
        fresh_session = False

    try:
        path = "data/{}/test.com".format(make_random_id())

        if path not in _SHOTS:
            _SHOTS.append(path)

        path_screenshots = urljoin(SERVER_URL, path)
        data = make_example_shot(keywords=keywords)
        headers = {'content-type': 'application/json'}

        async with session.put(path_screenshots, data=json.dumps(data),
                               headers=headers) as r:
            r.path = path
            r.session = session
            return r
    finally:
        if fresh_session:
            session.close()


async def read_shot(session=None, path=None, loop=None):
    """
    Read a shot, given a specific URL fragment (for example: "data/{UUID}/test.com")
    """
    if session is None:
        session = ClientSession(cookies=_COOKIES, loop=loop)
        fresh_session = True
    else:
        fresh_session = False

    try:
        if path is None:
            path = _SHOTS[-1]

        path_screenshots = urljoin(SERVER_URL, path)
        headers = {'content-type': 'application/json'}

        async with session.get(path_screenshots, headers=headers) as resp:
            return resp
    finally:
        if fresh_session:
            session.close()


async def list_shots(session=None):
    """
    Retrieve a list of shots (as JSON).
    """
    path = "shots?data=json"
    path_screenshots = urljoin(SERVER_URL, path)
    headers = {'content-type': 'application/json', 'accept': 'application/json, */*'}

    async with session.get(path_screenshots, data={}, headers=headers) as r:
        r.bod = await r.json()
        return r


async def search_shots(session=None, query=None):
    """
    Search a list of shots (as JSON).
    """
    path = "shots?q=" + query + "&data=json"
    path_screenshots = urljoin(SERVER_URL, path)
    headers = {'content-type': 'application/json', 'accept': 'application/json, */*'}

    async with session.get(path_screenshots, data={}, headers=headers) as r:
        r.bod = await r.json()
        return r


_COOKIES = None
_SHOTS = []

exampleImages = get_example_images()
deviceInfo = make_device_info()
deviceId = make_uuid()
secret = make_uuid()
