# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Implements the FUMBBL XML API in python. Currently limited to tournament information.
"""

__author__ = 'Sean Ahern (sean@ironmiketourney.com)'
__copyright__ = 'Copyright (c) 2012 Sean Ahern'
__license__ = 'New-style BSD'
__vcs_id__ = '$Id$'
__version__ = '0.1'

import urllib.request
from xml.dom import minidom

def test():
    """ Currently not implemented"""
    pass

if __name__=='__main__':
    test()

FUMBBL_URL = 'http://fumbbl.com/xml:'
GET_TOURNEYS_URL = 'group?id={0}&op=tourneys'
GET_MATCHES_URL = 'group?id={0}&op=matches&t={1}'
GET_TEAMS_URL = 'group?id={0}&op=members'
GET_TEAM_INFO_URL = 'team?id={0}&past=1'
GET_ROSTER_INFO_URL = 'roster?id={0}'

def fetchDOM(url):
    try:
        f = urllib.request.urlopen(url)
        dom = minidom.parseString(f.read())
    except IOError:
        return None
    else:
        return dom
    
def getTourneys(group):
    """ Get List of tournaments in a given group. """
    tourneys = {}
    dom = fetchDOM(FUMBBL_URL + GET_TOURNEYS_URL.format(group))
    if dom:
        for node in dom.getElementsByTagName('tournament'):
            myId = node.getAttribute('id')   
            nameNode = node.getElementsByTagName('name')[0]
        
            seasonNode = node.getElementsByTagName('season')[0]
            if seasonNode:
                seasonValue = getText(seasonNode.childNodes)
            else:
                seasonValue = None

            typeNode = node.getElementsByTagName('type')[0]
            if typeNode:
                typeValue = getText(typeNode.childNodes)
            else:
                typeValue = None

            styleNode = node.getElementsByTagName('style')[0]
            if styleNode:
                styleValue = getText(styleNode.childNodes)
            else:
                styleValue = None

            winnerNode = node.getElementsByTagName('winner')[0]
            if winnerNode:
                winnerValue = winnerNode.getAttribute('id')
            else:
                winnerValue = None
                                       
            tourneys.setdefault(myId, {'name': getText(nameNode.childNodes),
                                       'winner' : winnerValue,
                                       'style': styleValue,
                                       'type' : typeValue,
                                       'season': seasonValue,                       
                                       })
        return tourneys
    else:
        return None

def getPositionInfo():
    emptyCount = 0
    rosterId = 1
    positions = {}
    while emptyCount < 5: # Keep doing it until we get five empties in a row
        url = FUMBBL_URL + GET_ROSTER_INFO_URL.format(rosterId)
        f = urllib.request.urlopen(url)
        dom = minidom.parseString(f.read())
        if not dom.getElementsByTagName('name')[0].childNodes:
            emptyCount += 1
        else:
            emptyCount = 0        
            for node in dom.getElementsByTagName('position'):
                myId = node.getAttribute('id')
                nameNode = node.getElementsByTagName('name')[0]
                iconListNode = node.getElementsByTagName('iconList')[0]
                homeIconNode = iconListNode.getElementsByTagName('home')
                if homeIconNode:
                    icon = homeIconNode[0].getAttribute('standing')
                else:
                    icon = ""
                positions.setdefault(myId, {'name': getText(nameNode.childNodes), 
                                            'icon': icon})
        rosterId += 1
    return positions
  
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getPlayerInfo(group, tourneys):
    # Get list of performances
    players = {}
    teams = {}
    for tid in tourneys.keys():
        url = FUMBBL_URL + GET_MATCHES_URL.format(group, tid)
        f = urllib.request.urlopen(url)
        dom = minidom.parseString(f.read())
        for node in dom.getElementsByTagName('performance'):
            myId = node.getAttribute('player')   
            if myId in players:
                info = players[myId]
                info['completions'] += int(node.getAttribute('completions'))
                info['touchdowns'] += int(node.getAttribute('touchdowns'))
                info['interceptions'] += int(node.getAttribute('interceptions'))
                info['casualties'] += int(node.getAttribute('casualties'))
                info['mvps'] += int(node.getAttribute('mvps'))
                info['passing'] += int(node.getAttribute('passing'))
                info['rushing'] += int(node.getAttribute('rushing'))
                info['blocks'] += int(node.getAttribute('blocks'))
                info['fouls'] += int(node.getAttribute('fouls'))
                info['turns'] += int(node.getAttribute('turns'))
                info['spp'] = int(info['completions']) + int(info['touchdowns']) * 3 + int(info['interceptions']) * 2 + int(info['casualties']) * 2 + int(info['mvps']) * 5
            else:
                players.setdefault(myId, {
                  'completions': int(node.getAttribute('completions')),
                  'touchdowns': int(node.getAttribute('touchdowns')),
                  'interceptions': int(node.getAttribute('interceptions')),
                  'casualties': int(node.getAttribute('casualties')),
                  'mvps': int(node.getAttribute('mvps')),
                  'passing': int(node.getAttribute('passing')),
                  'rushing': int(node.getAttribute('rushing')),
                  'blocks': int(node.getAttribute('blocks')),
                  'fouls': int(node.getAttribute('fouls')),
                  'turns': int(node.getAttribute('turns')),
                  'tourney_id': tid,
                  })
                players[myId]['spp'] = int(players[myId]['completions']) + int(players[myId]['touchdowns']) * 3 + int(players[myId]['interceptions']) * 2 + int(players[myId]['casualties']) * 2 + int(players[myId]['mvps']) * 5
                  
    
    # Get list of teams        
    url = FUMBBL_URL + GET_TEAMS_URL.format(group)
    f = urllib.request.urlopen(url)
    dom = minidom.parseString(f.read())
    
    for node in dom.getElementsByTagName('team'):
        myId = node.getAttribute('id')
        nameNode = node.getElementsByTagName('name')[0]
        teams.setdefault(myId, {'name': getText(nameNode.childNodes)})
    
    #Update players with names
    for k in teams.keys():
        url = (FUMBBL_URL + GET_TEAM_INFO_URL).format(k)
        f = urllib.request.urlopen(url)
        dom = minidom.parseString(f.read())
        for node in dom.getElementsByTagName('player'):
            myId = node.getAttribute('id')        
            player = players.get(myId)
            if player is not None:
                nameNode = node.getElementsByTagName('name')[0]
                player['name'] = getText(nameNode.childNodes)
                positionNode = node.getElementsByTagName('positionId')[0]
                player['position_id'] = getText(positionNode.childNodes)
                player['team_id'] = k
                player['team_name'] = teams[k]['name']
                
    return players

def generateLeaderTable(stat, sorted_list, positions = None):
    output = "<div>\n <h3>" + stat.capitalize() + " Leaders</h3>\n"
    output += " <table>\n  <tr><th class='NameHeader'>Name</th><th class='TeamHeader'>Team</th><th class='tourneyHeader'>Tourney</th><th class='ValueHeader'>" + stat.capitalize() + "</th></tr>"
    for pid in sorted_list:
        if players[pid][stat] != 0:
            iconImage = ""
            if positions and positions[players[pid]['position_id']]:
                iconImage = "<div class='iconImage'><img src='" + positions[players[pid]['position_id']]['icon'] + "'></div>"               
            output += "\n  <tr><td><a href='http://fumbbl.com/FUMBBL.php?page=player&player_id=" + pid + "'>" + iconImage + players[pid]['name'] + "</a></td>"
            output += "<td><a href='http://fumbbl.com/FUMBBL.php?page=team&op=view&team_id=" + players[pid]['team_id'] + "'>" + players[pid]['team_name'] + "</a></td>"
            output += "<td>" + tourneys[ players[pid]['tourney_id'] ]['name'] + "</td>"
            output += "<td>" + str(players[pid][key]) + "</td></tr>"
    output += "\n </table>\n</div>"
    return output

def getTopPlayersList(stat, players, count=10):
    return sorted(players, key=lambda player: players[player][stat], reverse=True)[0:count-1]

import collections
    
players = {}
tourneys = {}

tourneys = getTourneys('7761')
positions = getPositionInfo()
# Change name to drop extra stuff
for key, tourney in tourneys.items():
    tourney['name'] = tourney['name'].replace("3DB1 - ", "").replace("Division", "").replace("division", "")
players = getPlayerInfo('7761', tourneys)
 
leader_lists = collections.OrderedDict([ 
    ("touchdowns" ,  getTopPlayersList("touchdowns",    players, 10) ) ,
    ("casualties" ,  getTopPlayersList('casualties',    players, 10) ) ,
    ("completions" , getTopPlayersList('completions',   players, 10) ) ,
    ("interceptions",getTopPlayersList('interceptions', players, 10) ) ,
    ("mvps" ,        getTopPlayersList('mvps',    players, 10) ) ,
    ("spp" ,         getTopPlayersList('spp',     players, 10) ) ,
    ("blocks" ,      getTopPlayersList('blocks',  players, 10) ) ,
    ("fouls" ,       getTopPlayersList('fouls',   players, 10) ) ,
    ("passing" ,     getTopPlayersList('passing', players, 10) ) ,
    ("rushing" ,     getTopPlayersList('rushing', players, 10) ) ,
])

output = "<html>\n<head>\n<style type=\"text/css\">\n"
output+= "th.NameHeader{width:35%}\n"
output+= "th.TeamHeader{width:35%}\n"
output+= "th.TourneyHeader{width:15%}\n"
output+= "th.ValueHeader{width:15%}\n"
output+= "div.iconImage{margin-right:7px;width:32px;height:32px; float:left}\n"
output+= "table{width:600px;border: 1px solid black;border-spacing: 0px;font-size:x-small}\n"
output+= "td,th{border: 1px solid black;padding: 1px; background-color:white}\n"
output+= "th{font-weight:bold;text-align:center}\n"
output+= "h3{margin: 1px;padding: 1px;margin-top:15px;font-weight:bold}\n"
output+= "body{font-family:'Arial';}\n</style>\n</head>\n<body>"

for key, sorted_list in leader_lists.items():
    output += generateLeaderTable(key, sorted_list, positions)
output += "</body></html>"

print(output)