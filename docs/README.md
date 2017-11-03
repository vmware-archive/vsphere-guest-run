```shell
$ vgr
Usage: vgr [OPTIONS] COMMAND [ARGS]...

  vSphere Guest Run

      Run commands on VM guest OS.

      Examples
          vgr list
              list of VMs.

          vgr run vm-111 /bin/date
              run command on a VM guest OS.

          vgr -i -w run vm-111 '/bin/uname -a'
              run command on a VM guest OS.

      Environment Variables
          VGR_URL
              If this environment variable is set, the command will use its value
              as the URL to login on the vCenter or ESXi. The --url
              option has precedence over the environment variable. The format for
              the URL is: 'user:pass@host'
          VGR_GUEST_USER
              If this environment variable is set, the command will use its value
              as the user to login on the guest. The --guest-user
              option has precedence over the environment variable.
          VGR_GUEST_PASSWORD
              If this environment variable is set, the command will use its value
              as the password to login on the guest. The --guest-password
              option has precedence over the environment variable.


Options:
  -d, --debug                     Enable debug
  -u, --url <user:pass@host>      ESXi or vCenter URL  [required]
  -s, --verify-ssl-certs / -i, --no-verify-ssl-certs
                                  Verify SSL certificates
  -w, --disable-warnings          Do not display warnings when not verifying
                                  SSL certificates
  -h, --help                      Show this message and exit.

Commands:
  help     show help
  info     show info
  list     list VMs
  run      run command in guest
  version  show version

$ export VGR_URL='administrator@vsphere.local:Welcome@123@vcenter.eng.vmware.com'

$ vgr list
name                                            moid    state
----------------------------------------------  ------  ----------
disk1 (91b3a2e2-fd02-412b-9914-9974d60b2351)    vm-363  notRunning
ubu1 (6f31ed4b-5b64-41c7-bbaa-3a64e695f425)     vm-361  notRunning
csetmpu (deb8dd18-e7d6-45f2-94d6-84b71f1197d0)  vm-348  running
ubu1 (eaccd602-b891-437b-a99b-7e2fe78e1166)     vm-346  running
csetmpu (c840e9a7-27b9-48ec-a327-ed63607ff4e4)  vm-312  notRunning
csetmp (5d51a087-0e6d-40e5-b757-13a4088f58fc)   vm-40   notRunning
csetmp (5aedeca9-5c9b-4a63-8110-d7d59578fa14)   vm-37   notRunning
ubu1 (632063e8-f375-498a-acf0-385ee3318602)     vm-357  notRunning
csetmpu (ee9197cf-f4e2-48d5-aaab-cc41b823d277)  vm-315  notRunning
ph1 (795d6e82-eb14-41cb-ae2a-ff390b4f174d)      vm-232  running
Photon (e851fe44-2cee-4d57-8a2d-4fc272f14828)   vm-33   notRunning

$ export VGR_GUEST_USER=root

$ export VGR_GUEST_PASSWORD='pA!9#6$f'

$ vgr info vm-346
{
    "config.guestFullName": "Ubuntu Linux (64-bit)",
    "config.guestId": "ubuntu64Guest",
    "config.hardware.memoryMB": 2048,
    "config.hardware.numCPU": 2,
    "config.uuid": "4208c56c-0209-425d-cbc1-408419364edc",
    "config.version": "vmx-10",
    "guest.guestState": "running",
    "moid": "vm-346",
    "name": "ubu1 (eaccd602-b891-437b-a99b-7e2fe78e1166)"
}

$ vgr -w -i run vm-346 '/usr/bin/which hostname'
/bin/hostname

$ vgr -w -i run vm-346 /bin/hostname
ubu1
```
