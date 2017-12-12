# vsphere-guest-run
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import click
import json
import pkg_resources
from pygments import formatters
from pygments import highlight
from pygments import lexers
import requests
from tabulate import tabulate
from vsphere_guest_run.vsphere import VSphere

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.pass_context
@click.option(
    '-d', '--debug', is_flag=True, default=False, help='Enable debug')
@click.option(
    '-u',
    '--url',
    metavar='<user:pass@host>',
    required=True,
    envvar='VGR_URL',
    help='ESXi or vCenter URL')
@click.option(
    '-s/-i',
    '--verify-ssl-certs/--no-verify-ssl-certs',
    required=False,
    default=True,
    help='Verify SSL certificates')
@click.option(
    '-w',
    '--disable-warnings',
    is_flag=True,
    required=False,
    default=False,
    help='Do not display warnings when not verifying SSL ' + 'certificates')
def vgr(ctx, debug, url, verify_ssl_certs, disable_warnings):
    """vSphere Guest Run

\b
    Run commands and work with files on VM guest OS.
\b
    Examples
        vgr list
            list of VMs.
\b
        vgr run vm-111 /bin/date
            run command on a VM guest OS.
\b
        vgr -i -w run vm-111 '/bin/which uname'
            run command on a VM guest OS.
\b
        vgr -i -w run vm-111 '/bin/uname -a'
            run command on a VM guest OS.
\b
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
    """  # NOQA
    if ctx.invoked_subcommand is None:
        click.secho(ctx.get_help())
        return
    if not verify_ssl_certs:
        if disable_warnings:
            pass
        else:
            click.secho(
                'InsecureRequestWarning: '
                'Unverified HTTPS request is being made. '
                'Adding certificate verification is strongly '
                'advised.',
                fg='yellow',
                err=True)
        requests.packages.urllib3.disable_warnings()
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
    ctx.obj = {}
    ctx.obj['vs'] = vs


@vgr.command(short_help='show info')
@click.pass_context
@click.argument('vm-moid', required=False)
def info(ctx, vm_moid):
    """Show info"""
    vs = ctx.obj['vs']
    vs.connect()
    if vm_moid is None:
        click.secho('URL: %s:*******@%s' % (vs.user, vs.host))
        click.secho('%s' % vs.service_instance.content.about)
    else:
        vm = vs.get_vm_by_moid(vm_moid)
        click.echo(
            highlight(
                json.dumps(vs.vm_to_dict(vm), indent=4, sort_keys=True),
                lexers.JsonLexer(), formatters.TerminalFormatter()))


@vgr.command(short_help='show version')
@click.pass_context
def version(ctx):
    """Show version"""
    ver = pkg_resources.require("vsphere-guest-run")[0].version
    click.secho(ver)


def print_command(cmd, level=0):
    click.echo(' ' + (' ' * level * 2) + ' ', nl=False)
    click.echo(cmd.name)
    if type(cmd) == click.core.Group:
        for k in sorted(cmd.commands.keys()):
            print_command(cmd.commands[k], level + 1)


@vgr.command(short_help='show help')
@click.pass_context
@click.option(
    '-t', '--tree', is_flag=True, default=False, help='show commands tree')
def help(ctx, tree):
    """Show help"""
    if tree:
        print_command(ctx.parent.command)
    else:
        click.secho(ctx.parent.get_help())


@vgr.command(short_help='run command in guest')
@click.pass_context
@click.argument('vm_moid', metavar='<vm-moid>', envvar='VGR_VM_MOID')
@click.option(
    'guest_user',
    '-g',
    '--guest-user',
    metavar='<guest-user>',
    envvar='VGR_GUEST_USER',
    help='Guest OS user name')
@click.option(
    'guest_password',
    '-p',
    '--guest-password',
    metavar='<guest-password>',
    envvar='VGR_GUEST_PASSWORD',
    help='Guest OS password')
@click.option(
    'rm_cmd',
    '-r',
    '--rm',
    default='/bin/rm',
    metavar='<rm-cmd>',
    envvar='VGR_RM_CMD',
    help='rm cmd')
@click.argument('command')
def run(ctx, vm_moid, guest_user, guest_password, command, rm_cmd):
    try:
        vs = ctx.obj['vs']
        vs.connect()
        if vm_moid is None:
            pass
        vm = vs.get_vm_by_moid(vm_moid)
        result = vs.execute_program_in_guest(
            vm,
            guest_user,
            guest_password,
            command,
            wait_for_completion=True,
            wait_time=1,
            get_output=True,
            rm_cmd=rm_cmd)
        stdout = result[1].content.decode()
        stderr = result[2].content.decode()
        if len(stderr) > 0:
            click.secho(stderr, err=True)
        if len(stdout) > 0:
            click.secho(stdout, err=False)
        ctx.exit(result[0])
    except Exception as e:
        import traceback
        traceback.print_exc()
        click.secho(str(e))


@vgr.command('list', short_help='list VMs')
@click.pass_context
def list_cmd(ctx):
    """List VMs"""
    vs = ctx.obj['vs']
    vs.connect()
    vm_data = vs.list_vms()
    headers = ['name', 'moid', 'state']
    table = []
    for vm in vm_data:
        table.append([vm['name'], vm['obj']._moId, vm['guest.guestState']])
    click.secho(tabulate(table, headers=headers))


@vgr.command('run-script', short_help='run script in guest')
@click.pass_context
@click.argument('vm_moid', metavar='<vm-moid>', envvar='VGR_VM_MOID')
@click.argument(
    'script-file',
    type=click.Path(exists=True),
    metavar='<script-file>',
    required=True)
@click.option(
    'guest_user',
    '-g',
    '--guest-user',
    metavar='<guest-user>',
    envvar='VGR_GUEST_USER',
    help='Guest OS user name')
@click.option(
    'guest_password',
    '-p',
    '--guest-password',
    metavar='<guest-password>',
    envvar='VGR_GUEST_PASSWORD',
    help='Guest OS password')
@click.option(
    'rm_cmd',
    '-r',
    '--rm',
    default='/bin/rm',
    metavar='<rm-cmd>',
    envvar='VGR_RM_CMD',
    help='rm cmd')
def run_script(ctx, vm_moid, script_file, guest_user, guest_password, rm_cmd):
    try:
        vs = ctx.obj['vs']
        vs.connect()
        if vm_moid is None:
            pass
        vm = vs.get_vm_by_moid(vm_moid)
        with open(script_file, 'r') as f:
            content = f.read()
        result = vs.execute_script_in_guest(
            vm,
            guest_user,
            guest_password,
            content,
            target_file=None,
            wait_for_completion=True,
            wait_time=1,
            get_output=True,
            rm_cmd=rm_cmd)
        stdout = result[1].content.decode()
        stderr = result[2].content.decode()
        if len(stderr) > 0:
            click.secho(stderr, err=True)
        if len(stdout) > 0:
            click.secho(stdout, err=False)
        ctx.exit(result[0])
    except Exception as e:
        import traceback
        traceback.print_exc()
        click.secho(str(e))


if __name__ == '__main__':
    vgr()
