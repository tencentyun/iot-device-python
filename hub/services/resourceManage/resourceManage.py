import json
from hub.utils.providers import ConnClientProvider
from hub.utils.providers import TopicProvider
import hashlib
from enum import Enum
from enum import IntEnum

class ResourceManage(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls, logger=logger)
        self.__protocol = self.__provider.protocol
        self.__topic = TopicProvider(product_id, device_name)
        self.__logger = logger
        self.__process_id = None
        self.__user_callback = {}
        self.http_manager = None
        self.__resource_manager = None

    class ResourceState(Enum):
        IOT_RESOURCES_UNINITED = 0
        IOT_RESOURCES_INITED = 1
        IOT_RESOURCES_FETCHING = 2
        IOT_RESOURCES_FETCHED = 3
        IOT_RESOURCES_DISCONNECTED = 4

    class resource_manage(object):
        def __init__(self):
            self.channel = None
            self.state = 0
            self.size_fetched = 0
            self.size_last_fetched = 0
            self.file_size = 0
            self.purl = None
            self.version = None
            self.md5sum = None
            self.md5 = None
            self.host = None
            self.is_https = False

            self.report_timestamp = 0

            # http连接管理
            self.http_manager = None

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def handle_resource(self, topic, qos, payload, userdata):

        if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def resource_init(self, resource_cb):
        topic = self.__topic.resource_manager_topic_sub
        self.__user_callback[topic] = resource_cb

        self.__resource_manage = self.resource_manage()
        self.__resource_manage.state = self.ResourceStateState.IOT_OTAS_UNINITED

        return self.__protocol.subscribe(topic, 1)

    def resource_manager_init(self):
        self.__resource_manage.state = self.ResourceStateState.IOT_RESOURCES_INITED
        self.__resource_manage.md5 = hashlib.md5()

    def resource_publish(self, message, qos):
        topic_pub = self.__topic.resource_manager_topic_pub
        rc, mid = self.__protocol.publish(topic_pub, json.dumps(message), qos)
        return rc, mid

    def resource_create_upload_task(self, size, name, md5sum):
        self.__assert(size)
        self.__assert(name)
        self.__assert(md5sum)

        if self.__resource_manage.state == self.ResourceStateState.IOT_OTAS_UNINITED:
            raise ValueError('resource handle is uninitialized')

        createTask = {
            "type": "create_upload_task",
            "size": size,
            "name": name,
            "md5sum": md5sum,
        }
        return self.resource_publish(createTask,1)


    def resource_file_md5(self, fileName):
        m = hashlib.md5()  # 创建md5对象
        with open(fileName, 'rb') as fobj:
            while True:
                data = fobj.read(4096)
                if not data:
                    break
                m.update(data)  # 更新md5对象

        return m.hexdigest()  # 返回md5对象


    # def resource_reply(self, reply):
    #
    #     topic = self.__topic.resource_manager_topic_pub
    #     return self.__protocol.publish(topic, json.dumps(reply), 0)