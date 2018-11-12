with open("playersCSV.csv") as f:
    lines = f.readlines()
lines = [x.strip() for x in lines]

headers = lines[0].split(',')

soloDuoIndex = headers.index("Are you signing up as a Solo or Duo?")

soloRankIndex = headers.index("What's your current Solo/Duo rank?")
soloPref1Index = headers.index("Primary Role")
soloPref2Index = headers.index("Secondary Role")

duo1RankIndex = headers.index("First Player's current Solo/Duo rank?")
duo2RankIndex = headers.index("Second Player's current Solo/Duo rank?")

duo1Pref1Index = headers.index("First Player's Primary Role?")
duo2Pref1Index = headers.index("First Player's Secondary Role?")

duo1Pref2Index = headers.index("Second Player's Primary Role?")
duo2Pref2Index = headers.index("Second Player's Secondary Role")

playerStats = {}

playerValues = [x.split(',') for x in lines[1:]]

i=0
playerStats = {}
for player in playerValues:
    playerStat = {'Rank':None,'First pref':None, 'Second pref':None}
    if player[soloDuoIndex]=="Solo":
        playerStat['Rank'] = player[soloRankIndex]
        playerStat['First pref'] = player[soloPref1Index]
        playerStat['Second pref'] = player[soloPref2Index]
        
        playerStats[i] = playerStat
        i+=1
    else:
        assert(player[soloDuoIndex]=="Duo")
        playerStat2 = playerStat.copy()
         
        playerStat['Rank'] = player[duo1RankIndex]
        playerStat2['Rank'] = player[duo2RankIndex]
        
        playerStat['First pref'] = player[duo1Pref1Index]
        playerStat2['First pref'] = player[duo2Pref1Index]

        playerStat['Second pref'] = player[duo1Pref2Index]
        playerStat2['Second pref'] = player[duo2Pref2Index]
        
        playerStats[i] = playerStat
        i+=1
        playerStats[i] = playerStat2
        i+=1
        
        
assert(len(headers)==len(playerValues[0]))
length = len(headers)
'''
playerStats = {}
for i in range(len(playerValues)):
    playerStats[i] = {headers[j]:playerValues[i][j] for j in range(length)}
'''
for k in playerStats.keys():
    print(playerStats[k])
