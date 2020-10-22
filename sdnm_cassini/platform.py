# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Copyright  (c) 2020  National Network for Education and Research (RNP)      +
#                                                                              +
#  Licensed under the Apache License, Version 2.0 (the "License");             +
#  you may not use this file except in compliance with the License.            +
#  You may obtain a copy of the License at                                     +
#                                                                              +
#      http://www.apache.org/licenses/LICENSE-2.0                              +
#                                                                              +
#  Unless required by applicable law or agreed to in writing, software         +
#  distributed under the License is distributed on an "AS IS" BASIS,           +
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    +
#  See the License for the specific language governing permissions and         +
#  limitations under the License.                                              +
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from sdnm_cassini.utils import make_query, convert_freq_vlan

MODULE = "openconfig-platform:components"


def get_component_config_name(session):
    module = MODULE
    submodule = "component[node()]/config/name"
    xpath = "/{}/{}".format(module,submodule)
    values = make_query(session, xpath, multi=True)
    if values is None:
        return None
    ret = []
    for v in values:
        s = v.split("name = ")
        if "/" not in s[1]:
            ret.append(s[1])
    return ret.copy()


def get_component_state_type(session, name):
    module = MODULE
    submodule = "component[name='{}']/state/type".format(name)
    xpath = "/{}/{}".format(module,submodule)
    values = make_query(session, xpath)
    if values is None:
        return None
    s = values[0].split("type = ")
    t = s[1].split(":")
    return t[1]


def get_config_frequency_vlan(session, name):
    module = MODULE
    submodule = "component[name='{}']/openconfig-terminal-device:optical-channel/config/frequency".format(name)
    xpath = "/{}/{}".format(module, submodule)
    values = make_query(session, xpath)
    s = values[0].split("frequency = ")
    f = s[1]
    v = None
    if f is not None:
        v = convert_freq_vlan(f.strip())
        return f, v
    return f, v