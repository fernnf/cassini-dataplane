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
import os
from sdnm_cassini import init_logger as log
from sdnm_cassini import ovsctl
import sdnm_cassini.terminal_device as td
import sdnm_cassini.platform as pl
from sdnm_cassini.utils import convert_freq_vlan


class CassiniDataPlane(object):

	MOD_PLATAFORM = "openconfig-platform"
	MOD_TERM_DEV = "openconfig-terminal-device"

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

	def reach_function(self, oper, old, new):
		module = str(new.to_string()).replace("\n", "")
		self.logger.info("New modification on repository modules")
		if module.startswith("/openconfig-platform"):
			self.logger.info("Modification on module ({})".format("openconfig-platform"))
			if module.find("frequency"):
				self.logger.info("Modification on submodule ({})".format("frequency"))
				o = old.to_string().replace("\n", "")
				n = new.to_string().replace("\n", "")
				self.update_frequency(o,n)
		elif module.startswith("/openconfig-terminal-device"):
			self.logger.info("Modification on module ({})".format("openconfig-terminal-device"))
			if module.find("logical-channel"):
				self.update_assignment(old.to_string(), new.to_string())
		else:
			self.logger.info("Modules not found")

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
		self.logger.info("New {} event reached".format(self.ev_to_str(event)))
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
		self.logger.info("Initializing cassini dataplane")
		self.logger.info("Discovering Sysrepo repository")
		s = self.sess.list_schemas()
		if s is None:
			self.logger.error("Sysrepo not found")
			self.logger.info("Existing application")
			exit(2)
		else:
			self.logger.info("Sysrepo was found")
		self.logger.info("Retrieving data of repository")
		self.add_phy_interfaces()
		self.add_logical_interfaces()
		self.logger.info("Registering events")
		try:

			self.subscribe.module_change_subscribe(self.MOD_PLATAFORM, self.module_cb)
			self.subscribe.module_change_subscribe(self.MOD_TERM_DEV, self.module_cb)
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


	def add_phy_interfaces(self):
		self.logger.info("Getting physical interfaces")
		interfaces = pl.get_component_config_name(self.sess)
		self.logger.info("New {} interfaces was found".format(len(interfaces)))
		try:
			for i in interfaces:
				self.create_interface(i)
			self.logger.info("All interfaces were created")
		except Exception as ex:
			self.logger.error(ex)

	def delete_phy_interfaces(self):
		self.logger.info("Deleting physical interfaces")
		interfaces = pl.get_component_config_name(self.sess)
		self.logger.info("{} interfaces was found".format(len(interfaces)))
		try:
			for i in interfaces:
				self.delete_interface(i)
			self.logger.info("The all interfaces were deleted")
		except Exception as ex:
			self.logger.error(ex)

	def create_interface(self, name):
		self.logger.info("Creating {} interface".format(name))
		try:
			ovsctl.add_bridge(name)
			self.logger.info("Interface {} was created".format(name))
		except Exception as ex:
			self.logger.error(ex)

	def delete_interface(self, name):
		self.logger.info("Deleting ({}) interface".format(name))
		try:
			ovsctl.del_bridge(name)
			self.logger.info("Intupdate_fequencieserface {} was deleted".format(name))
		except Exception as ex:
			self.logger.error(ex)

	def add_logical_interfaces(self):
		self.logger.info("Creating logical interfaces")
		interfaces = td.get_index_interfaces(self.sess)
		for i in interfaces:
			self.enable_logical_channel(i)
		for i in interfaces:
			self.enable_assignments_channels(i)
		self.logger.info("Logical interfaces was created with successful")

	def enable_logical_channel(self, i):
		desc = td.get_config_description(self.sess, i)
		type = td.get_lch_config_assignment_type(self.sess, i)
		self.logger.info("{}".format(type))
		if type.__eq__("LOGICAL_CHANNEL"):
			self.logger.info("Creating a {} {} interface".format(type, desc))
			br = td.get_ing_config_transceiver(self.sess, i)
			if br is not None:
				ovsctl.add_port_patch(br, desc, i, peer="none")
				self.logger.info(" {} {} was created".format(type, desc))
			else:
				raise RuntimeError("Transceiver not was found")
		elif type.__eq__("OPTICAL_CHANNEL"):
			self.logger.info("Creating a {} {} interface".format(type, desc))
			br = td.get_ing_config_transceiver(self.sess, i)
			if br is not None:
				ovsctl.add_port_patch(br, desc, i, peer="none")
				freq, vlan = pl.get_config_frequency_vlan(self.sess, desc)
				self.logger.info("Mapping vlan {} as frequency {}Ghz on port {}".format(vlan, freq, desc))
				ovsctl.set_vlan_port(desc,vlan)
				self.logger.info("{} {} was created".format(type, desc))
			else:
				raise RuntimeError("Transceiver not was found")
		else:
			raise RuntimeError("Type assignment not found")

	def enable_assignments_channels(self, i):
		self.logger.info("Creating assignments existed")
		name = td.get_config_description(self.sess, i)
		type = td.get_lch_config_assignment_type(self.sess, i)
		if type.__eq__("LOGICAL_CHANNEL"):
			peer_idx = td.get_lch_config_logical_channel(self.sess, i)
			if not peer_idx.__eq__("0"):
				peer = td.get_config_description(self.sess, peer_idx)
				ovsctl.set_peer_port(name, peer)
				ovsctl.set_peer_port(peer, name)
				self.logger.info("It was created new an assignment between {} and {}".format(name, peer))
			else:
				self.logger.info("there is no assignment to configure")
		else:
			self.logger.info("the port is a OPTICAL_CHANNEL")

	def update_frequency(self, old, new):

		def get_values(m):
			frq = m.rsplit("/", 3)[3].split("=")[1].strip()
			intf = m.rsplit("/", 3)[0].split("=")[1].split("]")[0].replace("'", "")
			vlan = convert_freq_vlan(frq)
			return frq, intf, vlan

		try:
			o = get_values(old)
			n = get_values(new)
			ovsctl.set_vlan_port(n[1], n[2])
			self.logger.info("optical frequency was modified {} GHz to {} GHz".format(o[0], n[0]))
			self.logger.info("vlan was modified of {} to {}".format(o[2], n[2]))
		except Exception as ex:
			self.logger.error(ex)

	def update_assignment(self, old, new):
		def get_values(m):
			d = m.rsplit("/", 4)[4].split(" = ")[1].strip()
			s = m.rsplit("/", 4)[2].split("=")[1].split("]")[0].replace("'", "").strip()
			self.logger.info("s{} d{}".format(s, d))
			src = td.get_config_description(self.sess, s)
			if src is None:
				raise ValueError("the source interface index {} not found".format(s))
			dst = td.get_config_description(self.sess, d)
			if dst is None:
				raise ValueError("the destination interface index {} not found".format(d))
			return src , dst

		try:
			osrc, odst = get_values(old)
			src, dst = get_values(new)
			ovsctl.set_peer_port(osrc, "none")
			ovsctl.set_peer_port(odst, "none")
			ovsctl.set_peer_port(src, dst)
			ovsctl.set_peer_port(dst, src)
			self.logger.info("the logical channel assignment was modified {}<->{} to {}<->{}".format(osrc, odst, src, dst))
		except Exception as ex:
			self.logger.error(ex)
