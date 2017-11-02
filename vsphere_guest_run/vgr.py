# vsphere-guest-run
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import click
import pkg_resources
from vsphere_guest_run.vsphere import VSphere


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group(context_settings=CONTEXT_SETTINGS,
             invoke_without_command=True)
@click.pass_context
@click.option('-d',
              '--debug',
              is_flag=True,
              default=False,
              help='Enable debug')
@click.option('-u',
              '--url',
              metavar='<user:pass@host>',
              required=True,
              envvar='VGR_URL',
              help='ESXi or vCenter URL')
@click.option('-s/-i',
              '--verify-ssl-certs/--no-verify-ssl-certs',
              required=False,
              default=True,
              help='Verify SSL certificates')
def vgr(ctx, debug, url, verify_ssl_certs):
    """vSphere Guest Run"""
    if ctx.invoked_subcommand is None:
        click.secho(ctx.get_help())
        return
    tokens = url.split(':')
    vc_user = tokens[0]
    tokens = tokens[1].split('@')
    vc_host = tokens[-1]
    vc_password = ''
    for token in tokens[:-1]:
        if len(vc_password) > 0:
            vc_password += '@'
        vc_password += token

    vs = VSphere(vc_host,
                 vc_user,
                 vc_password)
    # moid = va.get_vm_moid(vm_name)
    vs.connect()
    ctx.obj = {}
    ctx.obj['vs'] = vs


@vgr.command(short_help='show info')
@click.pass_context
def info(ctx):
    """Show info"""
    vs = ctx.obj['vs']
    print(vs.service_instance.content.about)


@vgr.command(short_help='show version')
@click.pass_context
def version(ctx):
    """Show version"""
    ver = pkg_resources.require("vsphere-guest-run")[0].version
    click.secho(ver)


def print_command(cmd, level=0):
    click.echo(' '+(' '*level*2)+' ', nl=False)
    click.echo(cmd.name)
    if type(cmd) == click.core.Group:
        for k in sorted(cmd.commands.keys()):
            print_command(cmd.commands[k], level+1)


@vgr.command(short_help='show help')
@click.pass_context
@click.option('-t',
              '--tree',
              is_flag=True,
              default=False,
              help='show commands tree')
def help(ctx, tree):
    """Show help"""
    if tree:
        print_command(ctx.parent.command)
    else:
        click.secho(ctx.parent.get_help())


@vgr.command(short_help='run command in guest')
@click.pass_context
@click.option('vm_name',
              '-v',
              '--vm',
              metavar='<vm-name>',
              envvar='VGR_VM',
              help='VM name')
@click.argument('guest-user')
@click.argument('guest-password')
@click.argument('command')
def run(ctx, vm_name,
        guest_user, guest_password, command):
    try:
        # vs = VSphere(vc_host,
        #              vc_user,
        #              vc_password)
        # moid = va.get_vm_moid(vm_name)
        vs = ctx.obj['vs']
        moid = vm_name
        vs.connect()
        vm = vs.get_vm_by_moid(moid)
        result = vs.execute_program_in_guest(
                    vm,
                    guest_user,
                    guest_password,
                    command,
                    True,
                    1
                    )
        click.secho('exit_code: %s\n' % result[0])
        click.secho('stdout: \n%s\n' % result[1].content.decode())
        click.secho('stderr: \n%s\n' % result[2].content.decode())
    except Exception as e:
        import traceback
        traceback.print_exc()
        click.secho(str(e))


@vgr.command('list', short_help='list VMs')
@click.pass_context
def list_cmd(ctx, tree):
    """List VMs"""
    click.secho('not implemented')


if __name__ == '__main__':
    vgr()
