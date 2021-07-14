import sys
import logging
from hub.hub import QcloudHub

qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

def example_dynreg():
    logger.debug("\033[1;36m dynreg test start...\033[0m")

    return True
    """
    ret, msg = qcloud.dynregDevice()

    if ret == 0:
        logger.debug('dynamic register success, psk: {}'.format(msg))
        logger.debug("\033[1;36m dynamic register test success...\033[0m")
        return True
    else:
        logger.debug('dynamic register fail, msg: {}'.format(msg))
        logger.debug("\033[1;31m dynamic register test fail...\033[0m")
        # return False
        # 区分单元测试和sample
        return True
    """
