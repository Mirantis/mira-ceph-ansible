# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Ceph utils"""

import sys
import math
import argparse

from ansible.inventory import Inventory
from ansible.vars import VariableManager
from ansible.parsing.dataloader import DataLoader


def to_upper_power_two(val, threshold=1E-2):
    """round to next 2**X integer

    closest upper integer, which is power of two, treshold is for tolerating
    float errors
    """
    if val < threshold:
        return 0
    val_log2 = math.log(val, 2)
    return 2 ** int(val_log2 + (1 if val_log2 % 1 > threshold else 0))


def get_pool_pg_count(osd_num, pool_sz, pools,
                      pg_per_osd,
                      min_pg_per_pool_per_osd=2):
    """calculate pg count for pools

    parametes:
        osd_num: int - OSD count
        pool_sz: int - pool size
        pools - {pool_name: weight}
        pg_per_osd:int, default 200 - lower boundry of PG per OSD
        minimal_pg_count: int, default 64 - minimal amout of PG per pool

    returns dictionary {pool_name: pool_pg_count}, with additional key -
    default_pg_num - default PG count for all pools, not in result

    * Estimated total amount of PG copyis calculated as
      (OSD * PG_COPY_PER_OSD),
      where PG_COPY_PER_OSD == 200 for now
    * Each small pool gets one PG copy per OSD. Means (OSD / pool_sz) groups
    * All the rest PG are devided between rest pools, proportional to their weights.
    * Each PG count is rounded to next power of 2
    """

    total_pg_count = float(pg_per_osd) / pool_sz * float(osd_num)
    total_weight = sum(pools.values())
    minimal_pg_count = to_upper_power_two(osd_num * min_pg_per_pool_per_osd / pool_sz)

    assert osd_num >= 2, "There should be at least 2 osd"
    assert osd_num >= pool_sz, "osd count({0}) should be >= pool_sz({1})".format(osd_num, pool_sz)

    if total_weight == 0:
        if len(pools) == 0:
            # return default for case when would be only one pool
            return {'default_pg_num': to_upper_power_two(total_pg_count)}

        default_pg_count = max(minimal_pg_count,
                               to_upper_power_two(total_pg_count / len(pools)))
        pg_per_weight = 0
    else:
        default_pg_count = minimal_pg_count
        small_pool_count = len([1 for name, weight in pools.items() if weight == 0])
        pg_per_weight = ((total_pg_count - minimal_pg_count * small_pool_count) / total_weight)

        if pg_per_weight < 0:
            pg_per_weight = 0

    res = {'default_pg_num': default_pg_count}

    for pool, weight in pools.items():
        res[pool] = max(to_upper_power_two(weight * pg_per_weight), default_pg_count)

    return res


pool_tmpl = '    - {{name: "{name}", pg_num: {pg_num}}}\n'

pool_template_cycle = """---

- hosts: mons[0]
  gather_facts: False
  vars:
    cluster: {cluster}
  tasks:
  - name: check pools exists
    shell: ceph --cluster {{{{ cluster }}}} osd pool get {{{{ item.name }}}} pg_num
    register: pool_exists
    ignore_errors: True
    with_items:
{pools}
  - name: create pools
    shell: ceph --cluster {{{{ cluster }}}} osd pool create {{{{ item.item.name }}}} {{{{ item.item.pg_num }}}}
    with_items: '{{{{ pool_exists.results }}}}'
    when: item.rc != 0
"""

# role 'has_pool' ???


def make_create_pools_site(inv, opts):
    osd_count = 0
    osds = inv.get_hosts('osds')
    for host in osds:
        osd_vars = host.get_vars().copy()
        osd_vars.update(host.get_group_vars())
        osd_count += len(osd_vars['devices'])

    pool_sz = osd_vars['pool_default_size']
    pools = osd_vars['pools']
    pg_per_osd = osd_vars.get('pg_per_osd', 200)
    min_pg_per_pool_per_osd = osd_vars.get('min_pg_per_pool_per_osd', 2)

    pool2pg = get_pool_pg_count(osd_count, pool_sz, pools,
                                pg_per_osd=pg_per_osd,
                                min_pg_per_pool_per_osd=min_pg_per_pool_per_osd)

    default_pg_num = pool2pg.pop('default_pg_num')

    yaml_pg_pools = {
        key: (key.replace(".", "_"), val) for key, val in pool2pg.items()
    }

    res = ""
    for name, (rname, pg_num) in yaml_pg_pools.items():
        res += pool_tmpl.format(name=rname, pg_num=pg_num)

    pools_creation_yaml = pool_template_cycle.format(pools=res, cluster='ceph')
    return pools_creation_yaml, default_pg_num


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-per-osd", type=int, default=200,
                        help="Target PG per OSD value. Real PG per OSD would" +
                             "almost always be bigger. Up to two times")
    parser.add_argument("inventory",
                        help="path to inventory file")
    opts = parser.parse_args(argv[1:])
    inv = Inventory(DataLoader(), VariableManager(), opts.inventory)
    print make_create_pools_site(inv, opts)[0]


if __name__ == "__main__":
    exit(main(sys.argv))
