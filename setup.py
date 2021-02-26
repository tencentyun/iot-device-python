import setuptools

with open("README.md", mode='r', encoding='UTF-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="iot-explorer-sdk",
    version="0.0.0",
    author="Tencent IoT Explorer Python SDK",
    author_email="",
    description="Tencent IoT Explorer SDK for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=['paho-mqtt'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
