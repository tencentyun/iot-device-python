* [Event Reporting and Multi-Event Reporting](#Event-Reporting-and-Multi-Event-Reporting)
  * [Publishing to topic for reporting event](#Publishing-to-topic-for-reporting-event)
  * [Publishing to topic for reporting multiple events](#Publishing-to-topic-for-reporting-multiple-events)

# Event Reporting and Multi-Event Reporting

This document describes how a device publishes to topics for event reporting and multi-event reporting.

## Publishing to topic for reporting event 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template, call the `templateEventPost()` API for event reporting, and publish to the event topic:
`$thing/up/event/{ProductID}/{DeviceName}`

Below is the sample code:
```python
# Construct QcloudExplorer
qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
# Initialize the log
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

# Register the MQTT callback
qcloud.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)
# Get the product ID and device name
product_id = qcloud.getProductID()
device_name = qcloud.getDeviceName()

# Connect to MQTT
qcloud.connect()

# Initialize the data template
qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
qcloud.templateSetup(product_id, device_name, "sample/template/template_config.json")

# Construct an event
timestamp = int(round(time.time() * 1000))
event = {
    "events": [
        {
            "eventId": "status_report",
            "type": "info",
            "timestamp": timestamp,
            "params": {
                "status":0,
                "message":"event test"
            }
        }
    ]
}
# Report the event
qcloud.templateEventPost(product_id, device_name, event)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 16:59:37,208.208 [log.py:35] - DEBUG - [event post] {'events': [{'eventId': 'status_report', 'type': 'info', 'timestamp': 1626857977209, 'params': {'status': 0, 'message': 'event test'}}]}
2021-07-21 16:59:37,209.209 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m5), 'b'$thing/up/event/xxx/dev1'', ... (182 bytes)
2021-07-21 16:59:37,209.209 [log.py:35] - DEBUG - publish success
2021-07-21 16:59:37,261.261 [client.py:2165] - DEBUG - Received PUBACK (Mid: 5)
2021-07-21 16:59:37,262.262 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 16:59:37,286.286 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/event/xxx/dev1', ...  (85 bytes)
2021-07-21 16:59:37,287.287 [log.py:35] - DEBUG - product_1:on_template_event:payload:{'method': 'events_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': '', 'data': {}},userdata:None
```
The above log represents the process in which the device publishes to the topic for reporting a single event successfully. As can be seen, the device publishes an event successfully and receives the `event_reply` from the cloud. In the information of the device created in the console, you can view the corresponding device event. If the `type` passed in is `info`, the event is of the information type. For more information on how to view device events in the console, please see [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).

## Publishing to topic for reporting multiple events 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template, call the `templateEventPost()` API for event reporting, and publish to the event topic:
`$thing/up/event/{ProductID}/{DeviceName}`

Below is the sample code:
```python
# Construct a JSON message
def report_json_construct_events(event_list):
    # deal events and add your real value
    status = 1
    message = "test"
    voltage = 20.0
    name = "memory"
    error_code = 0
    timestamp = int(round(time.time() * 1000))

    format_string = '"%s":"%s",'
    format_int = '"%s":%d,'
    events = []
    for event in event_list:
        string = '{'
        string += format_string % ("eventId", event.event_name)
        string += format_string % ("type", event.type)
        string += format_int % ("timestamp", timestamp)
        string += '"params":{'
        for prop in event.events_prop:
            if (prop.type == "int" or prop.type == "float"
                    or prop.type == "bool" or prop.type == "enum"):
                if prop.key == "status":
                    string += format_int % (prop.key, status)
                elif prop.key == "voltage":
                    string += format_int % (prop.key, voltage)
                elif prop.key == "error_code":
                    string += format_int % (prop.key, error_code)
            elif prop.type == "string":
                if prop.key == "message":
                    string += format_string % (prop.key, message)
                elif prop.key == "name":
                    string += format_string % (prop.key, name)

        string = string[:len(string) - 1]
        string += "}}"
        events.append(json.loads(string))

    json_out = '{"events":%s}' % json.dumps(events)

    return json.loads(json_out)

# Construct QcloudExplorer
qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
# Initialize the log
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

# Register the MQTT callback
qcloud.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)
# Get the product ID and device name
product_id = qcloud.getProductID()
device_name = qcloud.getDeviceName()

# Connect to MQTT
qcloud.connect()

# Initialize the data template
qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
qcloud.templateSetup(product_id, device_name, "sample/template/template_config.json")

# Get the event list from the configuration file
event_list = qcloud.getEventsList(product_id, device_name)
# Construct a JSON event structure based on the event list
events = report_json_construct_events(event_list)
# Report the event
qcloud.templateEventPost(product_id, device_name, events)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 16:48:28,464.464 [log.py:35] - DEBUG - [event post] {'events': [{'eventId': 'status_report', 'type': 'info', 'timestamp': 1626857308464, 'params': {'status': 1, 'message': 'test'}}, {'eventId': 'low_voltage', 'type': 'alert', 'timestamp': 1626857308464, 'params': {'voltage': 20}}, {'eventId': 'hardware_fault', 'type': 'fault', 'timestamp': 1626857308464, 'params': {'name': 'memory', 'error_code': 0}}]}
2021-07-21 16:48:28,464.464 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m5), 'b'$thing/up/event/xxx/dev1'', ... (409 bytes)
2021-07-21 16:48:28,464.464 [log.py:35] - DEBUG - publish success
2021-07-21 16:48:28,508.508 [client.py:2165] - DEBUG - Received PUBACK (Mid: 5)
2021-07-21 16:48:28,508.508 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 16:48:28,538.538 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/event/xxx/dev1', ...  (85 bytes)
2021-07-21 16:48:28,539.539 [log.py:35] - DEBUG - on_template_event:payload:{'method': 'events_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': '', 'data': {}},userdata:None
```
The above log represents the process in which the device publishes to the topic for reporting multiple events successfully. As can be seen, the device publishes events successfully and receives the `events_reply` from the cloud. In the information of the device created in the console, you can view the corresponding device events. If the `type` passed in is `info`, the event is of the information type; if `alert`, the alarm type; if `fault`, the fault type. For more information on how to view device events in the console, please see [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).
