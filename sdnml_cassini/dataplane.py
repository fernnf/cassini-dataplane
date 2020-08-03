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

import sysrepo as sr

from sdnml_cassini import init_logger as log
from sdnml_cassini import ovs_util as ovs


class CassiniDataPlane(object):
	def __init__(self):
		self.logger = log("CassiniDataPlane")
		self.context = "CassiniDataPlane"
		self.conn = sr.Connection(self.context)
		self.sess = sr.Session(self.conn, sr.SR_DS_RUNNING)
		self.subscribe = sr.Subscribe(self.sess)

	def print_change(self, op, old_val, new_val):
		if (op == sr.SR_OP_CREATED):
			self.logger.info("CREATED: {}".format(new_val.to_string()))
		elif (op == sr.SR_OP_DELETED):
			self.logger.info("DELETED: {}".format(old_val.to_string()))
		elif (op == sr.SR_OP_MODIFIED):
			self.logger.info("MODIFIED: old ({}) to new ({})".format(old_val.to_string(), new_val.to_string()))
		elif (op == sr.SR_OP_MOVED):
			self.logger.info("MOVED: ({}) to ({})".format(old_val.xpath(), new_val.xpath()))

	def get_attributes(self, xpath):
		tmp = xpath.rsplit("/", maxsplit=3)
		n = tmp[3].split(" = ")[0].strip()
		v = tmp[3].split(" = ")[1].strip()
		i = tmp[0].split("'")[1].strip()
		return i, n, v

	def change_trcv_frequency(self, new):
		pass

	def module_openconfig_plataform_module(self):
		pass

	def reach_function(self, oper, old, new):
		if (oper == sr.SR_OP_MODIFIED):
			self.logger.info("New modification on frequency transceiver")
			i, n, v = self.get_attributes(new.to_string())
			self.logger.info("{} {} {}".format(i, n, v))
			if n.__eq__("frequency"):
				self.logger.info("Changing vlan")
				freq, vlan = self.get_frequency_vlan(i)
				self.logger.info("{} {} {}".format(i, freq, vlan))
				try:
					ovs.set_freq_port(i, vlan)
					trcv = i.split("/")[0]
					ovs.update_trunk_port(trcv)
					self.logger.info("the frequency was changed")
				except Exception as ex:
					self.logger.warning(ex)

	def ev_to_str(self, ev):
		if (ev == sr.SR_OP_CREATED):
			return "CREATED"
		elif (ev == sr.SR_OP_MODIFIED):
			return "MODIFIED"
		elif (ev == sr.SR_OP_DELETED):
			return "DELETED"
		elif (ev == sr.SR_OP_MOVED):
			return "MOVED"
		else:
			return None

	def module_cb(self, sess, module_name, event, private_ctx):
		xpath = "/" + module_name + ":*//*"
		it = sess.get_changes_iter(xpath)
		self.logger.info("New {} event   reached".format(self.ev_to_str(event)))
		while True:
			change = sess.get_change_next(it)
			if change == None:
				break
			if (event == sr.SR_OP_CREATED):
				self.logger.info("New event was reached type CREATED")
			if (event == sr.SR_OP_MODIFIED):
				self.logger.info("applying new changes on dataplane")
				self.reach_function(change.oper(), change.old_val(), change.new_val())

		return sr.SR_ERR_OK

	def init(self):
		self.print_banner()
		self.logger.info("Initializing emulate cassini dataplane")
		self.logger.info("Verifying sysrepo inventory repository")
		s = self.sess.list_schemas()
		if s is None:
			self.logger.error("Sysrepo not found")
			exit(2)
		else:
			self.logger.info("Sysrepo was found")
		self.logger.info("Retrieving data of repository")
		self.create_phy_interfaces()
		self.create_logical_interfaces()
		self.logger.info("Registering events")
		try:
			module = "openconfig-platform"
			self.subscribe.module_change_subscribe(module, self.module_cb)
			self.logger.info("Waiting events")
			sr.global_loop()
			self.logger.warning("Application exit requested, exiting.\n")
		finally:
			self.delete_phy_interfaces()

	def print_banner(self):
		import pyfiglet as fl
		banner = fl.figlet_format("Cassini Dataplane")
		print(banner)
		print("Project: SDN-Multilayer (c) 2020 National Network for Education and Research (RNP)\n")

	def make_query(self, xpath, multi=False):
		def query_item():
			values = self.sess.get_item(xpath)
			if values is None:
				return None
			ret = []
			ret.append(values.to_string().rstrip("\n"))
			return ret

		def query_items():
			values = self.sess.get_items(xpath)
			if values is None:
				raise RuntimeError("Query Error or None")
			ret = []
			for i in range(values.val_cnt()):
				v = values.val(i)
				s = v.to_string().rstrip("\n")
				ret.append(s)

			return ret

		if multi:
			return query_items()
		else:
			return query_item()

	def get_logical_interfaces(self):
		xpath = "/openconfig-terminal-device:terminal-device//channel[node()]/index"
		values = self.make_query(xpath, multi=True)
		ret = []
		for v in values:
			s = v.split("index = ")
			ret.append(s[1])
		return ret

	def get_phy_interfaces(self):
		xpath = "/openconfig-platform:components//component[node()]/name"
		values = self.make_query(xpath, multi=True)
		ret = []
		for v in values:
			s = v.split("name = ")
			if "/" not in s[1]:
				ret.append(s[1])
		return ret

	def create_phy_interfaces(self):
		self.logger.info("Getting physical interfaces")
		interfaces = self.get_phy_interfaces()
		self.logger.info("New {} interfaces was found".format(len(interfaces)))
		try:
			for i in interfaces:
				self.logger.info("Adding physical interface ({})".format(i))
				ovs.add_bridge(i)
			self.logger.info("The physical interfaces were created")
		except Exception as ex:
			self.logger.error(ex.__str__())

	def delete_phy_interfaces(self):
		self.logger.info("Deleting physical interfaces")
		interfaces = self.get_phy_interfaces()
		try:
			for i in interfaces:
				self.logger.info("Deleting physical interface ({})".format(i))
				ovs.del_bridge(i)
			self.logger.info("The physical interfaces were deleted")
		except Exception as ex:
			self.logger.error(ex.__str__())

	def create_phy_interface(self, interface):
		self.logger.info("Creating ({}) physical interface".format(interface))
		try:
			ovs.add_bridge(interface)
			self.logger.info("Physical interface {} was created".format(interface))
		except Exception as ex:
			self.logger.error(ex.__str__())

	def delete_phy_interface(self, interface):
		self.logger.info("Deleting ({}) physical interface".format(interface))
		try:
			ovs.del_bridge(interface)
			self.logger.info("Physical interface {} was deleted".format(interface))
		except Exception as ex:
			self.logger.error(ex.__str__())

	def get_logical_description(self, index):
		xpath = "/openconfig-terminal-device:terminal-device//channel[index='{}']/config/description".format(index)
		values = self.make_query(xpath)
		s = values[0].split("description = ")
		return s[1]

	def get_logical_transceiver(self, index):
		xpath = "/openconfig-terminal-device:terminal-device/logical-channels/channel[index='{}']/ingress/config/transceiver".format(index)
		values = self.make_query(xpath)
		if values is None:
			return None
		s = values[0].split("transceiver = ")
		return s[1]

	def get_logical_type(self, desc):
		xpath = "/openconfig-platform:components/component[name='{}']/state/type".format(desc)
		values = self.make_query(xpath)
		if values is None:
			return None
		s = values[0].split("type = ")
		t = s[1].split(":")
		return t[1]

	def get_logical_channel(self, index):
		xpath = "/openconfig-terminal-device:terminal-device/logical-channels/channel[index='{i}']/logical-channel-assignments/assignment[index='{i}']/config/logical-channel".format(i=index)
		values = self.make_query(xpath)
		s = values[0].split("logical-channel = ")
		return s[1]

	def create_logical_channel(self, i):
		desc = self.get_logical_description(i)
		type = self.get_logical_type(desc)
		if type is None:
			self.logger.info("Creating logical channel ({}) interface".format(desc))
			trcv = self.get_logical_transceiver(i)
			self.logger.info("{}".format(trcv))
			if ovs.exist_bridge(trcv):
				ovs.add_port_patch(trcv, desc, i, peer="none")
				self.logger.info("Logical channel interface ({}) was created".format(desc))
			else:
				raise RuntimeError("Transceiver ({}) not was created or found".format(desc))
		elif type == "OPTICAL_CHANNEL":
			self.logger.info("Creating optical channel ({})".format(desc))
			v = desc.split("/")
			trcv = v[0]
			if ovs.exist_bridge(trcv):
				ovs.add_port_patch(trcv, desc, i, peer="none")
				freq, vlan = self.get_frequency_vlan(desc)
				if (freq and vlan) is not None:
					self.logger.info("Mapping vlan {} as frequency {}Ghz on port {}".format(vlan, freq, desc))
					ovs.set_freq_port(desc, vlan)
				self.logger.info("Optical channel interface ({}) was created".format(desc))
			else:
				raise RuntimeError("Transceiver ({}) not was created or found")
		else:
			self.logger.warn("Type not found")

	def create_logical_assignment(self, i):
		self.logger.info("Creating logical assignment")
		desc = self.get_logical_description(i)
		type = self.get_logical_type(desc)
		if type is None:
			if self.exist_channel_assignments(i):
				peer_index = self.get_logical_channel(i)
				peer = self.get_logical_description(peer_index)
				ovs.set_peer_port(desc, peer)
				ovs.set_peer_port(peer, desc)
				self.logger.info("It has created a assignment from ({}) to ({})".format(desc, peer))
			else:
				self.logger.info("there is not assignment to ({})".format(desc))
		else:
			self.logger.warn("Type not found")

	def create_logical_interfaces(self):
		self.logger.info("Creating logical interfaces")
		interfaces = self.get_logical_interfaces()
		for i in interfaces:
			self.create_logical_channel(i)
		for i in interfaces:
			self.create_logical_assignment(i)
		self.logger.info("Logical and optical interfaces have created with successful")

	def exist_channel_assignments(self, index):
		xpath = "/openconfig-terminal-device:terminal-device/logical-channels/channel[index='{}']/logical-channel-assignments//*".format(index)
		values = self.sess.get_items(xpath)
		if values is None:
			return False
		else:
			return True

	def change_frequency_vlan(self, ifname):
		freq, vlan = self.get_frequency_vlan(ifname)
		self.logger.info("Change frequency Transceiver to {}GHZ".format(freq))
		ovs.set_freq_port(ifname, vlan)
		self.logger.info("Created mapping of vlan {} as frequency {}Ghz on port {}".format(vlan, freq, ifname))

	def get_frequency_vlan(self, ifname):
		xpath = "/openconfig-platform:components/component[name='{}']/openconfig-terminal-device:optical-channel/config/frequency".format(ifname)
		values = self.make_query(xpath)
		s = values[0].split("frequency = ")
		f = s[1]
		v = None
		if f is not None:
			v = self.convert_freq_vlan(f.strip())
			return f, v
		return f, v

	def convert_freq_vlan(self, freq):
		f = int(freq)

		v = (f * 0.0001 - 19000)
		return (int(v))


if __name__ == '__main__':
	cassini = CassiniDataPlane()
	cassini.init()
