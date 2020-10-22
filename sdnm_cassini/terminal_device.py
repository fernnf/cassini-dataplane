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

from sdnm_cassini.utils import make_query

MODULE = "openconfig-terminal-device:terminal-device"


def get_index_interfaces(session):
    module = MODULE
    submodule = "logical-channels/channel[node()]/index"
    xpath = "/{}/{}".format(module, submodule)
    values = make_query(session, xpath, multi=True)
    ret = []
    for v in values:
        s = v.split("index = ")
        ret.append(s[1])
    return ret.copy()


def get_lch_config_logical_channel(session, index):
    module = MODULE
    submodule1 = "logical-channels/channel[index='{}']".format(index)
    submodule2 = "logical-channel-assignments/assignment[index='{}']/config/logical-channel".format(index)
    xpath = "/{}/{}/{}".format(module, submodule1, submodule2)
    values = make_query(session, xpath)
    if values is None:
        return None
    ret = values[0].split("logical-channel = ")
    return ret[1]


def get_lch_config_allocation(session, index):
    module = MODULE
    submodule1 = "logical-channels/channel[index='{}']".format(index)
    submodule2 = "logical-channel-assignments/assignment[index='{}']/config/allocation".format(index)
    xpath = "/{}/{}/{}".format(module, submodule1, submodule2)
    values = make_query(session, xpath)
    if values is None:
        return None
    s = values[0].split("allocation = ")
    return s[1]

def get_lch_config_assignment_type(session, index):
    module = MODULE
    submodule1 = "logical-channels/channel[index='{}']".format(index)
    submodule2 = "logical-channel-assignments/assignment[index='{}']/config/assignment-type".format(index)
    xpath = "/{}/{}/{}".format(module, submodule1, submodule2)
    values = make_query(session, xpath)
    if values is None:
        return None
    s = values[0].split("assignment-type = ")
    return s[1]

def get_ing_config_transceiver(session, index):
    module = MODULE
    submodule = "logical-channels/channel[index='{}']/ingress/config/transceiver".format(index)
    xpath = "/{}/{}".format(module, submodule)
    values = make_query(session, xpath)
    if values is None:
        return None
    s = values[0].split("transceiver = ")
    return s[1]


def get_config_description(session, index):
    module = MODULE
    submodule = "logical-channels/channel[index='{}']/config/description".format(index)
    xpath = "/{}/{}".format(module, submodule)
    values = make_query(session,xpath)
    if values is None:
        return None
    s = values[0].split("description = ")
    return s[1]

