import re
from datetime import datetime
import time

fstab_file = 'fstab.txt'
metric_file = 'metrics.txt'
except_fstab = ()
except_metric = ('tmpfs', 'gvfsd-fuse', 'lxcfs', '/boot', '/dev/sr0', 'udf,iso9660')
metric_name = 'node_filesystem_avail_bytes'

fstab_list = []
metric_list = []
with open(fstab_file, encoding='cp1251') as f:
    for n, s in enumerate(f.readlines(), 1):
        if not s.startswith('#') and s != '\n':
            s_n = re.sub(r'[\s]+', ' ', s).split(' ')
            if not ''.join(s_n[2:3]).startswith('sw') and \
                    not ''.join(s_n[1:2]).startswith('/boot'):
                fstab_list.append(s_n)

with open(metric_file) as m:
    for i, l in enumerate(m.readlines(), 1):
        if not l.startswith('#') and l != '\n':
            l_n = re.sub(r'[ ]+', ' ', l).split(' ')
            if ''.join(l_n[0:1]).startswith(metric_name):
                for _ in except_metric:
                    if not ''.join(l_n[0:1]).startswith(_):
                        lll = ','.join(
                            ''.join(l_n[0:1]).replace('"', '').replace(
                                'node_filesystem_avail_bytes{', '').replace('}', '').split('=')).split(',')
                        metric_list.append(lll)
                        lll = ''

bc_shares_match = set()
bc_shares_exception = set()

fstab_set = set()
for _ in range(len(fstab_list)):
    fstab_set.add(f'{fstab_list[_][0]};{fstab_list[_][1]};{fstab_list[_][2]}')

metric_set = set()
for _ in range(len(metric_list)):
    metric_set.add(f'{metric_list[_][1]};{metric_list[_][5]};{metric_list[_][3]}')

for _ in fstab_set & metric_set:
    bc_shares_match.add(_ + ';1')

for _ in fstab_set - metric_set:
    bc_shares_match.add(_ + ';0')

for _ in metric_set - fstab_set:
    bc_shares_exception.add(_ + ';0')

out_version = '# HELP bc_shares_match \n' \
              '# HELP bc_shares_exception \n' \
              '# HELP bc_shares_timestamp \n' \
              f'bc_shares_timestamp {time.mktime(datetime.now().timetuple())} \n'

for _ in bc_shares_match:
    st_split = _.split(';')
    out_version += f'bc_shares_match{{device={st_split[0]}, ' \
                   f'fstype={st_split[2]}, mountpoint={st_split[1]}}} {st_split[3]} \n'

for _ in bc_shares_exception:
    st_split = _.split(';')
    out_version += f'bc_shares_exception{{device={st_split[0]}, ' \
                   f'fstype={st_split[2]}, mountpoint={st_split[1]}}} {st_split[3]} \n'

# print(out_version)
with open('shares_match.prom', 'w+') as file:
    file.write(out_version)
