import sys
import logging
from explorer import explorer
sys.path.append('../../')


# log setting
def example_dynreg():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    dyn_explorer = explorer.QcloudExplorer('sample/device_info.json')
    dyn_explorer.enable_logger(logging.DEBUG)
    ret, msg = dyn_explorer.dynreg_device()

    if ret == 0:
        print('dynamic register success, psk: {}'.format(msg))
    else:
        print('dynamic register fail, msg: {}'.format(msg))
    return True
