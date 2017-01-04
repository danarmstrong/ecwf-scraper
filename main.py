import json
import re
from lxml import html
import requests

url = 'http://www.easterncoloradowildflowers.com/'

link_page = requests.get(url + '_Scientific.htm')
link_tree = html.fromstring(link_page.content)
links = link_tree.xpath('//a')

flower_list = []

for link in links:
    # print(link.get('href'))
    flower_page = requests.get(url + link.get('href'))
    flower_tree = html.fromstring(flower_page.content)

    full_name = ''
    common_name = ''
    full_family = ''
    common_family = ''
    flower_obj = {}

    flower_obj['images'] = []
    for e in flower_tree.xpath('//img'):
        flower_obj['images'].append(e.get('src'))

    for e in flower_tree.xpath('//body/table[1]/tr[1]/td[1]'):
        full_name = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    m = re.search(r'\((.*?)\)', full_name)
    if m is None:
        print('Page `' + link.get('href') + '` has no common name')
        common_name = ''
    else:
        common_name = m.group(1)

    flower_obj['commonName'] = common_name
    flower_obj['scientificName'] = full_name.replace('(' + common_name + ')', '').rstrip()

    for e in flower_tree.xpath('//body/table[1]/tr[1]/td[3]'):
        full_family = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    if len(full_family) == 0:
        for e in flower_tree.xpath('//body/table[1]/tr[1]/td[2]'):
            full_family = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split()).replace('Family: ', '')

    m = re.search(r'\((.*?)\)', full_family)
    if m is None:
        print('Page `' + link.get('href') + '` has no common family')
        common_family = ''
    else:
        common_family = m.group(1)

    flower_obj['commonFamily'] = common_family
    flower_obj['scientificFamily'] = full_family.replace('(' + common_family + ')', '').rstrip()

    for e in flower_tree.xpath('//body/font[1]'):
        flower_obj['description'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    for e in flower_tree.xpath('//body/table[2]/tr[1]/td[2]'):
        flower_obj['zone'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    for e in flower_tree.xpath('//body/table[2]/tr[2]/td[2]'):
        flower_obj['bloom'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    for e in flower_tree.xpath('//body/table[2]/tr[3]/td[2]'):
        flower_obj['origin'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    flower_list.append(flower_obj)

flower_json = json.dumps(flower_list, indent=4, sort_keys=True)

f = open('flower_data.json', 'w')
f.write(flower_json)
f.close()

print('Done!')