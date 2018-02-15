#!/usr/bin/env python3

import os
import sys

from vsphere_guest_run.vsphere import VSphere

url = os.environ['VGR_URL']
verify_ssl_certs = False
moid = os.environ['VGR_MOID']
guest_user = os.environ['VGR_GUEST_USER']
guest_password = os.environ['VGR_GUEST_PASSWORD']
if len(sys.argv) < 2:
    print('usage: run-cmd.py \'program to run on guest with arguments\'')
    sys.exit()
vgr_command = sys.argv[1]

tokens = url.split(':')
vc_user = tokens[0]
tokens = tokens[1].split('@')
vc_host = tokens[-1]
vc_password = ''
for token in tokens[:-1]:
    if len(vc_password) > 0:
        vc_password += '@'
    vc_password += token
vs = VSphere(vc_host, vc_user, vc_password, verify=verify_ssl_certs)
vs.connect()
vm = vs.get_vm_by_moid(moid)
result = vs.execute_program_in_guest(
            vm,
            guest_user,
            guest_password,
            vgr_command,
            get_output=False,
            wait_for_completion=False)
print(result)
