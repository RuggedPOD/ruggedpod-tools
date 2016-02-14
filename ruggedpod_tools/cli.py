# RuggedPOD Tools
#
# Copyright (C) 2016 Guillaume Giamarchi <guillaume.guillaume@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from click import group, option, pass_context, argument, UsageError
from prettytable import PrettyTable

import ruggedpod_tools.firmware_burn as burn


@group()
@pass_context
def ruggedpod(ctx):
    """RuggedPOD Tools command line interface"""
    # ctx.obj['api'] = RuggedPODClient(api_url, username, password, debug)
    pass


@ruggedpod.command(name='firmware-burn')
@option('--target', help='Comma separated device list')
@option('--image', help='Binary image file path')
@option('--version', help='Firmware version to copy (Git tag)')
@pass_context
def firmware_burn(ctx, target, image, version):
    """Copy the firmware binary image to the specified devices"""
    burn.run({
        "file": "/Users/guillaume/dev/ocp/ruggedpod-tools/test.img",
        "devices": [
            "/tmp/a",
        ]
    })


def main():
    ruggedpod(obj={})


if __name__ == '__main__':
    main()
