#!/usr/bin/env python

"""
Converts between cluster.txt and cluster.yaml. cluster.yaml carries more
information than cluster.txt, so converting from cluster.yaml to cluster.txt
will discard information.

cluster.yaml schema example:

cluster_name: TEST
nodes:
  fake-node-r06n01:
    domain: completelyfake.example
    hardware_type: null
    ip_address: 131.81.229.220
    ipmi_address: 62.185.178.18
    ipmi_username: meep
    ipmi_password: moop
    mac_address: 21:b0:d5:9b:f8:3b
    role: bootstrap
  [...]
    fake-node-r06n02:
    domain: completelyfake.example
    hardware_type: null
    ip_address: 127.228.36.77
    ipmi_address: 218.161.198.210
    ipmi_username: beep
    ipmi_password: boop
    mac_address: 18:c2:93:42:a5:cd
    role: work
"""

import argparse
import os
import sys
import yaml


def to_yaml(path, cluster_name, hardware_type, ipmi_username, ipmi_password):
    """
    Opens and reads the given file, which is assumed to be in cluster.txt
    format. Returns a string with cluster.txt converted to YAML or dies trying.
    """
    f = open(path)
    cluster_txt = f.readlines()
    f.close()

    cluster = {'cluster_name': cluster_name, 'nodes': {}}

    for line in cluster_txt:
        if line.strip() == "end":
            break
        try:
            name, mac, ip, ipmi, domain, role = line.strip().split()
        except ValueError, e:
            err = "ERROR: failure unpacking line '%s' into 6 values: %s. "
            err += "Is this a valid cluster.txt file? Exiting."
            sys.exit(err % (line.strip(), e))
        if name in cluster['nodes']:
            sys.exit("ERROR: %s found more than once in cluster.txt" % name)
        if ipmi == "-":
            ipmi = None
        cluster['nodes'][name] = {
            'mac_address': mac,
            'ip_address': ip,
            'ipmi_address': ipmi,
            'ipmi_username': ipmi_username,
            'ipmi_password': ipmi_password,
            'domain': domain,
            'role': role,
            'hardware_type': hardware_type,
            'cobbler_profile': 'bcpc_host',
        }

    return yaml.dump(cluster, default_flow_style=False)


def to_text(path):
    """
    Opens and reads the given file, which is assumed to be YAML.
    Returns a string with cluster.yaml converted to text, or dies trying.
    """
    f = open(path)
    cluster_yaml = f.read()
    f.close()

    cluster = yaml.safe_load(cluster_yaml)
    # if it's a string and not a dict, something not YAML was loaded
    if type(cluster) != dict:
        sys.exit("ERROR: %s did not parse as YAML. Exiting." % path)

    buf = ""

    for node in sorted(cluster['nodes'].keys()):
        if cluster['nodes'][node]['ipmi_address'] is None:
            ipmi_address = "-"
        else:
            ipmi_address = cluster['nodes'][node]['ipmi_address']

        line = "%s %s %s %s %s %s\n" % (
            node,
            cluster['nodes'][node]['mac_address'],
            cluster['nodes'][node]['ip_address'],
            ipmi_address,
            cluster['nodes'][node]['domain'],
            cluster['nodes'][node]['role']
        )
        buf += line

    buf += "end"
    return buf


def main():
    parser = argparse.ArgumentParser(
        description='Converts between cluster.txt and cluster.yaml. '
        'Text to YAML is the default direction. Specify -t to go from '
        'YAML to text. The YAML format contains more information than '
        'the text format, so information will be lost when converting '
        'to text.')
    parser.add_argument("path", help="path to cluster.txt")
    parser.add_argument("cluster_name", help="name of cluster")
    parser.add_argument(
        "-t", "--text",
        help="convert from YAML to text (THIS WILL DISCARD DATA)",
        action="store_true")
    parser.add_argument(
        "-H", "--hardware_type",
        default=None,
        help="chef hardware role name")
    parser.add_argument(
        "-U", "--ipmi_username",
        default=None,
        help="IPMI username")
    parser.add_argument(
        "-P", "--ipmi_password",
        default=None,
        help="IPMI password")

    args = parser.parse_args()

    if not os.path.exists(args.path) or not os.access(args.path, os.R_OK):
        sys.exit("ERROR: Unable to open %s" % args.path)

    if args.text:
        print(to_text(args.path))
    else:
        print(to_yaml(args.path, 
                      args.cluster_name,
                      args.hardware_type,
                      args.ipmi_username,
                      args.ipmi_password))


if __name__ == "__main__":
    main()
