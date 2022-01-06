* [API Description](#API-Description)
  * [MQTT APIs](#MQTT-APIs)
  * [Gateway APIs](#Gateway-APIs)
  * [Device shadow APIs](#Device-shadow-APIs)
  * [RRPC APIs](#RRPC-APIs)
  * [Broadcast APIs](#Broadcast-APIs)
  * [Dynamic registration APIs](#Dynamic-registration-APIs)
  * [OTA APIs](#OTA-APIs)
  * [Log APIs](#Log-APIs)

# API Description
## MQTT APIs
| API | Description |
| :-: | :-: |
| connect | Establishes MQTT connection |
| disconnect | Closes MQTT connection |
| subscribe | Subscribes to MQTT |
| unsubscribe | Unsubscribes from MQTT |
| publish | Publishes message over MQTT |
| registerMqttCallback | Registers MQTT callback function |
| registerUserCallback | Registers user callback function |
| isMqttConnected | Checks whether MQTT is normally connected |
| getConnectState | Gets MQTT connection status |
| setReconnectInterval | Sets MQTT reconnection attempt interval |
| setMessageTimout | Sets message sending timeout period |
| setKeepaliveInterval | Sets MQTT keepalive interval |

## Gateway APIs
| API | Description |
| :-: | :-: |
| gatewayInit | Initializes gateway |
| isSubdevStatusOnline | Determines whether subdevice is online |
| updateSubdevStatus | Updates subdevice's online status |
| gatewaySubdevGetConfigList | Gets subdevice list from configuration file |
| gatewaySubdevOnline | Proxies subdevice connection |
| gatewaySubdevOffline | Proxies subdevice disconnection |
| gatewaySubdevBind | Binds subdevice |
| gatewaySubdevUnbind | Unbinds subdevice |
| gatewaySubdevGetBindList | Gets the list of bound subdevices |
| gatewaySubdevSubscribe | Proxies subdevice subscription |

## Device shadow APIs
| API | Description |
| :-: | :-: |
| shadowInit | Initializes device shadow |
| getShadow | Gets device shadow |
| shadowJsonConstructDesireAllNull | Constructs JSON structure |
| shadowUpdate | Updates device shadow |
| shadowJsonConstructReport | Constructs JSON structure for reporting |

## RRPC APIs
| API | Description |
| :-: | :-: |
| rrpcInit | Initializes RRPC |
| rrpcReply | Replies to message |

## Broadcast APIs
| API | Description |
| :-: | :-: |
| broadcastInit | Initializes broadcast |

## Dynamic registration APIs
| API | Description |
| :-: | :-: |
| dynregDevice | Gets the dynamic registration information of device |

## OTA APIs
| API | Description |
| :-: | :-: |
| otaInit | Initializes OTA |
| otaIsFetching | Determines whether the download is in progress |
| otaIsFetchFinished | Determines whether the download is completed |
| otaReportUpgradeSuccess | Reports update success message |
| otaReportUpgradeFail | Reports update failure message |
| otaIoctlNumber | Gets the information of the downloaded firmware in `int` type, such as the size |
| otaIoctlString | Gets the information of the downloaded firmware in `String` type, such as MD5 |
| otaResetMd5 | Resets MD5 information |
| otaMd5Update | Updates MD5 information |
| httpInit | Initializes HTTP |
| otaReportVersion | Reports the information of current firmware version |
| otaDownloadStart | Starts firmware download |
| otaFetchYield | Reads firmware |

## Log APIs
| API | Description |
| :-: | :-: |
| logInit | Initializes log |