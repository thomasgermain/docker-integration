[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/thomasgermain/docker-integration?style=for-the-badge)

# Docker monitor integration

## Installation

- Through HACS [custom repositories](https://hacs.xyz/docs/faq/custom_repositories/) !

## Configuration

Configuration is done through the UI. Only parameter is the URL of the docker server (for example `unix:
///var/run/docker.sock` or `tcp://127.0.0.1:1234`).
You can also configure the refresh rate, this is 30 seconds by default.

## Changelog
See [releases details](https://github.com/thomasgermain/docker-integration/releases)

## Provided data
For each container following data are provided
- container status (running or not running)
- buttons to start, stop and restart a container
if the container is running:
- start time
- used cpu percentage
- used memory percentage
- used memory
- memory limit
- total network tx
- total network rx


---
<a href="https://www.buymeacoffee.com/tgermain" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
