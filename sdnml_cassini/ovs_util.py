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

import subprocess

VSCTL_CMD = "/usr/bin/ovs-vsctl"
OFCTL_CMD = "/usr/bin/ovs-ofctl"


def _run_command(cmd):
    ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ret.returncode > 0:
        raise RuntimeError(ret.stderr.decode("utf-8"))
    else:
        return ret.stdout.decode("utf-8")


def _vsctl_cmd(cmd):
    cmd = [VSCTL_CMD] + cmd
    ret = _run_command(cmd)
    if ret is not None:
        return ret


def add_bridge(name):
    cmd = ["add-br", name]
    return _vsctl_cmd(cmd)


def del_bridge(name):
    cmd = ["del-br", name]
    return _vsctl_cmd(cmd)


def add_port(name, port):
    cmd = ["add-port", name, port]
    return _vsctl_cmd(cmd)


def del_port(name, port):
    cmd = ["del-port", name, port]
    return _vsctl_cmd(cmd)


def set_port_num(port, num):
    cmd = ["set", "interface", port, "ofport_request={}".format(num)]
    return _vsctl_cmd(cmd)


def set_type_port(port, type):
    cmd = ["set", "interface", port, "type={}".format(type)]
    return _vsctl_cmd(cmd)


def set_peer_port(port, peer):
    cmd = ["set", "interface", port, "options:peer={}".format(peer)]
    return _vsctl_cmd(cmd)


def set_freq_port(port, freq):
    cmd = ["set", "port", port, "tag={}".format(freq)]
    return _vsctl_cmd(cmd)


def get_ports(br):
    cmd = ["list-ports", br]
    p = _vsctl_cmd(cmd)
    return p.split()


def is_trunk(port):
    cmd = ["get", "port", port, "trunk"]
    ret = _vsctl_cmd(cmd)
    r = ret.replace("\n", "")
    if r == "[]":
        return False
    return True


def get_tag_port(port):
    cmd = ["get", "port", port, "tag"]
    return _vsctl_cmd(cmd)


def get_trunk_ports(br):
    ports = get_ports(br)
    for i in ports:
        if is_trunk(i):
            return i
    raise RuntimeWarning("there are not trunk ports")


def get_tags_br(br):
    ports = get_ports(br)
    tags = []
    for port in ports:
        if not is_trunk(port):
            tag = get_tag_port(port)
            tags.append(tag.replace("\n", ""))

    if len(tags) == 0:
        raise RuntimeWarning("there are is not tagged ports")
    return tags


def set_trunk_port(trunk, tags):
    cmd = ["set", "port", "{}".format(trunk), "trunks={}".format(",".join(tags))]
    _vsctl_cmd(cmd)


def update_trunk_port(br):
    trunk = get_trunk_ports(br)
    tags = get_tags_br(br)
    set_trunk_port(trunk, tags)


def add_port_patch(name, port, num_port, peer=None):
    try:
        add_port(name, port)
        set_type_port(port, "patch")
        set_peer_port(port, peer)
        set_port_num(port, num_port)
    except Exception as ex:
        raise RuntimeError(ex.__str__())


def list_bridges():
    cmd = ["list-br"]
    v = _vsctl_cmd(cmd)
    br = v.split("\n")
    br.pop((len(br) - 1))
    return br


def exist_bridge(name):
    brs = list_bridges()
    if name in brs:
        return True
    else:
        return False
