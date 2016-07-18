Installation steps
==================

* Prefly
* Install ansible
* Checkout ceph-ansible and mira-ceph-ansible
* Edit inventory file
* Edit Parameters
* Prepare vars files
* Run pools.py to get pools.yml
* Run site.yml

Prefly
======

Make passwordless ssh connections to all hosts
and also add all cluster hosts keys to ~/.ssh/knownhosts file.
If you like to use other connection options consult with ansible documentation
[inventory][ans-inv].

All hosts shouls have resolvable hostnames.


Install ansible
===============

You need ansible 1.8.4+. It can be installed using pip

    # pip install ansible

You can use [virtual-env][venv] to avoid overriding system ansible.

Or system-wide from 'ppa:ansible/ansible' with

    # add-apt-repository -y ppa:ansible/ansible
    # apt-get update
    # apt-get install -y ansible

Checkout ceph-ansible and mira-ceph-ansible
===========================================

    # git clone https://github.com/ceph/ceph-ansible.git
    # git clone https://github.com/Mirantis/mira-ceph-ansible.git

Be strict about directories names and locations. In case if you
would organize you code in other way you will need to update ansible.cfg file.
Read README.md from ceph-ansible repo.

All subsequent steps should be executed from 'mira-ceph-ansible' folder

Edit inventory file
===================
    
Put hostsnames into 'hosts' file, like this

    [mons]
    mon1
    mon2
    mon3

    [osds]
    osd1
    osd2
    osd3
    osd4
    osd5

    [rgws]
    mon1
    mon2
    mon3

    [clients]
    osd3


You have to use hostnames and not ip address in inventory.

Edit Parameters
===============

Set ip/interface for monitors to listen on. Either per host
or globally.

UPDATE_ME

group_vars/osds
---------------

In case if you colocate journals with osd(not recommended):
osd_auto_discovery: false
raw_multi_journal: true
journal_colocation: false

In case if you use separated partitions for journals:

    devices:
      - /dev/sdg
      - /dev/sdh
      - /dev/sdi
      - /dev/sdj
      - /dev/sdk
      - /dev/sdl
    raw_journal_devices:
      - /dev/sdc1
      - /dev/sdc2
      - /dev/sdc3
      - /dev/sdc4
      - /dev/sdc5
      - /dev/sdd1

Edit 'pools' section, if need.

    pools:
        POOL_NAME1: POOL_WEIGHT1
        POOL_NAME2: POOL_WEIGHT2
        ....
        POOL_NAMEN: POOL_WEIGHTN

File already contains default values for openstack + ceph for hammer release.

Pool weight should be proportional to pool data size/io activity.
Set all small weight to 0. Usually only volumes,compute,images, and ".rgw"
should have non-zero weight. generate_pools.py will calculate PG counts
for pools, basis on this weight.

You can also specify 

    min_pg_per_pool_per_osd: int (default=2)
    pg_per_osd: int (default=200)

min\_pg\_per\_pool\_per\_osd set minimal average PG, stored from each pool on each OSD,
pg\_per\_osd set average PG per OSD (sum over all pools)

Prepare vars files
==================

Reaplce 'SET_ME' indentificator in vars/all, vars/osds, and vars/mons files with appropriate
values.

Generate pools.yml
==================

Run

    # python py/generate_pools.py hosts > pools.yml

pools.yml now contains ansible play for creationg pools.
You can review and update it, if need.


Install ceph
============

Run

    # ansible-play -i hosts site.yml

In case if you face an error you can rerun it with -v/-vv/-vvvv
to get more detailed output.


Purging the cluster
===================

*Don't use purge-cluster.yml, comes with ceph-ansible for ubuntu systems.*
*Use ones from mira-ceph-ansible.*

Run

    # ansible-play -i hosts purge-cluster.yml

[venv]: https://virtualenv.pypa.io/en/stable/
[ans-inv]: http://docs.ansible.com/ansible/intro_inventory.html


