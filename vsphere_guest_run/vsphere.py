# vsphere-guest-run
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from pyVim import connect
import pyVmomi
from pyVmomi import vim
import requests
import ssl
import time
import uuid

RM_CMD = '/bin/rm'


class VSphere(object):
    def __init__(self, host, user, password, verify=True, port=443):
        self.host = host
        self.user = user
        self.password = password
        self.verify = verify
        self.port = port

    def connect(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        if not self.verify:
            context.verify_mode = ssl.CERT_NONE
        self.service_instance = connect.SmartConnect(
            host=self.host,
            user=self.user,
            pwd=self.password,
            sslContext=context)

    def get_vm_by_moid(self, moid):
        vm = vim.VirtualMachine(moid)
        vm._stub = self.service_instance._stub
        return vm

    def vm_to_dict(self, vm):
        result = {}
        result['name'] = vm.name
        result['moid'] = vm._moId
        result['config.hardware.numCPU'] = vm.config.hardware.numCPU
        result['config.hardware.memoryMB'] = vm.config.hardware.memoryMB
        result['config.guestFullName'] = vm.config.guestFullName
        result['config.version'] = vm.config.version
        result['config.uuid'] = vm.config.uuid
        result['config.guestId'] = vm.config.guestId
        result['guest.guestState'] = vm.guest.guestState
        result['guest.toolsRunningStatus'] = vm.guest.toolsRunningStatus
        return result

    def execute_program_in_guest(self,
                                 vm,
                                 user,
                                 password,
                                 command,
                                 wait_for_completion=False,
                                 wait_time=1,
                                 get_output=True,
                                 rm_cmd=RM_CMD,
                                 callback=None):
        tokens = command.split()
        program_path = tokens.pop(0)
        arguments = ''
        for token in tokens:
            arguments += ' %s' % token

        if get_output:
            file_uuid = uuid.uuid1()
            stdout_file = '/tmp/%s.out' % file_uuid
            stderr_file = '/tmp/%s.err' % file_uuid
            arguments += ' > %s 2> %s' % (stdout_file, stderr_file)
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        pm = content.guestOperationsManager.processManager
        ps = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=program_path, arguments=arguments)
        result = pm.StartProgramInGuest(vm, creds, ps)
        if not wait_for_completion:
            return [result]
        n = 0
        while True:
            try:
                processes = pm.ListProcessesInGuest(vm, creds, [result])
                if processes[0].exitCode is not None:
                    result = [processes[0].exitCode]
                    if get_output:
                        r = self.download_file_from_guest(
                            vm, user, password, stdout_file)
                        result.append(r)
                        r = self.download_file_from_guest(
                            vm, user, password, stderr_file)
                        result.append(r)
                        try:
                            ps = vim.vm.guest.ProcessManager.ProgramSpec(
                                programPath=rm_cmd,
                                arguments='-rf /tmp/%s.*' % file_uuid)
                            r = pm.StartProgramInGuest(vm, creds, ps)
                        except Exception as e:
                            if callback is not None:
                                callback('exception', e)
                            else:
                                print(str(e))
                    if callback is not None:
                        callback('process %s finished, exit code: %s' %
                                 (result, processes[0].exitCode))
                    return result
                else:
                    if callback is not None:
                        n += 1
                        callback('waiting for process %s to finish (%s)' %
                                 (result, n))
                    time.sleep(wait_time)
            except Exception as e:
                if callback is not None:
                    callback('exception, will retry in a few seconds', e)
                else:
                    print(str(e))
                    print('will retry again in a few seconds')
                time.sleep(wait_time * 3)

    def upload_file_to_guest(self, vm, user, password, data, target_file):
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        url = content.guestOperationsManager.fileManager. \
            InitiateFileTransferToGuest(vm,
                                        creds,
                                        target_file,
                                        file_attribute,
                                        len(data),
                                        False)
        resp = requests.put(url, data=data, verify=False)
        if not resp.status_code == 200:
            raise Exception(
                'Error while uploading file: %s' % resp.status_code)
        else:
            return True

    def download_file_from_guest(self, vm, user, password, source_file):
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        info = content.guestOperationsManager.fileManager. \
            InitiateFileTransferFromGuest(vm,
                                          creds,
                                          source_file)
        return requests.get(info.url, verify=False)

    def list_files_in_guest(self, vm, user, password, file_path, pattern):
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        return content.guestOperationsManager.fileManager. \
            ListFilesInGuest(vm,
                             creds,
                             file_path,
                             index=0,
                             maxResults=1000,
                             matchPattern=pattern)

    def move_file_in_guest(self, vm, user, password, src_file_path,
                           trg_file_path, overwrite):
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        content.guestOperationsManager.fileManager.MoveFileInGuest(
            vm, creds, src_file_path, trg_file_path, overwrite)

    def delete_file_in_guest(self, vm, user, password, file_path):
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=user, password=password)
        content = self.service_instance.RetrieveContent()
        content.guestOperationsManager.fileManager. \
            DeleteFileInGuest(vm, creds, file_path)

    def execute_script_in_guest(self,
                                vm,
                                user,
                                password,
                                content,
                                target_file=None,
                                wait_for_completion=False,
                                wait_time=1,
                                get_output=True,
                                delete_script=True,
                                rm_cmd=RM_CMD,
                                callback=None):
        target = target_file
        if target is None:
            target = '/tmp/%s.sh' % uuid.uuid1()
        self.upload_file_to_guest(vm, user, password, content, target)
        cmd = '/bin/chmod u+rx %s' % target
        self.execute_program_in_guest(
            vm, user, password, cmd, wait_for_completion=True)
        result = self.execute_program_in_guest(
            vm,
            user,
            password,
            target,
            wait_for_completion=wait_for_completion,
            wait_time=wait_time,
            get_output=get_output,
            rm_cmd=rm_cmd,
            callback=callback)
        if wait_for_completion and delete_script:
            self.delete_file_in_guest(vm, user, password, target)
        return result

    def list_vms(self):
        vm_properties = [
            "name", "config.uuid", "config", "config.hardware.numCPU",
            "config.hardware.memoryMB", "guest.guestState",
            "config.guestFullName", "config.guestId", "config.version"
        ]
        content = self.service_instance.RetrieveContent()
        view = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True)
        vm_data = self.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties,
            include_mors=True)
        return vm_data

    # Shamelessly borrowed from:
    # https://github.com/dnaeon/py-vconnector/blob/master/src/vconnector/core.py
    def collect_properties(self,
                           view_ref,
                           obj_type,
                           path_set=None,
                           include_mors=False):
        collector = self.service_instance.content.propertyCollector

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = pyVmomi.vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        # Create a traversal specification to identify the path for collection
        traversal_spec = pyVmomi.vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

        # Identify the properties to the retrieved
        property_spec = pyVmomi.vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type

        if not path_set:
            property_spec.all = True

        property_spec.pathSet = path_set

        # Add the object and property specification to the
        # property filter specification
        filter_spec = pyVmomi.vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val

            if include_mors:
                properties['obj'] = obj.obj

            data.append(properties)
        return data

    def wait_until_tools_ready(self, vm, sleep=5, callback=None):
        while True:
            try:
                status = vm.guest.toolsRunningStatus
                callback(status)
                if 'guestToolsRunning' == status:
                    return
                time.sleep(sleep)
            except Exception as e:
                callback('exception', exception=e)
                time.sleep(sleep)
