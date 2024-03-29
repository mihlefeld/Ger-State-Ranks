# tool to write html in a pythonic way
import dominate
from dominate.util import raw, text
from dominate.tags import *

# get remote files with urls
import urllib.request as libreq
# tool to read in the response as json
import json

# for multi-sorting by priorities in nested lists
from operator import itemgetter

# from GCA Discord
import info

# make formatting easier / human-readable
import util

# to record when the last update happened
import datetime

from argparse import ArgumentParser

parser = ArgumentParser(description='Generate new WCA German State Ranks.')
parser.add_argument('-d', '--debug', default = False,
                    help='Get detailed printouts')
parser.add_argument('-l', '--local', default = False,
                    help='Use locally available json data')
parser.add_argument('-a', '--automate', default = False,
                    help='Do not write json data to local dir')

args = parser.parse_args()

print()
print('>> Running with options:')
print('>>   debug =', args.debug)
print('>>   local =', args.local)
print('>>   automate =', args.automate)

# if you want a bunch of printouts to understand what's going on -> True,
# default -> False (just get very few printouts)
debug = args.debug

# Use local copies to limit traffic
local = args.local

# Don't save downloaded jsons when running on schedule (GitHub Action)
automate = args.automate


# unofficial api, returns version of data
if local:
    with open('../local/version.json') as file:
        # the file is understood as json
        json_data_v = json.load(file)
else:
    with libreq.urlopen('https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/version.json') as file:
        # the file is understood as json
        json_data_v = json.load(file)
        if not automate:
            with open('../local/version.json', 'w') as f:
                json.dump(json_data_v, f)

version_y = json_data_v['export_date'][:4]
version_m = info.month_map[json_data_v['export_date'][5:7]]
version_d = json_data_v['export_date'][8:10]

# unofficial api, returns events
if local:
    with open('../local/events.json') as file:
        # the file is understood as json
        json_data_e = json.load(file)
else:
    with libreq.urlopen('https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/events.json') as file:
        # the file is understood as json
        json_data_e = json.load(file)
        if not automate:
            with open('../local/events.json', 'w') as f:
                json.dump(json_data_e, f)
e_list = [i['id'] for i in json_data_e['items']]

# model state dictionary with singles and averages, for each state, for each event
state_r = {k : {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}} for k in info.id_state.keys()}

print()
# where the magic happens -> reading the ranks once per WCA ID and writing what we need into the dictionary
for s in info.id_state.keys():
    wca_ids_s = info.id_state[s]
    print('>> Processing', wca_ids_s)
    for wca_id in wca_ids_s:
        if local:
            with open(f'../local/persons/{wca_id}.json') as file:
                json_data_p = json.load(file)
        else:
            with libreq.urlopen(f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/persons/{wca_id}.json') as file:
                json_data_p = json.load(file)
                if not automate:
                    with open(f'../local/persons/{wca_id}.json', 'w') as f:
                        json.dump(json_data_p, f)
        # ToDo: check for country == / != de
        # collect single / average results per person for each event they have a result in
        # for now, WCA ID, full name, best result (numerical value as in DB, not yet human-readable) and NR, CR, WR
        for e in json_data_p['rank']['singles']:
            state_r[s]['single'][e['eventId']].append([json_data_p['id'],
                                                       json_data_p['name'],
                                                       e['best'],
                                                       e['rank']['country'],
                                                       e['rank']['continent'],
                                                       e['rank']['world'],
                                                       json_data_p['country']])
        for e in json_data_p['rank']['averages']:
            state_r[s]['average'][e['eventId']].append([json_data_p['id'],
                                                        json_data_p['name'],
                                                        e['best'],
                                                        e['rank']['country'],
                                                        e['rank']['continent'],
                                                        e['rank']['world'],
                                                        json_data_p['country']])

# the rankings need to be sorted,
# otherwise we just have them as they appear in the discord reaction roles
for st,dicts in zip(state_r.keys(),state_r.values()):
    if debug:
        print('Sorting', st, 'now.')
    for s,sd in zip(dicts['single'].keys(),dicts['single'].values()):
        if debug:
            print(s)
            print(sd)
        # if tied on best result (index 2 in inner list), sort by name instead (index 1 in inner list)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r[st]['single'][s] = sd
    for s,sd in zip(dicts['average'].keys(),dicts['average'].values()):
        if debug:
            print(s)
            print(sd)
        # same here, just for averages (more precise: mean or average)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r[st]['average'][s] = sd


# now, for the combination we start over again with an empty dict
overview = {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}}

