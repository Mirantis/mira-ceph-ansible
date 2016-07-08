Installation steps
==================

* Prefly
* Install ansible
* Checkout ceph-ansible and mira-ceph-ansible
* Update roles path to add ceph-ansible roles
* Edit inventory file
* Edit Parameters
* Run pools.py to get pools.yml
* Check pools.yml
* Run site.yml
* Run pools.yml

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

Checkout ceph-ansible and mira-ceph-ansible
===========================================

    # git clone https://github.com/ceph/ceph-ansible.git
    # git clone https://github.com/Mirantis/mira-ceph-ansible.git


All subsequent steps should be executed from *mira-ceph-ansible* folder

Update roles path to add ceph-ansible roles
===========================================

Edit ansible.cfg. Add line

    roles_path = PATH_TO_CEPH_ANSIBLE/roles

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

Open 'group_vars/osds' and set storage devices and journal devices:

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

Edit *pools* section, if need.

  pools:
      POOL_NAME: POOL_WEIGHT

Pool weight should be proportional to pool data size/io activity.
Set all small weight to 0. Usually only volumes,compute,images, and ".rgw"
should have non-zero weight. generate_pools.py will calculate PG counts
for pools, basis on this weight.

You can also specify 

    min_pg_per_pool_per_osd: int (default=2)
    pg_per_osd: int (default=200)

min\_pg\_per\_pool\_per\_osd set minimal average PG, stored from each pool on each OSD
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


Run site.yml
============
Run

    # ansible-play -i hosts site.yml

In case if you face an error you can rerun it with -v/-vv/-vvvv
to get more detaild output.

[venv]: https://virtualenv.pypa.io/en/stable/
[ans-inv]: http://docs.ansible.com/ansible/intro_inventory.html


