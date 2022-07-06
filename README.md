<h1 align="center">
    Network Management Protocols for Mountebank
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/telekom/mb-netmgmt?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/telekom/mb-netmgmt?style=flat"></a>
    <a href="./COPYING" title="License"><img src="https://img.shields.io/badge/License-GPL--2.0-blue.svg?style=flat"></a>
</p>

<p align="center">
  <a href="#development">Development</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#support-and-feedback">Support</a> •
  <a href="#how-to-contribute">Contribute</a> •
  <a href="#licensing">Licensing</a>
</p>

SNMP, Telnet, SSH and NETCONF implementation for [Mountebank](https://www.mbtest.org/)

## Installation

### Docker

```sh
$ docker run -p2525:2525 -p23:23 -p830:830 cbuehler/mb-netmgmt
info: [mb:2525] Loaded custom protocol snmp
info: [mb:2525] Loaded custom protocol telnet
info: [mb:2525] Loaded custom protocol netconf
info: [mb:2525] Loaded custom protocol ssh
info: [mb:2525] mountebank v2.6.0 now taking orders - point your browser to http://localhost:2525/ for help
```

### Manual installation

```sh
$ npm install -g mountebank
$ pip install mb-netmgmt
$ wget https://raw.githubusercontent.com/telekom/mb-netmgmt/main/mb_netmgmt/protocols.json
$ mb
info: [mb:2525] Loaded custom protocol snmp
info: [mb:2525] Loaded custom protocol telnet
info: [mb:2525] Loaded custom protocol netconf
info: [mb:2525] Loaded custom protocol ssh
info: [mb:2525] mountebank v2.6.0 now taking orders - point your browser to http://localhost:2525/ for help
```

## Usage

```sh
$ curl -XPUT localhost:2525/imposters -d '
{
  "imposters": [
    {
      "port": 23,
      "protocol": "telnet",
      "stubs": [
        {
          "predicates": [
            {
              "deepEquals": {
                "command": "show run\r\n"
              }
            }
          ],
          "responses": [
            {
              "is": {
                "response": "end\r\n\r\n#"
              }
            }
          ]
        },
        {
          "responses": [
            {
              "proxy": {
                "predicatesGenerators": [
                  {
                    "matches": {
                      "command": true
                    }
                  }
                ],
                "to": "telnet://example.org"
              }
            }
          ]
        }
      ]
    },
    {
      "port": 830,
      "protocol": "netconf",
      "stubs": [
        {
          "predicates": [
            {
              "deepEquals": {
                "rpc": "<get-config>running</get-config>"
              }
            }
          ],
          "responses": [
            {
              "is": {
                "rpc-reply": "<rpc-reply xmlns=\"urn:ietf:params:xml:ns:netconf:base:1.0\"><configuration/></rpc-reply>"
              }
            }
          ]
        },
        {
          "responses": [
            {
              "proxy": {
                "predicateGenerators": [
                  {
                    "matches": {
                      "rpc": true
                    }
                  }
                ],
                "to": "netconf://username:password@example.org"
              }
            }
          ]
        }
      ]
    }
  ]
}
'
```

For more details, have a look at the [Mountebank documentation](https://www.mbtest.org/)

## Code of Conduct

This project has adopted the [Contributor Covenant](https://www.contributor-covenant.org/) in version 2.1 as our code of conduct. Please see the details in our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). All contributors must abide by the code of conduct.

## Working Language

We decided to apply _English_ as the primary project language.  

Consequently, all content will be made available primarily in English. We also ask all interested people to use English as language to create issues, in their code (comments, documentation etc.) and when you send requests to us. The application itself and all end-user facing content will be made available in other languages as needed.

## Support and Feedback

The following channels are available for discussions, feedback, and support requests:

| Type                     | Channel                                                |
| ------------------------ | ------------------------------------------------------ |
| **Issues**   | <a href="/../../issues/new/choose" title="General Discussion"><img src="https://img.shields.io/github/issues/telekom/mb-netmgmt?style=flat-square"></a> </a>   |
| **Other Requests**    | <a href="mailto:opensource@telekom.de" title="Email Open Source Team"><img src="https://img.shields.io/badge/email-Open%20Source%20Team-green?logo=mail.ru&style=flat-square&logoColor=white"></a>   |

## How to Contribute

Contribution and feedback is encouraged and always welcome. For more information about how to contribute, the project structure, as well as additional contribution information, see our [Contribution Guidelines](./CONTRIBUTING.md). By participating in this project, you agree to abide by its [Code of Conduct](./CODE_OF_CONDUCT.md) at all times.

## Licensing

Copyright (c) 2021 Deutsche Telekom AG.

Licensed under the **GNU General Public License Version 2.0** (or later) (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License by reviewing the file [COPYING](./COPYING) in the repository or by downloading the respective version from  
[https://www.gnu.org/licenses/](https://www.gnu.org/licenses/)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the [COPYING](./COPYING) for the specific language governing permissions and limitations under the License.
