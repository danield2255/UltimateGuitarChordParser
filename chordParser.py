import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import glob
import time

def transposeToC(driver, key, capo):
    majKeys = ['A', "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    transposes = driver.find_elements_by_tag_name("button")
    for t in transposes:
        if t.text== "−1":
            transposeDown= t
        elif t.text == "+1":
            transposeUp = t
   
    #Check flats
    if "b" in key:
        flatKeys = ['A', "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]
        index = flatKeys.index(key[:2])
        newKey = majKeys[index]
        if "m" in key or "M" in key:
            key = newKey + 'm'
        else:
            key = newKey
            
    #if key is minor, make it its relative major
    if "m" in key or "M" in key:
        oldKey = key.replace('m', "")
        index = majKeys.index(oldKey)
        index = (index + 3)%12
        key = majKeys[index]
    #Now in a major key
    
    if key == 'C':
        return driver
    #account for the capo if it is present, without transposing
    elif capo != 0:
        index = (majKeys.index(key) - capo)
        if index < 0: 
            key = majKeys[12 + index]
        else:
            key = majKeys[index]
    if key == 'C':
        return driver
    elif key in ["F#", "G", "G#", 'A', "A#", "B"]:
        while key != "C":
            index = (majKeys.index(key) + 1)%12
            time.sleep(6)
            transposeUp.click()
            key = majKeys[index]
    elif key in ["C#", "D", "D#", "E", "F"]:
        while key != "C":
            index = (majKeys.index(key) - 1)
            time.sleep(6)
            transposeDown.click()
            key = majKeys[index]
    time.sleep(5)
    return driver
        
    
    
def diatonicPattern(chords):
    cMaj = ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]
    numerals = ["I", "ii", "iii", "IV", "V", "vi", "VII"]
    noExtend=[]
    nonDiatonic = 0
    
    for val in chords:
        if '/' in val:
            if 'm/' in val:
                val = val[0:2]
            else:
                val = val[0]
        noExtend.append(''.join([i for i in val if not i.isdigit()]).replace("maj", "").replace("sus", "").replace('dim', "").replace('aug', "").replace('(', "").replace(')', "").replace('add',""))

    numbers = ""
    last = ""
    prog = []
    for number in noExtend:
        if number != last:
            prog.append(number)
        last = number
    for c in prog:
        try:
            numbers = numbers + "-" + numerals[cMaj.index(c)]
        except:
            cMajStripped = ["C", "D", "E", "F", "G", "A", "B"]
            nonDiatonic += 1
            suffix = ""
            if "#" in c:
                c = c.replace("#", "")
                suffix += "#"
            elif "b" in c:
                c = c.replace('b', "")
                suffix += "b"
            if 'dim' in c:
                c = c.replace('dim', "")
                suffix += ' dim'
            elif 'aug' in c:
                c = c.replace('aug', "")
                suffix += "aug"
            if 'm' in c:
                minor = True
                c = c.replace("m", "")
            elif "M" in c:
                minor = True
                c = c.replace("M", "")
            else:
                minor = False
            #need to handle a major where there should not be one or minor where there should not be one
            if minor: 
                numbers = numbers + "-"+ numerals[cMajStripped.index(c)].lower()+suffix
            else:
                numbers = numbers + "-"+ numerals[cMajStripped.index(c)].upper()+suffix
    return numbers[1:], nonDiatonic

#Function to turn dictionary key value pairs into dataframe rows
def dictToDF(data, song, artist):
    df = pd.DataFrame(columns = ['Name', "Artist", "Section", "Progression", "EndDifferent", "NumSectionChords", "nonDiatonicChords", "extendedChords"])
    for key, value in data.items():
        if value == []:
            continue
        df = df.append({'Name':song, "Artist":artist, "Section":key, "Progression":value[0], "EndDifferent":value[1], "NumSectionChords":value[2], "nonDiatonicChords":value[3], "extendedChords":value[4]}, ignore_index = True)
    return df


def scrapeUltimateGuitar(wd, song, artist):
    url = 'https://www.ultimate-guitar.com/'
    wd.get(url)
    time.sleep(2)
    #Search for the song name 
    searchBarPath = '/html/body/div[1]/div/div/div[2]/div/div/div/p[2]/form/div[2]/input'
    searchBar =  wd.find_element_by_tag_name("input")
    searchBar.send_keys(artist+ " "+song)
    searchBar.send_keys(Keys.ENTER)
    time.sleep(2)
    #Search Chords only 
    try:
        chordsPath = "/html/body/div[1]/div/div/div[2]/main/div[2]/div[3]/section/nav/div[1]/nav/a[2]"
        chords = wd.find_element_by_xpath(chordsPath)
        chords.click()
        time.sleep(2)
    except:
        try:
            button  = wd.find_element_by_xpath("/html/body/div[1]/div/a[2]")
            button.click()
            time.sleep
        except:
            print("need to wait")
            try:
                time.sleep(20)
                chords = wd.find_element_by_xpath(chordsPath)
                chords.click()
            except:
                print("There was no chords button")
    
    #Pick the top rated listing
    time.sleep(2)
    try:
        bestPath = "/html/body/div[1]/div/div/div[2]/main/div[2]/div[3]/section/nav/div[2]/nav/a[2]"
        highestRated = wd.find_element_by_xpath(bestPath)
        highestRated.click()
        time.sleep(2)
    except:
        try:
            button  = wd.find_element_by_xpath("/html/body/div[1]/div/a[2]")
            button.click()
            time.sleep
        except:
            print("need to wait")
            try:
                time.sleep(20)
                highestRated = wd.find_element_by_xpath(bestPath)
                highestRated.click()
            except:
                print("ERROR OUT")
    ad = False
    if BeautifulSoup(wd.page_source, 'html.parser').find('title') == "Advertising Page":
        ad =True
        print('ad pops up')
        time.sleep(41)
    curHTML = wd.page_source
    curSoup = BeautifulSoup(curHTML, 'html.parser')
    valid = False
    header = True
    data = None
   #for listing in curSoup.find_all('div', attrs = {'class': '_2vnXR'}):
    for listing in curSoup.find_all('div', attrs = {'class': 'pZcWD'}):
        if header:
            header = False
            continue
        #for form in listing.find_all('div', attrs = {'class':"s2__B _3grw4"}):
        for form in listing.find_all('div', attrs = {'class':"_3g0_K _1_CWK"}):
            tabType = form.get_text()
        if tabType.lower() == "chords":
            valid = True
            link = listing.find('a', href = True)['href']
            wd.get(link)
            #At this point, we are on the actual tab
            data = chordScraper(wd)
            if data == None:
                wd.execute_script("window.history.go(-1)")
                time.sleep(5)
            else:
                return data
    if not valid:
        print("It does not seem that there is a chord tab for the song " + song + " by " + artist + " on UltimateGuitarTab.com")
        return None
    
    
def chordScraper(wd):
    html = wd.page_source
    soup = BeautifulSoup(html, 'html.parser')
    time.sleep(16)
    #Get key data
    key = ""
    capo = 0
    for headerLine in soup.find_all('div', attrs ={'class':'_2EcLF'}):
        if headerLine.get_text()[0:5] == "Capo:":
            capo = int(headerLine.get_text()[6])
        if headerLine.get_text()[0:4] =="Key:":
            key = headerLine.get_text()[5:].strip()
            break
    if key == "":
        #this isn't a valid tab really, we cant standardize it ---> make it go to the next one
        print("NOT A VALID TAB")
        return None
    
    #standardize the key
    transposeToC(wd, key, capo)
    #Now should be in C major

    body = BeautifulSoup(wd.page_source, 'html.parser').find('pre', attrs ={'class':'_3zygO'})

    #Try to split into different sections
    secs = ["Intro", "Hook","Verse","Chorus","Pre-Chorus","Post-Chorus", "Bridge", "Interlude","Solo","Outro"]
    regex = "\[(.*?)\]"
    sections = re.split(regex,str(body))

    data = {} #Data will be held in a dictionary with the key being the section, and the value being a list of the progression, the end (this one will be None if the end is the same as the whole thing), number of chords in the section, number of nondiatonic chords and number of extended chords 
    secDataNext=False
    secLabel = ""
    #Try to define sections
    for sec in sections:
        #have to take digits away from string to make it see verse 1 and verse 2 as equal for example
        secMod = ''.join([i for i in sec if not i.isdigit()])
        if secMod.strip() in secs:
            #detect if we are actually just finding the label
            secLabel = secMod
            if secLabel not in data.keys():
                data[secLabel] = []
                secDataNext = True
        else:
            miniSoup = BeautifulSoup(sec, 'html.parser')
            secChords= []
            if len(miniSoup.find_all('span', attrs ={'class':'_3bHP1 _3ffP6'})) == 0:
                #This means we are looking at a section of the tab that is not a section label, and does not have any chords
                print('there is nothing useful in this section')
                continue
            for item in miniSoup.find_all('span', attrs ={'class':'_3bHP1 _3ffP6'}):
                chord = item.get_text()
            
                try:
                    secChords.append(chord.strip())
                except:
                    pass

            progression = []
            chords = []
            for c in range(len(secChords)):
                progression.append(secChords[c])
                if c == len(secChords)-1 and chords == []:
                    chords = secChords
                #check if this is the point of circular nature in the progression
                elif len(progression) > 1 and progression[-1] == progression[0]:
                    progLen = len(progression) -1 
                    qualify = True
                    for i in range(progLen):
                        if len(secChords)-1 < progLen + i: 
                            #Then this is the progression
                            chords = secChords
                        #check to see if this pattern repeats itself
                        elif secChords[i] != secChords[progLen + i]:
                            qualify= False
                            break
                    if qualify:
                        chords = progression[:-1]
                        print("Chords are : " + str(chords))
                        break
            if chords == []:
                chords = progression
                        
            #See if the end of the progression is different at all
            end = []
            i = len(chords) -1
            if secChords[-1] == chords[i]:
                if i == len(chords) -1 and i != 0 and secChords[-2] != chords[i-1]: 
                    end = [secChords[-2] , secChords[-1]]
                    counter1 = len(chords) - 3
                    counter2 = -3
                    while secChords[counter2] !=chords[counter1] and counter1 > 0:
                        end = [secChords[counter2]]+ end
                        counter1 -= 1
                        counter2 -= 1
            else:
                end = [secChords[-1]]
                counter1 = len(chords) - 2
                counter2 = -1
                while secChords[counter2] != chords[counter1] and counter1 > 0:
                    end = [secChords[counter2]] + end
                    counter1 -= 1
                    counter2 -= 1
            
            #count extended chords, do not consider the 5 extension, as it is just a part of regular major/minor chord 
            extendedChords = 0
            if end != []:
                for val in end:
                    if not "5" in val and (''.join([i for i in val if i.isdigit()]) != "" or 'sus' in val or 'add' in val):
                        extendedChords += 1
                        val.replace("sus", "")
                    elif '/' in val:
                        extendedChords += 1

            for val in chords:
                if not "5" in val and (''.join([i for i in val if i.isdigit()]) != "" or 'sus' in val or 'add' in val):
                    extendedChords += 1
                    val.replace("sus", "")
                elif '/' in val:
                    extendedChords += 1
            
            #Get number of non-diatonic chords and get the chord pattern in notation
            chords, outKey1 = diatonicPattern(chords)
            
            #do the same for the end pattern
            end, outKey2 = diatonicPattern(end)
            nonDiatonicChords = outKey1 + outKey2
            
            if end == "":
                end = None
            if secDataNext:
                data[secLabel]= [chords, end, len(set(secChords)), nonDiatonicChords, extendedChords]
                secDataNext = False
            if secLabel in list(data.keys()) and data[secLabel] == []:
                print("EMPTY SECTION")
                del data[secLabel]
    return data



def scrapeSongChords(inputArtists):#Returns the data on each section of each song in the scrapeSongs.csv file by any of the input artists
    option = webdriver.ChromeOptions()
    option.add_argument('--incognito')
    wd = webdriver.Chrome('dependencies/chromedriver', options = option)
    scrapeSongs = pd.DataFrame(pd.read_csv("data/scrapeSongs.csv"))
    done = []
    for index, row in scrapeSongs.iterrows():
        if row['Artists'] in inputArtists and (row["Name"], row['Artists']) not in done:
            try:
                data = scrapeUltimateGuitar(wd, row["Name"], row['Artists'])
            except:
                print("Diverted from site")
                done.append((row["Name"], row['Artists']))
                continue
            if data == None:
                done.append((row["Name"], row['Artists']))
                continue
            else:
                df = dictToDF(data,row["Name"], row['Artists'])
                done.append((row["Name"], row['Artists']))
                cur = row["Name"] + "-" + row['Artists']
                df.to_csv("data/songData/{0}.csv".format(cur), encoding='utf-8')
    files = [file for file in glob.glob('data/songData/*.csv')]
    try:
        finalFile = pd.concat([pd.read_csv(file) for file in files])
        finalFile.to_csv('data/songSections.csv')
    except:
        print("No valid tabs were found and there were no songs already saved, try searching for different songs!")


def main():
    inputArtists =["Ed Sheeran"]
    scrapeSongChords(inputArtists)

if __name__ == "__main__":
    main()