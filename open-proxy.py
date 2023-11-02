import aiohttp
from aiohttp import web
import logging
from colorlog import ColoredFormatter

import argparse

# Initialize the parser with a description that includes the setup instructions
parser = argparse.ArgumentParser(
    description='''
    Open Proxy Script Usage Instructions:
    
    To set up internet access for a drone using an SSH reverse tunnel, follow these steps:
    
    On your local machine, establish a reverse tunnel:
    ssh -R 8080:localhost:8080 bstg@drone
    
    Then, on the drone, allow TCP forwarding and set the proxy environment variables:
    sudo sed -i 's/#AllowTcpForwarding/AllowTcpForwarding/g' /etc/ssh/sshd_config
    sudo service ssh restart
    export http_proxy=http://localhost:8080
    export https_proxy=http://localhost:8080
    
    Make sure the SSH server configuration has 'GatewayPorts' enabled if needed.
    ''',
    formatter_class=argparse.RawTextHelpFormatter
)

# The rest of your argument definitions would go here

# Parse the arguments
args = parser.parse_args()

# Rest of your code goes here

# Setup logger
logger = logging.getLogger('proxy')
handler = logging.StreamHandler()
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
    log_colors={
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# This dictionary defines the color for each type of status code
status_colors = {
    '2': '32',  # Green
    '3': '34',  # Blue
    '4': '31',  # Red
    '5': '35',  # Magenta
}

def colorize_status_code(code):
    """Wrap the status code in ANSI escape sequences for the corresponding color."""
    return f"\033[{status_colors.get(str(code)[0], '37')}m{code}\033[0m"

async def handle(request):
    url = str(request.url.with_scheme(request.headers.get('X-Forwarded-Proto', 'http')))
    method = request.method
    data = await request.read()
    headers = request.headers.copy()

    logger.info(f"Request URL: {url}")
    logger.info(f"HTTP Method: {method}")

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, data=data, headers=headers) as response:
            status_code_colored = colorize_status_code(response.status)
            logger.info(f"Response Status: {status_code_colored}\n")

            proxied_response = web.Response(body=await response.read(), status=response.status)
            proxied_response.headers.update(response.headers)

            return proxied_response

app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle)
web.run_app(app, port=8080)