# collecting the best of all 16 states, for each event, for single / avg
for e in e_list:
    if debug:
        print(e)
    for i, st in enumerate(state_r.keys()):
        if debug:
            print('>>', i, st)
            print('>> Doing Singles')
        # checking if something exists for that state
        if len(state_r[st]['single'][e]) > 0:
            # ToDo: ties *within* one federal state are NOT yet modeled,
            # only the first one (alphabetically), as it's very very uncommon (333fm ?)
            #this_states_best_list = state_r[st]['single'][e][0]
            # modeling ties within a federal state
            this_states_best_value = state_r[st]['single'][e][0][2]
            this_states_best_list = [v for v in state_r[st]['single'][e] if v[2] == this_states_best_value]
            
            if debug:
                print(this_states_best_list)
            # checking if it's the first state with a result here
            if len(overview['single'][e]) == 0:
                # first result for this evt/single -> collect!
                overview['single'][e] = []
                for v in this_states_best_list:
                    overview['single'][e].append([st] + v)
                #overview['single'][e] = [[st] + this_states_best_list]
            else:
                # could be interesting, check if better or equal than already existing ones
                if this_states_best_list[0][2] <= overview['single'][e][0][3]:
                    # better -> collect as the only state
                    if this_states_best_list[0][2] < overview['single'][e][0][3]:
                        # currently best -> write state + who achieved that
                        overview['single'][e] = []
                        for v in this_states_best_list:
                            overview['single'][e].append([st] + v)
                        #overview['single'][e] = [[st] + this_states_best_list]
                    # just equal -> append
                    else:
                        # currently tied
                        for v in this_states_best_list:
                            overview['single'][e].append([st] + v)
                        #overview['single'][e].append([st] + this_states_best_list)

        # same stuff again, just for averages
        if e not in info.no_avg:
            if debug:
                print('>> Doing Averages')
            if len(state_r[st]['average'][e]) > 0:
                #this_states_best_list = state_r[st]['average'][e][0]
                # modeling ties within a federal state
                this_states_best_value = state_r[st]['average'][e][0][2]
                this_states_best_list = [v for v in state_r[st]['average'][e] if v[2] == this_states_best_value]
                if debug:
                    print(this_states_best_list)
                if len(overview['average'][e]) == 0:
                    overview['average'][e] = []
                    for v in this_states_best_list:
                        overview['average'][e].append([st] + v)
                    #overview['average'][e] = [[st] + this_states_best_list]
                else:
                    if this_states_best_list[0][2] <= overview['average'][e][0][3]:
                        if this_states_best_list[0][2] < overview['average'][e][0][3]:
                            # currently best
                            overview['average'][e] = []
                            for v in this_states_best_list:
                                overview['average'][e].append([st] + v)
                            #overview['average'][e] = [[st] + this_states_best_list]
                        else:
                            # currently tied
                            for v in this_states_best_list:
                                overview['average'][e].append([st] + v)
                            #overview['average'][e].append([st] + this_states_best_list)


# to show that we are only using a subset of all available results in German states,
# i.e. counting how many gave their consent
print()
id_count = 0
for k in info.id_state.keys():
    id_count += len(info.id_state[k])
print(f'>> Using {id_count} WCA IDs.')

# interesting info to fill on each page, as the results are time-dependent
#now = datetime.datetime.now()
updated = f'{version_m} {version_d}, {version_y}'

def generate_readme():
    md_str = f'''# WCA German State Ranks
[![WCA German State Ranks Automation](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/automate.yml/badge.svg)](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/automate.yml)
[![pages-build-deployment](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/pages/pages-build-deployment)

Displaying the PRs of people who have given *explicit consent* (opt-in) to appear in German WCA state rankings. Federal state data taken from the GCA Discord Server (reaction roles), PRs taken from the WCA database via the [unofficial API](https://github.com/robiningelbrecht/wca-rest-api).

## How to appear in these rankings?
- Join the GCA Discord Server and read + understand the rules.
- Append your WCA ID to your username (example: Nickname | 2024ABCD42)
- Click one of the 16 federal state reaction roles.

## Data statement
> This information is based on competition results owned and maintained by the
> World Cube Assocation, published at https://worldcubeassociation.org/results
> as of {updated}.
'''

    with open('../README.md', 'w') as f:
        f.write(md_str)

