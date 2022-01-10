import sys
import logging
from hub.hub import QcloudHub

provider = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
qcloud = provider.hub
logger = None

