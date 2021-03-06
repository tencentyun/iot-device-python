import json
import re
import urllib.request
import setuptools

name = "TIoTExploreSDK"
resp = urllib.request.urlopen(f'https://test.pypi.org/pypi/{name}/json')
data = json.loads(resp.read().decode("utf-8"))
version = data['info']['version']
last_num = re.findall(r'\d+', version)[-1]
version = version[:-len(last_num)] + str(int(last_num) + 1)

with open("README.md", mode='r', encoding='UTF-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name=("%s" % name),
#    version="0.0.1a01",
    version=f"{version}",
    author="larrytin",
    author_email="dev_tester@163.com",
    description="Tencent IoT Explorer SDK for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tencentyun/iot-device-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
