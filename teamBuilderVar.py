import math, random, re, time
Lanes = ('top','jungle','mid','adc','support')
Divisions = ('Bronze','Silver',\
    'Gold','Platinum','Diamond','Master','Challenger')
SubDivisions = ('V','IV','III','II','I')

class Rank:
    base = 2
    minRank = base**2
    maxRank = minRank*(base**(len(Divisions)-2))


    #Static
    def getRank(s):
        '''>>>Rank.getRank('diamondIV')
        2^5.2'''
        getNonCaptureGroups = lambda x: "".join("(?:{})|".format(s) for s in x)[:-1]
        #[:-1] to remove | at the end
        caseFoldIndi = lambda x: '(?:{}|{})'.format(x[0],x[0].lower())+x[1:]
        caseFold = lambda y: tuple(caseFoldIndi(x) for x in y)
        
        alphaRanks = SubDivisions
        rankAlDic = {alphaRanks[i]:i/5 for i in range(len(alphaRanks))}
        rankIntDic =  {str(i+1): 1-(i/5) for i in range(5)}

        subDivisions = getNonCaptureGroups(alphaRanks+tuple(range(1,6)))
        noSub = getNonCaptureGroups(('{}(?: +I)*'.format(caseFoldIndi("Master")),\
                '{}'.format(caseFoldIndi("Challenger"))))
            #for some reason, the website I use calls master 'Master I'
            #so I hardcoded a noncapture group to accept that ' I' suffex
        withSub = getNonCaptureGroups(caseFold(Divisions[:5]))

        regexNoSub = "((?:{}))".format(noSub)
            # no subdivision ie Challenger IV d.n.e.
        regexSub = "((?:(?:{}))) *((?:{}))".format(withSub,subDivisions)
        mSub = re.fullmatch(regexSub, s)
        mNoSub = re.fullmatch(regexNoSub, s)

        if mSub or mNoSub:
            m = mSub if mSub else mNoSub
            divisionIndex = Divisions.index("Master") if m.group(1)=="Master I" else Divisions.index(m.group(1).capitalize())
            preExpoVal = divisionIndex+math.log(Rank.minRank,Rank.base)
            #add one so that the minimum is the minimum index(0) +1
            #or else for bronzeV = 0, bronzeIV = 0.2:
            # 2^bronzeV > 2^bronzeIV
            
            if mSub:
                preExpoVal+= rankIntDic[m.group(2)] if m.group(2).isnumeric() else rankAlDic[m.group(2)]
                #pre exponential value
            return Rank.base**preExpoVal           
        print('invalid rank: '+s)
        return

    #Static
    def rankIntToStr(rank):
        '''>>>rankIntToStr(128)
        "Challenger" '''
        #round to nearest 0.2
        ''' 4.72 -> 4.7  -> 47 -> 48 -> 4.8'''
        #num = log(round(rank,1),2)
        num = math.log(rank,Rank.base)
        num = int(num*10)
        if num%2!=0:
            #if the last digit isn't even
            num=min((num+1,num-1),key=lambda x:math.fabs(x/10-rank))/10
        else:   
            num = num/10

        num-=math.log(Rank.minRank,Rank.base) #remember, bronzeV => 1 not 0, but divisions[1] != bronze

        index = int(num//1)
        s = Divisions[index]
        if num<5:
            s +=  " "+SubDivisions[round(5*(num%1))]
        # int(1.9999999996)!=2
        # round(1.9...)=2
        return s

class Player:

    def __init__(self, name: str, rank: str, prefRole1: str, prefRole2: str):
        assert(prefRole1 in Lanes and prefRole2 in Lanes)
        self.name = name
        self.rank = Rank.getRank(rank)
        self.prefRole1 = prefRole1
        self.prefRole2 = prefRole2
        self.team = None

    def setTeam(self, team):
        self.team = team

    def getName(self):
        return self.name

    def getTeam(self):
        return self.team

    def getRank(self):
        return self.rank

    def getPrefRole1(self):
        return self.prefRole1

    def getPrefRole2(self):
        return self.prefRole2

    def __repr__(self):
        return self.name

class Team:

    def __init__(self, name = str):
        self.name = name
        self.members = {Lanes[i]:None for i in range(5)}

    def getMembers(self):
        return self.members

    def getName(self):
        return self.name
    
    def removePlayer(self, player: Player):
        for key in self.members.keys():
            if self.members[key] == player:
                self.members[key] = None
                assert(player.getTeam() == self)
                player.team = None
                return
        print('error: no such player') 


    def isFullTeam(self):
        for value in self.members.values():
            if value is None:
                return False
        return True

    def addPlayer(self, player, role=None):
        player.setTeam(self)
        if role:
            if self.members[role] is None:
                self.members[role]=player
                player.setTeam(self)
            else:
                print('error: role already taken') 
        else:
            if not self.isFullTeam():
                for key in self.members.keys():
                    if not self.members[key]:
                        self.members[key]=player
                        player.setTeam(self)
                        return
            else:
                print('error: full team') 

    def getAvgRank(self):
        return sum(p.getRank() for p in self.members.values())/5

    def getVariance(self,avgRank)->int:
        numPlayers = 5 # = len(self.members)
        summ = 0
        for role in self.members:
            rank=self.members[role].getRank()
            summ+=(rank-avgRank)**2
        return summ/(numPlayers)
    # divided by n instead of n-1 because this is
    # population deviation

    #@static
    def getAvgBenefit(members):
        benefitSum = 0
        for key in members.keys():
            if members[key].prefRole1 == key:
                benefitSum += 1
            elif members[key].prefRole2 == key:
                benefitSum += 0.75
        return benefitSum/5.0
    
    def optimiseUtility(self):
        
        players = list(self.members.values())
        layout = {Lanes[i]:None for i in range(5)}
        layoutKeys = list(layout.keys())
        # for some reason, dict keys() and values() returns
        # aren't generators, they are special objects of their own type ://

        def _optimiseUtility(players, layout, layoutKeys):
            if len(layoutKeys) == 0:
                return layout
            branches = []
            for i in range(len(players)):
                layoutCopy = layout.copy()
                playersCopy = players.copy()
                layoutKeysCopy = layoutKeys.copy()
                layoutCopy[layoutKeysCopy.pop()] = playersCopy.pop(i)
                if len(players)==1:
                    # implies that when playerCopy is popped, there are no players left
                    branches.append(_optimiseUtility(playersCopy, layoutCopy, layoutKeysCopy))
                else:
                    branches.extend(_optimiseUtility(playersCopy, layoutCopy, layoutKeysCopy))
            return branches

        tree = _optimiseUtility(players, layout, layoutKeys)
        assert(self.members in tree)
        maxi = max(tree, key = lambda x: Team.getAvgBenefit(x))
        self.members = maxi
        return maxi

    def revert(self, members):
        self.members = members
    
    def getUtility(self, avgRank):
        assert(self.isFullTeam())

        ar = avgRank
        maxMeanDiff = max(ar-Rank.minRank,Rank.maxRank-ar)

        selfAvgRank = self.getAvgRank()
        #maxSelfMeanDiff = max(av,upperBoundAR-selfAvgRank)
        #maxSelfSD = ((((maxSelfMeanDiff)**2)*5)/5)**0.5

        maxSD = ((((maxMeanDiff)**2)*5)/5)**0.5
        standardDev = self.getVariance(avgRank)**0.5
        
        #ohs = (maxSelfSD - standardDev)/maxSelfSD
        ohs = (maxSD - standardDev)/maxSD
        # as variance approaches 0, lhs approaches 1
        # as variance approaches maxVariance, lhs approaches 0
        # ^this option saw far worse rank variation between teams

        lhs = (maxMeanDiff-math.fabs(selfAvgRank-avgRank))/maxMeanDiff
        rhs = Team.getAvgBenefit(self.members)
        #return lhs*rhs*ohs
        return lhs*rhs

    def __repr__(self):
        return "{} {}".format(self.name, self.members)


def getAvgRank(teams: list):
    return sum(t.getAvgRank() for t in teams)/len(teams)

def getAvgUtility(teams, avgRank):
    return sum(t.getUtility(avgRank) for t in teams)/len(teams)

def genRandomPlayers(numPlayers):
    players = [] #this will have a length of numplayers
    # but we cannot specify array lengths at construction in python

    for i in range(numPlayers):
        roles = list(Lanes)
        randomRole = lambda : roles.pop(random.randint(0,len(roles)-1))
        role1 = randomRole()
        role2 = randomRole()
        #role1 =/= role2

        rankIndex = random.randint(1,len(Divisions)-1)
        rank = Divisions[rankIndex]
        if rankIndex<5:
            #if not challenger or master, add subdivision
            rank+=str(random.randint(1,5))
        '''
        rankIndex = random.randint(1,100*100)/100
        #100*100 = 00.00, 00.01, 00.02... etc *100
        # ie 2 decimal point nums
        rankDist = getRankDist()
        for tupRange in rankDist.keys():
            if tupRange[0]<=rankIndex<=tupRange[1]:
                rank = rankDist[tupRange]
                break
        '''
        name = "Player {}".format(i+1)
        players.append(Player(name,rank,role1,role2))
    return players

def raiseUtility(team1, team2, avgRank, key: int)->bool:
    ar = avgRank
    def _swapPlayers1(p1,p2):
        t1,t2 = p1.getTeam(), p2.getTeam()
        t1.removePlayer(p1)
        t2.removePlayer(p2)
        t1.addPlayer(p2)
        t2.addPlayer(p1)

    def _swapPlayers2(t1p1, t1p2, t2p1, t2p2):
        assert(t1p1.getTeam()==t1p2.getTeam())
        assert(t2p1.getTeam()==t2p2.getTeam())
        t1,t2 = t1p1.getTeam(), t2p1.getTeam()
        
        t1.removePlayer(t1p1)
        t1.removePlayer(t1p2)
        
        t2.removePlayer(t2p1)
        t2.removePlayer(t2p2)
        
        t1.addPlayer(t2p1)
        t1.addPlayer(t2p2)

        t2.addPlayer(t1p1)
        t2.addPlayer(t1p2)

    absD = lambda x,y: math.fabs(x-y)

    if key==1:
        for p1 in team1.getMembers().values():
            for p2 in team2.getMembers().values():
                avgUtilityOld = getAvgUtility([team1,team2],avgRank)
                _swapPlayers1(p1,p2)
                                      
                t1PreOptimise = team1.getMembers()
                t2PreOptimise = team2.getMembers()
                team1.optimiseUtility()
                team2.optimiseUtility()
                
                #these operations can be done in parallel if multithreading --
                # my understanding is python has something called a
                # global interpretor lock, which implies processors may only
                # work on a single python thread at a time anyway
                avgUtilityNew = getAvgUtility([team1,team2],avgRank)
                deltaUtility = avgUtilityNew - avgUtilityOld
                #if deltaUtility<=0:
                if deltaUtility>0:
                    # it isn't strictly smaller, because if
                    # we allow for equal changes in utility
                    # there will be an infinite loop
                    # as teams switch and then switch back
                    # players
                    return deltaUtility
                team1.revert(t1PreOptimise)
                team2.revert(t2PreOptimise)
                _swapPlayers1(p2,p1)
    else:
        assert(key==2)
        membersT1 = list(team1.getMembers().values())
        membersT2 = list(team2.getMembers().values())

        for t1p1 in membersT1[:-1]:
            for t1p2 in membersT1[membersT1.index(t1p1)+1:]:
                # this gives unique combinations of t1p1 and t1p2
                # the other way to do this would be to copy
                # the list each iteration of the loop and pop
                # values, like in the main function
                for t2p1 in membersT2[:-1]:
                    for t2p2 in membersT2[membersT2.index(t2p1)+1:]:
                        avgUtilityOld = getAvgUtility([team1,team2],avgRank)
                        
                        _swapPlayers2(t1p1,t1p2,t2p1,t2p2)
                        t1PreOptimise = team1.getMembers()
                        t2PreOptimise = team2.getMembers()
                        team1.optimiseUtility()
                        team2.optimiseUtility()
                        avgUtilityNew = getAvgUtility([team1,team2],avgRank)
                        
                        deltaUtility = avgUtilityNew - avgUtilityOld
                        #if deltaUtility<=0:
                        if deltaUtility>0:
                            return deltaUtility
                        team1.revert(t1PreOptimise)
                        team2.revert(t2PreOptimise)
                        _swapPlayers2(t2p1,t2p2,t1p1,t1p2)
                        
    #loop hasn't broken by return statement
    return 0

def manual_swap_team(t1,t2,avgRank):
    ar = avgRank
    
    def _swapPlayers1(p1,p2):
        t1,t2 = p1.getTeam(), p2.getTeam()
        t1.removePlayer(p1)
        t2.removePlayer(p2)
        t1.addPlayer(p2)
        t2.addPlayer(p1)

    absD = lambda x,y: math.fabs(x-y)
    avgUtilDist = lambda t1,t2: sum(absD(t.getUtility(ar),avgU) for t in (t1,t2))/2
    for p1 in team1.getMembers().values():
        for p2 in team2.getMembers().values():
            avgUtilityOld = getAvgUtility([team1,team2],avgRank)
            _swapPlayers1(p1,p2)

            avgDistOld = avgUtilDist(team1,team2)
                                  
            t1PreOptimise = team1.getMembers()
            t2PreOptimise = team2.getMembers()
            team1.optimiseUtility()
            team2.optimiseUtility()

            avgDistNew = avgUtilDist(team1,team2)
            print('t1: {}'.format(team1))
            print('t2: {}'.format(team2))
            print('t1 util: {}, t2 util: {}'.format(team1.getUtility(ar),team2.getUtility(ar)))
            avgUtilityNew = getAvgUtility([team1,team2],avgRank)
            deltaUtility = avgUtilityNew - avgUtilityOld
            print('delta util: {}'.format(deltaUtility))

            if deltaUtility>0 and avgDistNew >= avgDistOld:
                return deltaUtility
            
            team1.revert(t1PreOptimise)
            team2.revert(t2PreOptimise)
            _swapPlayers1(p2,p1)

def manual_swap_player(p1,p2,avgRank):
    ar = avgRank
    
    def _swapPlayers1(p1,p2):
        t1,t2 = p1.getTeam(), p2.getTeam()
        t1.removePlayer(p1)
        t2.removePlayer(p2)
        t1.addPlayer(p2)
        t2.addPlayer(p1)

    absD = lambda x,y: math.fabs(x-y)
    avgUtilDist = lambda t1,t2: sum(absD(t.getUtility(ar),avgU) for t in (t1,t2))/2
    avgUtilityOld = getAvgUtility([team1,team2],avgRank)
    _swapPlayers1(p1,p2)

    avgDistOld = avgUtilDist(team1,team2)
                          
    t1PreOptimise = team1.getMembers()
    t2PreOptimise = team2.getMembers()
    team1.optimiseUtility()
    team2.optimiseUtility()

    avgDistNew = avgUtilDist(team1,team2)
    print('t1: {}'.format(team1))
    print('t2: {}'.format(team2))
    print('t1 util: {}, t2 util: {}'.format(team1.getUtility(ar),team2.getUtility(ar)))
    avgUtilityNew = getAvgUtility([team1,team2],avgRank)
    deltaUtility = avgUtilityNew - avgUtilityOld
    print('delta util: {}'.format(deltaUtility))

    if deltaUtility>0 and avgDistNew >= avgDistOld:
        return deltaUtility
    
    team1.revert(t1PreOptimise)
    team2.revert(t2PreOptimise)
    _swapPlayers1(p2,p1)

def teamStr(teams,avgRank):
    s=""
    for team in teams:
            s+="\n"+team.name+"\n"
            teamAvgRank = team.getAvgRank()
            rank = Rank.rankIntToStr(teamAvgRank)
            #s+="Team utility: {}\n".format(round(team.getUtility(avgRank),4))
            s+="Average rank: {}\n".format(rank)
            sd = round(team.getVariance(avgRank)**0.5,5)
            s+="Standard deviation of rank: {}\n{}\n".format(sd,"-"*60)
            members = team.getMembers()
            for role in members.keys():
                    p = members[role]
                    fs = "actual role: {} | pref1: {}, pref2: {} | rank: {}"
                    s+=fs.format(role, p.getPrefRole1(), p.getPrefRole2(), Rank.rankIntToStr(p.getRank()))+'\n'
    return s

def teamStatStr(teams)->str:
    s=''
    totalFirstPref = 0
    totalSecondPref = 0
    teamAvgs = []
    for team in teams:
        teamAvgs.append(team.getAvgRank())
        for role in team.getMembers().keys():
            player = team.getMembers()[role]
            if role == player.getPrefRole1():
                totalFirstPref+=1
            elif role == player.getPrefRole2():
                totalSecondPref+=1
    prefStr = lambda x,y: "Players who got {} pref: {}/{} ~ {}%"\
        .format(x,y,numPlayers,round(y*100/numPlayers,2))
    s = prefStr('first',totalFirstPref) + "\n"
    s += prefStr('first or second',totalSecondPref+totalFirstPref)+'\n'
    
    sd = round(getSDOfTeamRank(teamAvgs,avgRank),5)
    s=''.join((s,("Standard deviation of team ranks: {}\n".format(sd))))
    
    utility = round(getAvgUtility(teams,getAvgRank(teams)),5)
    s=''.join((s,("Average team utility: {}".format(utility))))
    return s

def getRankDist():
    r = [] #[(division,winrate),...]
    
    getNonCaptureGroups = lambda x: "".join("(?:{})|".format(s) for s in x)[:-1]
    #[:-1] to remove | at the end

    subDivisions = getNonCaptureGroups(('I','II','III','IV','V'))
    noSub = getNonCaptureGroups(('Challenger','Master +I'))
    withSub = getNonCaptureGroups(('Bronze','Silver',\
        'Gold','Platinum','Diamond'))

    regexp1 = "(?:((?:{}|(?:(?:{}) +(?:{})))) *\t*)+".format(noSub,\
        withSub,subDivisions)
    regexp2 = "(?: *\t*)(?:(\d*\d\.\d\d)%)+"

    regex="".join((regexp1,regexp2))
    
    with open("playrates.txt") as f:
        lines = f.readlines()
        
    lines = [x.strip() for x in lines]
    state = 0
    for line in lines:
        m =  re.match(regex,line)
        if m!=None:
            playRate = round(float(m.group(2)),2)
            r.insert(0,(m.group(1),playRate))
            #reverse list

    rCumm = []

    for i in range(len(r)):
        rCumm.append((r[i][0],sum(x[1] for x in r[:i+1])))
        
    dicRankRanges = {(0,rCumm[0][1]):rCumm[0][0]}

    for i in range(1,len(rCumm)):
        dicRankRanges[(rCumm[i-1][1],rCumm[i][1])]=rCumm[i][0]

    return dicRankRanges

def getSDOfTeamRank(teamRanks, avgRank):
    summ = 0
    for rank in teamRanks:
        summ+=(rank-avgRank)**2
    return (summ/len(teamRanks))**0.5

def getSampleSD(iterable):
    average = sum(iterable)/len(iterable)
    summ = 0
    for num in iterable:
        summ+=(num-average)**2
    return (summ/(len(iterable)-1))**0.5
    #same as getPopSD but minus 1 degree of freedom

def getPopSD(iterable):
    average = sum(iterable)/len(iterable)
    summ = sum((num-average)**2 for num in iterable)
    return (summ/len(iterable))**0.5


if __name__ == "__main__":
    
    numPlayers = 80
    numTeams = int(numPlayers//len(Lanes))
    print("Players to be placed {}, {} players will be left over"\
          .format(numPlayers-(numPlayers%5),numPlayers%5))
    players = genRandomPlayers(numPlayers)
    players2 = players.copy()
    teams = []
    teamsChanged = [True for _ in range(numTeams)]
    # teams changed is a list that says if a team has changed
    # in the last round(loop) of swapping
    # when comparing 2 teams.
    
    # we know that each round every team is compared against each other--
    # if they both haven't changed in the last round of swapping,
    # then we don't need to compare them again: 
    # improving runtime
    for i in range(numPlayers//5):
        teams.append(Team("Team {}".format(i+1)))
        for i in range(5):
            teams[-1].addPlayer(players.pop(),Lanes[i])
    avgRank = getAvgRank(teams) #constant
    ar = avgRank
    #print(teams)
    team1Str = teamStr(teams,avgRank)
    team1StatStr = teamStatStr(teams)
    changed=True
    state = 0
    print(team1Str)
    print(team1StatStr)
    input('\nPress enter to continue...')
    print("Avg utility (state=0):")
    start = time.time()
    utility = getAvgUtility(teams,avgRank)
    statement = lambda s: "changed to state {}".format(s)
    avgF = lambda iterable: sum(iterable)/len(iterable)
    
    teamUtilities = [team.getUtility(avgRank) for team in teams]
    utilityAvg = avgF(teamUtilities)
    utilitySD = getPopSD(teamUtilities)
    getTeamChanged = lambda t: teamsChanged(teams.index(t))

    avgF = lambda iterable: sum(iterable)/len(iterable)
    
    while(state!=3):
        teamsChanged = [True for _ in range(numTeams)]
        teamsCopy = teams.copy()
        changed = False
        #while(len(teamsCopy)>1 and not changed):
        while(len(teamsCopy)>1):
            team1 = teamsCopy.pop()
            for team2 in teamsCopy:
                t1Index = teams.index(team1)
                t2Index = teams.index(team2)
                if not(teamsChanged[t1Index] and teamsChanged[t2Index]):
                    # if none of the two have changed in the last loop,
                    # no point in trying to permutate them again
                    
                    # teamsChanged is initialised with True
                    
                    # I was very surprised, runtime went from
                    # 2-4 minutes to less than 20 seconds with
                    # this change implemented
                    continue
                #print('{} {}'.format(team1.name,team2.name))
                if state==0:
                    result = raiseUtility(team1, team2, avgRank, 1)
                elif state==1:
                    result = raiseUtility(team1, team2, avgRank, 2)
                elif state==2:
                    result = raiseUtility(team1, team2, avgRank, 1)
                changed = changed or result
                teamsChanged[t1Index] = result
                teamsChanged[t2Index] = result
                
                if result:
                    print("\tchange in utility: {}".format(result))
                    #print(getAvgUtility(teams,avgRank))
                    teamUtilities[t1Index]=team1.getUtility(ar)
                    teamUtilities[t2Index]=team2.getUtility(ar)
                    # only change value
                    #utilitySD = getPopSD(teamUtilities)
                    result = False
                    #break
        if not changed:
            state+=1
            print(statement(state))
        elif state==2:
            state=1
            print(statement(state))
    finish = time.time()
    team2Str = teamStr(teams,avgRank)
    team2StatStr = teamStatStr(teams)
    print("\nOld layout:\n")
    print(team1Str)
    print(team1StatStr+"\n")
    print("="*60)
    print("\nNew layout:\n")
    print(team2Str)
    print(team2StatStr)
    print("\nOverall average rank: {}".format(Rank.rankIntToStr(avgRank)))
    timeSecs = round((finish-start),2)
    minutes = "{} minutes and ".format(int(timeSecs//60)) if timeSecs>60 else ''
    print("Time elapsed: {}{} seconds".format(minutes, round(timeSecs%60)))
    input("Press enter to exit.")
