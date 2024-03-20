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
state_r = {k : {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list}} for k in info.id_state.keys()}

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
overview = {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list}}

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
            this_states_best_list = state_r[st]['single'][e][0]
            if debug:
                print(this_states_best_list)
            # checking if it's the first state with a result here
            if len(overview['single'][e]) == 0:
                # first result for this evt/single -> collect!
                overview['single'][e] = [[st] + this_states_best_list]
            else:
                # could be interesting, check if better or equal than already existing ones
                if this_states_best_list[2] <= overview['single'][e][0][3]:
                    # better -> collect as the only state
                    if this_states_best_list[2] < overview['single'][e][0][3]:
                        # currently best -> write state + who achieved that
                        overview['single'][e] = [[st] + this_states_best_list]
                    # just equal -> append
                    else:
                        # currently tied
                        overview['single'][e].append([st] + this_states_best_list)
    
        # same stuff again, just for averages
        if debug:
            print('>> Doing Averages')
        if len(state_r[st]['average'][e]) > 0:
            this_states_best_list = state_r[st]['average'][e][0]
            if debug:
                print(this_states_best_list)
            if len(overview['average'][e]) == 0:
                overview['average'][e] = [[st] + this_states_best_list]
            else:
                if this_states_best_list[2] <= overview['average'][e][0][3]:
                    if this_states_best_list[2] < overview['average'][e][0][3]:
                        # currently best
                        overview['average'][e] = [[st] + this_states_best_list]
                    else:
                        # currently tied
                        overview['average'][e].append([st] + this_states_best_list)
                        

# to show that we are only using a subset of all available results in German states,
# i.e. counting how many gave their consent
print()
id_count = 0
for k in info.id_state.keys():
    id_count += len(info.id_state[k])
print(f'>> Using {id_count} WCA IDs.')

# interesting info to fill on each page, as the results are time-dependent
now = datetime.datetime.now()
updated = now.strftime("%Y-%m-%d")

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
                h3(f'From {id_count} WCA IDs, last updated on {updated}.')
                for es, s in zip(overview['single'].keys(),overview['single'].values()):
                    if debug:
                        print(es, s)
                    text(es + ' (Single)')
                    with table():
                        with thead():
                            with tr():
                                th('Federal State')
                                th('Name')
                                th('WCA Id')
                                th('Value')
                                th('WR')
                                th('CR')
                                th('NR')
                                th('Country')
                        with tbody():
                            for sid in s:
                                if debug:
                                    print(sid)
                                with tr():
                                    th(sid[0])
                                    th(sid[2])
                                    th(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'))
                                    if es not in ['333fm', '333mbf', '333mbo']:
                                        th(util.centiseconds_to_human(sid[3]))
                                    else:
                                        th(sid[3])
                                    th(sid[6])
                                    th(sid[5])
                                    th(sid[4])
                                    th(sid[7])
                for ea, aa in zip(overview['average'].keys(),overview['average'].values()):
                    if debug:
                        print(ea, aa)
                    text(ea + ' (Average)')
                    with table():
                        with thead():
                            with tr():
                                th('Federal State')
                                th('Name')
                                th('WCA Id')
                                th('Value')
                                th('WR')
                                th('CR')
                                th('NR')
                                th('Country')
                        with tbody():
                            for aid in aa:
                                with tr():
                                    th(aid[0])
                                    th(aid[2])
                                    th(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'))
                                    if es not in ['333fm', '333mbf', '333mbo']:
                                        th(util.centiseconds_to_human(aid[3]))
                                    else:
                                        th(aid[3])
                                    th(aid[6])
                                    th(aid[5])
                                    th(aid[4])
                                    th(aid[7])
        
        # main page
        elif variant == 'index':
            with div():
                attr(cls = 'container')
                h1('WCA German State Ranks'+title_app)
                h3(f'From {id_count} WCA IDs, last updated on {updated}.')
                br()
                a('Overview', href=f'pages/overview_all.html')
                for st in state_r.keys():
                    a(info.name_state[st], href=f'pages/by-state_{st}.html')         
        
        # individual states
        else:
            with div():
                attr(cls = 'container')
                h1('WCA German State Ranks'+title_app)
                h3(f'From {id_count} WCA IDs, last updated on {updated}.')
                for es, s in zip(s_dict.keys(),s_dict.values()):
                    text(es + ' (Single)')
                    with table():
                        with thead():
                            with tr():
                                th('Name')
                                th('WCA Id')
                                th('Value')
                                th('WR')
                                th('CR')
                                th('NR')
                                th('Country')
                        with tbody():
                            for sid in s:
                                if sid[6] == 'DE':
                                    with tr():
                                        th(sid[1])
                                        th(a(sid[0], href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'))
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            th(util.centiseconds_to_human(sid[2]))
                                        else:
                                            th(sid[2])
                                        th(sid[5])
                                        th(sid[4])
                                        th(sid[3])
                                        th(sid[6])
                                else:
                                    with tr():
                                        th(sid[1], style='font-style:italic;color:#A4A4A4;')
                                        th(a(sid[0], href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'), style='font-style:italic;color:#A4A4A4;')
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            th(util.centiseconds_to_human(sid[2]), style='font-style:italic;color:#A4A4A4;')
                                        else:
                                            th(sid[2], style='font-style:italic;color:#A4A4A4;')
                                        th(sid[5], style='font-style:italic;color:#A4A4A4;')
                                        th(sid[4], style='font-style:italic;color:#A4A4A4;')
                                        th(sid[3], style='font-style:italic;color:#A4A4A4;')
                                        th(sid[6], style='font-style:italic;color:#A4A4A4;')
                for ea, aa in zip(a_dict.keys(),a_dict.values()):
                    text(ea + ' (Average)')
                    with table():
                        with thead():
                            with tr():
                                th('Name')
                                th('WCA Id')
                                th('Value')
                                th('WR')
                                th('CR')
                                th('NR')
                                th('Country')
                        with tbody():
                            for aid in aa:
                                if aid[6] == 'DE':
                                    with tr():
                                        th(aid[1])
                                        th(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'))
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            th(util.centiseconds_to_human(aid[2]))
                                        else:
                                            th(aid[2])
                                        th(aid[5])
                                        th(aid[4])
                                        th(aid[3])
                                        th(aid[6])
                                else:
                                    with tr():
                                        th(aid[1], style='font-style:italic;color:#A4A4A4;')
                                        th(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'), style='font-style:italic;color:#A4A4A4;')
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            th(util.centiseconds_to_human(aid[2]), style='font-style:italic;color:#A4A4A4;')
                                        else:
                                            th(aid[2], style='font-style:italic;color:#A4A4A4;')
                                        th(aid[5], style='font-style:italic;color:#A4A4A4;')
                                        th(aid[4], style='font-style:italic;color:#A4A4A4;')
                                        th(aid[3], style='font-style:italic;color:#A4A4A4;')
                                        th(aid[6], style='font-style:italic;color:#A4A4A4;')

        with footer():
            attr(style='text-align: center;height:10rem;clear:both;display:block;')
            a('© Annika Stein, 2024.',
              href='https://cuboss.com/affiliate/?affiliate=hugacuba&r=hugacuba',
              target='_blank')
        #script(src='js/script-Copy1.js')
        script(data_id='101446349', _async=True, src='//static.getclicky.com/js')

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
print('#'*8)
print()
print('>> Finished UI update. Have fun!')
print()
print('#'*8)
print()
