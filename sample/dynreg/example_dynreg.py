import sys
import logging
from explorer import explorer
sys.path.append('../../')


# log setting
def example_dynreg():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    print("\033[1;36m dynreg test start...\033[0m")

    dyn_explorer = explorer.QcloudExplorer('sample/device_info.json')
    dyn_explorer.enableLogger(logging.DEBUG)
    ret, msg = dyn_explorer.dynregDevice()

    if ret == 0:
        print('dynamic register success, psk: {}'.format(msg))
        print("\033[1;36m dynamic register test success...\033[0m")
        return True
    else:
        print('dynamic register fail, msg: {}'.format(msg))
        print("\033[1;31m dynamic register test fail...\033[0m")
        return False
