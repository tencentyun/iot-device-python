* [API接口说明](#API接口说明)
  * [MQTT接口](#MQTT接口)
  * [网关接口](#网关接口)
  * [数据模板接口](#设备影子接口)
  * [动态注册接口](#动态注册接口)
  * [OTA接口](#OTA接口)
  * [LOG接口](#LOG接口)

# API接口说明
## MQTT接口

| 接口名称 | 接口描述 |
| :-: | :-: |
| connect | MQTT连接 |
| disconnect | 断开MQTT连接 |
| subscribe | MQTT订阅 |
| unsubscribe | MQTT取消订阅 |
| publish | MQTT发布消息 |
| registerMqttCallback | 注册MQTT回调函数 |
| registerUserCallback | 注册用户回调函数 |
| isMqttConnected | MQTT是否正常连接 |
| getConnectState | 获取MQTT连接状态 |
| setReconnectInterval | 设置MQTT重连尝试间隔 |
| setMessageTimout | 设置消息发送超时时间 |
| setKeepaliveInterval | 设置MQTT保活间隔 |

## 网关接口
| 接口名称 | 接口描述 |
| :-: | :-: |
| gatewayInit | 网关初始化 |
| isSubdevStatusOnline | 判断子设备是否在线 |
| updateSubdevStatus | 更新子设备在线状态 |
| gatewaySubdevGetConfigList | 获取配置文件中子设备列表 |
| gatewaySubdevOnline | 代理子设备上线 |
| gatewaySubdevOffline | 代理子设备下线 |
| gatewaySubdevBind | 绑定子设备 |
| gatewaySubdevUnbind | 解绑子设备 |
| gatewaySubdevSubscribe | 子设备订阅 |

## 数据模板接口
| 接口名称 | 接口描述 |
| :-: | :-: |
| templateInit | 数据模板初始化 |
| getEventsList | 获取设备event列表 |
| getActionList | 获取设备action列表 |
| getPropertyList | 获取设备property列表 |
| templateSetup | 解析数据模板 |
| templateEventPost | events上报 |
| templateJsonConstructReportArray | 构建上报的json结构 |
| templateReportSysInfo | 设备信息上报 |
| templateControlReply | 控制消息应答 |
| templateActionReply | action消息应答 |
| templateGetStatus | 获取设备最新状态 |
| templateReport | 设备属性上报 |
| clearControl | 清除控制 |
| templateDeinit | 数据模板销毁 |

## 动态注册接口
| 接口名称 | 接口描述 |
| :-: | :-: |
| dynregDevice | 获取设备动态注册的信息 |

## OTA接口
| 接口名称 | 接口描述 |
| :-: | :-: |
| otaInit | OTA初始化 |
| otaIsFetching | 判断是否正在下载 |
| otaIsFetchFinished | 判断是否下载完成 |
| otaReportUpgradeSuccess | 上报升级成功消息 |
| otaReportUpgradeFail | 上报升级失败消息 |
| otaIoctlNumber | 获取下载固件大小等int类型信息 |
| otaIoctlString | 获取下载固件md5等string类型信息 |
| otaResetMd5 | 重置md5信息 |
| otaMd5Update | 更新md5信息 |
| httpInit | 初始化http |
| otaReportVersion | 上报当前固件版本信息 |
| otaDownloadStart | 开始固件下载 |
| otaFetchYield | 读取固件 |

## LOG接口
| 接口名称 | 接口描述 |
| :-: | :-: |
| logInit | 日志初始化 |