# called multiple times, for different purposes, however with some equal parts across pages
def generate_html(variant = 'by-state', choice = 'bw'):
    # three types of pages to generate, each coming with different setups here
    if variant == 'by-state':
        title_app = f' - {choice}'
        r = state_r[choice]
        s_dict = r['single']
        a_dict = r['average']
        prefix = '../pages/'
    if variant == 'overview':
        title_app = ' - Overview'
        prefix = '../pages/'
    if variant == 'index':
        title_app = ''
        prefix = '../'

    # start the DOM
    doc = dominate.document(title='WCA German State Ranks'+title_app)

    with doc.head:
        meta(charset='utf-8')
        meta(name='viewport', content='width=device-width, initial-scale=1')
        link(rel='stylesheet', href='https://www.w3schools.com/w3css/4/w3.css')
        link(rel='stylesheet', href='https://www.w3schools.com/lib/w3-theme-light-blue.css')
        link(rel='stylesheet', href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css')
        if variant == 'index':
            link(rel='stylesheet', href='./css/style.css')
        else:
            link(rel='stylesheet', href='../css/style.css')

    with doc:
        # body ('what the user sees')

        # how to write comments in the dominate library
        comment(' Content container ')

        # individual content per type, here from all states combined
        if variant == 'overview':
            with div():
                # give class attribute, don't use python reserved keywords
                attr(cls = 'container')
                # this would also be a good place to improve such items with id or class attributes for easy styling
                h1('WCA German State Ranks'+title_app)
                for es, s in zip(overview['single'].keys(),overview['single'].values()):
                    if debug:
                        print(es, s)
                    text(es + ' (Single)')
                    with div():
                        attr(style = 'overflow-x:auto;')
                        with table():
                            with thead():
                                with tr():
                                    th('Federal State', style = 'text-align: center;')
                                    th('Name', style = 'text-align: left;')
                                    th('WCA Id', style = 'text-align: center;')
                                    th('Value', style = 'text-align: right;')
                                    th('WR', style = 'text-align: right;')
                                    th('CR', style = 'text-align: right;')
                                    th('NR', style = 'text-align: right;')
                                    th('Country', style = 'text-align: center;')
                            with tbody():
                                for sid in s:
                                    if debug:
                                        print(sid)
                                    with tr():
                                        td(sid[0], style = 'text-align: center;')
                                        td(sid[2], style = 'text-align: left;')
                                        td(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            td(util.centiseconds_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbf':
                                            td(util.mbf_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbo':
                                            td(util.mbo_to_human(sid[3]), style = 'text-align: right;')
                                        else:
                                            td(sid[3], style = 'text-align: right;')
                                        td(sid[6], style = 'text-align: right;')
                                        td(sid[5], style = 'text-align: right;')
                                        td(sid[4], style = 'text-align: right;')
                                        td(sid[7], style = 'text-align: center;')
                for ea, aa in zip(overview['average'].keys(),overview['average'].values()):
                    if debug:
                        print(ea, aa)
                    text(ea + ' (Average)')
                    with div():
                        attr(style = 'overflow-x:auto;')
                        with table():
                            with thead():
                                with tr():
                                    th('Federal State', style = 'text-align: center;')
                                    th('Name', style = 'text-align: left;')
                                    th('WCA Id', style = 'text-align: center;')
                                    th('Value', style = 'text-align: right;')
                                    th('WR', style = 'text-align: right;')
                                    th('CR', style = 'text-align: right;')
                                    th('NR', style = 'text-align: right;')
                                    th('Country', style = 'text-align: center;')
                            with tbody():
                                for aid in aa:
                                    with tr():
                                        td(aid[0], style = 'text-align: center;')
                                        td(aid[2], style = 'text-align: left;')
                                        td(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm']:
                                            td(util.centiseconds_to_human(aid[3]), style = 'text-align: right;')
                                        else:
                                            td(aid[3], style = 'text-align: right;')
                                        td(aid[6], style = 'text-align: right;')
                                        td(aid[5], style = 'text-align: right;')
                                        td(aid[4], style = 'text-align: right;')
                                        td(aid[7], style = 'text-align: center;')

        # main page
        elif variant == 'index':
            with div():
                attr(cls = 'container')
                h1('WCA German State Ranks'+title_app)
                br()
                a('Overview', href=f'pages/overview_all.html')
                for st in state_r.keys():
                    a(info.name_state[st], href=f'pages/by-state_{st}.html')

        # individual states
        else:
            with div():
                attr(cls = 'container')
                h1('WCA German State Ranks'+title_app)
                for es, s in zip(s_dict.keys(),s_dict.values()):
                    text(es + ' (Single)')
                    with div():
                        attr(style = 'overflow-x:auto;')
                        with table():
                            with thead():
                                with tr():
                                    th('Name', style = 'text-align: left;')
                                    th('WCA Id', style = 'text-align: center;')
                                    th('Value', style = 'text-align: right;')
                                    th('WR', style = 'text-align: right;')
                                    th('CR', style = 'text-align: right;')
                                    th('NR', style = 'text-align: right;')
                                    th('Country', style = 'text-align: center;')
                            with tbody():
                                for sid in s:
                                    if sid[6] == 'DE':
                                        with tr():
                                            td(sid[1], style = 'text-align: left;')
                                            td(a(sid[0], href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'), style='text-align: center;')
                                            if es not in ['333fm', '333mbf', '333mbo']:
                                                td(util.centiseconds_to_human(sid[2]), style='text-align: right;')
                                            elif es == '333mbf':
                                                td(util.mbf_to_human(sid[2]), style='text-align: right;')
                                            elif es == '333mbo':
                                                td(util.mbo_to_human(sid[2]), style='text-align: right;')
                                            else:
                                                td(sid[2], style='text-align: right;')
                                            td(sid[5], style='text-align: right;')
                                            td(sid[4], style='text-align: right;')
                                            td(sid[3], style='text-align: right;')
                                            td(sid[6], style='text-align: center;')
                                    else:
                                        with tr():
                                            td(sid[1], style='font-style:italic;color:#A4A4A4;text-align: left;')
                                            td(a(sid[0], href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'), style='font-style:italic;color:#A4A4A4;text-align: center;')
                                            if es not in ['333fm', '333mbf', '333mbo']:
                                                td(util.centiseconds_to_human(sid[2]), style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            elif es == '333mbf':
                                                td(util.mbf_to_human(sid[2]), style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            elif es == '333mbo':
                                                td(util.mbo_to_human(sid[2]), style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            else:
                                                td(sid[2], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(sid[5], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(sid[4], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(sid[3], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(sid[6], style='font-style:italic;color:#A4A4A4;text-align: center;')
                for ea, aa in zip(a_dict.keys(),a_dict.values()):
                    text(ea + ' (Average)')
                    with div():
                        attr(style = 'overflow-x:auto;')
                        with table():
                            with thead():
                                with tr():
                                    th('Name', style = 'text-align: left;')
                                    th('WCA Id', style = 'text-align: center;')
                                    th('Value', style = 'text-align: right;')
                                    th('WR', style = 'text-align: right;')
                                    th('CR', style = 'text-align: right;')
                                    th('NR', style = 'text-align: right;')
                                    th('Country', style = 'text-align: center;')
                            with tbody():
                                for aid in aa:
                                    if aid[6] == 'DE':
                                        with tr():
                                            td(aid[1], style = 'text-align: left;')
                                            td(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'), style='text-align: center;')
                                            if es not in ['333fm']:
                                                td(util.centiseconds_to_human(aid[2]), style='text-align: right;')
                                            else:
                                                td(aid[2], style='text-align: right;')
                                            td(aid[5], style='text-align: right;')
                                            td(aid[4], style='text-align: right;')
                                            td(aid[3], style='text-align: right;')
                                            td(aid[6], style='text-align: center;')
                                    else:
                                        with tr():
                                            td(aid[1], style='font-style:italic;color:#A4A4A4;text-align: left;')
                                            td(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'), style='font-style:italic;color:#A4A4A4;text-align: center;')
                                            if es not in ['333fm']:
                                                td(util.centiseconds_to_human(aid[2]), style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            else:
                                                td(aid[2], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(aid[5], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(aid[4], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(aid[3], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                            td(aid[6], style='font-style:italic;color:#A4A4A4;text-align: center;')

        with div():
            attr(cls = 'container')
            with footer():
                attr(style='text-align: center;height:10rem;clear:both;display:block;')
                text(f'From {id_count} WCA IDs.')
                br()
                text(f'This information is based on competition results owned and maintained by the World Cube Assocation, published at https://worldcubeassociation.org/results as of {updated}.')
                br()
                a('© Annika Stein, 2024.',
                  href='https://annikastein.github.io/',
                  target='_blank')
        #script(src='js/script-Copy1.js')

    if debug:
        print()
        print('#'*8)
        print()
        print('>> Writing HTML file:')
        print(doc.render())
        print()
        print('#'*8)
        print()
    if variant == 'index':
        with open(f"{prefix}{variant}.html", "w") as text_file:
            print(doc, file=text_file)
    else:
        with open(f"{prefix}{variant}_{choice}.html", "w") as text_file:
            print(doc, file=text_file)


# now we know the relevant info to steer the UI
print()
print('#'*8)
print()
print('>> Finished reading competitor information and matched with state')
print()
print('#'*8)
print()

print('>> Writing index to UI.')
generate_html(variant = 'index', choice = 'all')

print('>> Writing updated state rank overview to UI.')
generate_html(variant = 'overview', choice = 'all')

for st in state_r.keys():
    print(f'>> Writing {st} ranks to UI.')
    generate_html(variant = 'by-state', choice = st)

print()
print('>> Writing version to README.md')
generate_readme()
print()
print('#'*8)
print()
print('>> Finished UI update. Have fun!')
print()
print('#'*8)
print()
