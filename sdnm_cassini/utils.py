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

def make_query(session, xpath, multi=False):
    def query_item():
        values = session.get_item(xpath)
        if values is None:
            return None
        ret = []
        ret.append(values.to_string().rstrip("\n"))
        return ret.copy()

    def query_items():
        values = session.get_items(xpath)
        if values is None:
            raise RuntimeError("Query Error or None")
        ret = []
        for i in range(values.val_cnt()):
            v = values.val(i)
            s = v.to_string().rstrip("\n")
            ret.append(s)

        return ret.copy()

    if multi:
        return query_items()
    else:
        return query_item()


def convert_freq_vlan(freq):
    if freq is "0":
        return "0"
    f = int(freq)
    v = (f * 0.0001 - 19000)
    return (int(v))