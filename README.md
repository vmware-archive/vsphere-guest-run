
# vsphere-guest-run

[![Latest Version](https://img.shields.io/pypi/v/vsphere-guest-run.svg)](https://pypi.python.org/pypi/vsphere-guest-run)
[![Build Status](https://img.shields.io/travis/vmware/vsphere-guest-run.svg?style=flat)](https://travis-ci.org/vmware/vsphere-guest-run)


## Overview

**vsphere-guest-run** enables executing programs in the guest operating system of virtual machines running on vSphere. It also enables working with directories and files. It uses the **vSphere Guest Operations API** (via [pyVmomi](https://github.com/vmware/pyvmomi)), and therefore network connectivity to the virtual machine is not required. vCenter and guest OS credentials are required. It is distributed as a package with a Python library and CLI.

## Documentation

See the [docs](docs/README.md).

## Contributing

The **vsphere-guest-run** project team welcomes contributions from the community. Before you start working with **vsphere-guest-run**, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on as an open-source patch. For more detailed information, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[BSD-2](LICENSE.txt)
