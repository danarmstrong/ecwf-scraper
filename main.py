import os, random, string, json, re, requests, sqlite3, shutil
from lxml import html
from PIL import Image


def randomword(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


url = 'http://www.easterncoloradowildflowers.com/'
img_dir = 'img'
db_template = 'flower_data.sqlite'
db_file = 'flower_data.db'
json_file = 'flower_data.json'

if os.path.exists(img_dir):
    os.rmdir(img_dir)
os.mkdir(img_dir)

if os.path.exists(db_file):
    os.remove(db_file)
shutil.copyfile(db_template, db_file)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

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
    flower_obj = {
        'scientificName': '',
        'commonName': '',
        'scientificFamily': '',
        'commonFamily': '',
        'description': '',
        'zone': '',
        'origin': '',
        'bloom': '',
        'thumbnail': ''
    }

    #################################
    ## Name
    #################################
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

    #################################
    ## Family
    #################################
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

    #################################
    ## Description
    #################################
    for e in flower_tree.xpath('//body/font[1]'):
        flower_obj['description'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    if len(flower_obj['description']) is 0:
        for e in flower_tree.xpath('//body/font[2]'):
            flower_obj['description'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    if len(flower_obj['description']) is 0:
        print('Page `' + link.get('href') + '` has no description')

    #################################
    ## Zone
    #################################
    for e in flower_tree.xpath('//body/table[2]/tr[1]/td[2]'):
        flower_obj['zone'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    #################################
    ## Bloom
    #################################
    for e in flower_tree.xpath('//body/table[2]/tr[2]/td[2]'):
        flower_obj['bloom'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    #################################
    ## Origin
    #################################
    for e in flower_tree.xpath('//body/table[2]/tr[3]/td[2]'):
        flower_obj['origin'] = ' '.join(e.text_content().replace('\n', '').replace('\r', '').split())

    #################################
    ## Images
    #################################
    flower_obj['images'] = []
    create_thumb = True
    for e in flower_tree.xpath('//img'):
        r = requests.get(url + e.get('src'), stream=True)
        if r.status_code == 200:
            filename = randomword(10) + '.jpg'
            with open(img_dir + '/' + filename, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
                f.close()
            flower_obj['images'].append(filename)
            if create_thumb:
                thumb_filename = 'thumb_' + randomword(10) + '.jpg'
                im = Image.open(img_dir + '/' + filename)
                im.thumbnail((150, 150), Image.ANTIALIAS)
                im.save(img_dir + '/' + thumb_filename)
                flower_obj['thumbnail'] = thumb_filename
                create_thumb = False

    ##########################################
    ## Write the data to the SQLite database
    ##########################################
    cursor.execute("""
      INSERT INTO flowers(
        scientificName,
        commonName,
        scientificFamily,
        commonFamily,
        description,
        zone,
        bloom,
        origin,
        thumbnail
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        flower_obj['scientificName'],
        flower_obj['commonName'],
        flower_obj['scientificFamily'],
        flower_obj['commonFamily'],
        flower_obj['description'],
        flower_obj['zone'],
        flower_obj['bloom'],
        flower_obj['origin'],
        flower_obj['thumbnail']
    ))
    conn.commit()

    last_id = cursor.lastrowid

    for i in flower_obj['images']:
        cursor.execute("""
          INSERT INTO images(flowerId, filename) VALUES(?, ?)
        """, (last_id, i))
    conn.commit()

    flower_list.append(flower_obj)

flower_json = json.dumps(flower_list, indent=4, sort_keys=True)

f = open(json_file, 'w')
f.write(flower_json)
f.close()

conn.close()
print('Done!')
