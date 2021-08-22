# HA-Unraid-API
## Home Assistant Custom Component for [Unraid-API](https://github.com/ElectricBrainUK/UnraidAPI) by [ElectricBrainUK](https://github.com/ElectricBrainUK)

## Features
- Monitor and manage dockers and virtual machines on your Unraid servers

## Installation

- Place 'unraidapi' folder in your Home Assistant custom_components folder
- in your configuration.yaml file, add the following:

```
unraid:
  host: "192.168.178.46"        // IP Address of the server running the unraid-api container
  port: 3005                    // Port of unraid-api
  servers:                      // List of all servers managed by your unraid-api, used for authentication
    my_unraid:                  // Server name
      host: "192.168.178.46"    // Server IP
      user: "root"              // Server Username
      pass: "admin"             // Server Password
    my_unraid_2:                // (Optional) Add any other servers which are managed by the same unraid-api isntance
      host: "192.168.178.44"
      user: "root"
      pass: "admin"
```
