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
from seleniumbase import SB

def verify_success(sb):
    sb.assert_element('img[alt="Logo Assembly"]', timeout=4)
    sb.sleep(4)


def scrape_ultimate_guitar(web_driver, song, artist):
    """Parent function to scrape the chord progression of a single song from ultimate-guitar.com

    Args:
        web_driver (selenium.webdriver): The webdriver instance
        song (str): The name of the song to scrape
        artist (str): The name of the artist who performed the song

    Returns:
        dict: A dictionary containing the scraped chord data
    """
    
    search_string = str(song + " " + artist).replace(" ", "+")
    search_url = f"https://www.ultimate-guitar.com/search.php?title={search_string}&type%5B0%5D=300&page=1&order=myweight"
    web_driver.uc_open_with_reconnect(search_url, 3)
    time.sleep(4)

    print("Searching for " + song + " by " + artist)

    #Pick the top rated listing
    time.sleep(4)
    print("Picking the top rated listing")
    row_num = 1
    on_usable_tab = False
    while not on_usable_tab or row_num > 5:
        print("Trying listing number " + str(row_num))
        try:
            try:
                web_driver.click(f"/html/body/div/div[2]/main/div/div[2]/section/article/div/div[{row_num}]/div[2]/header/span/span/a")
                time.sleep(4)
            except:
                try:
                    print("Trying alternative XPath")
                    web_driver.click("/html/body/div/div[2]/main/div/div[2]/section/article/div/div[2]/div[2]/header/span/span/a")
                    time.sleep
                except:
                    print("need to wait")
            ad = False
            if BeautifulSoup(web_driver.driver.page_source, 'html.parser').find('title') == "Advertising Page":
                ad =True
                print('AD POPS UP')
                time.sleep(41)
            cur_html = web_driver.driver.page_source
            cur_soup = BeautifulSoup(cur_html, 'html.parser')
            if len(cur_soup.find_all(string="Transpose")) == 0:
                print('not on tab yet')
                raise Exception("Not on tab")
            print("MADE IT TO THE TAB")
            #At this point, we are on the actual tab
            print("SCRAPE CHORDS")
            data = scrape_chords(web_driver)
            if data != None:
                on_usable_tab = True
            else:
                raise Exception("Not a usable tab")
        except Exception as e:
            print(f"Error with listing number {row_num} with error: {e}")
            row_num += 1
            print("Trying the next best listing")
            web_driver.uc_open_with_reconnect(search_url, 3)
            time.sleep(5)
    return data
    

def scrape_chords(web_driver):
    """Runs when you are on the webpage you want to scrape. Scrapes the chord data of the song transposed to the key of C major

    Args:
        web_driver (selenium.webdriver): The webdriver instance

    Returns:
        dict: A dictionary containing the scraped chord data
    """
    time.sleep(4)
    html = web_driver.driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    #Get key and capo data
    key = ""
    capo = 0
    for header_line in soup.find_all('div', attrs ={'class':'CCUPL'}): 
        print(header_line.get_text())
        if "Capo:" in header_line.get_text():
            try:
                capo = int(header_line.get_text().split("Capo:")[1].strip()[0])
            except:
                capo = 0
        if "Key:" in header_line.get_text():
            key = header_line.get_text().split("Key: ")[1].strip().split("Capo")[0]
            break
        # Old Format
        # if header_line.get_text()[0:5] == "Capo:":
        #     capo = int(header_line.get_text()[6])
        # if header_line.get_text()[0:4] =="Key:":
        #     key = header_line.get_text()[5:].strip()
        #     break
    print("KEY: " + key)
    print("CAPO: " + str(capo))
    if key == "":
        #this isn't a valid tab really, we cant standardize it ---> make it go to the next one
        print("NOT A VALID TAB")
        return None
    
    #standardize the key to C major
    transpose_to_C(web_driver, key, capo)
    #Now should be in C major

    body = BeautifulSoup(web_driver.driver.page_source, 'html.parser').find('pre', attrs ={'class':'_3zygO'})

    #Try to split into different song sections
    secs = ["Intro", "Hook","Verse","Chorus","Pre-Chorus","Post-Chorus", "Bridge", "Interlude","Solo","Outro"]
    regex = "\[(.*?)\]"
    sections = re.split(regex,str(body))


    #Data will be held in a dictionary with the key being the section, and the value being a list of the progression,
    #   the end (this one will be None if the end is the same as the whole thing), number of chords in the section, 
    #   number of non_diatonic chords and number of extended chords 
    data = {} 
    sec_data_next=False
    sec_label = ""
    #Try to define sections
    for sec in sections:
        #have to take digits away from string to make it see verse 1 and verse 2 as equal for example
        sec_mod = ''.join([i for i in sec if not i.isdigit()])
        if sec_mod.strip() in secs:
            #detect if we are actually just finding the label
            sec_label = sec_mod
            if sec_label not in data.keys():
                data[sec_label] = []
                sec_data_next = True
        else:
            mini_soup = BeautifulSoup(sec, 'html.parser')
            sec_chords= []
            if len(mini_soup.find_all('span', attrs ={'class':'_3bHP1 _3ffP6'})) == 0:
                #This means we are looking at a section of the tab that is not a section label, and does not have any chords
                print('there is nothing useful in this section')
                continue
            for item in mini_soup.find_all('span', attrs ={'class':'_3bHP1 _3ffP6'}):
                chord = item.get_text()
            
                try:
                    sec_chords.append(chord.strip())
                except:
                    pass

            progression = []
            chords = []
            for c in range(len(sec_chords)):
                progression.append(sec_chords[c])
                if c == len(sec_chords)-1 and chords == []:
                    chords = sec_chords
                #check if this is the point of circular nature in the chord progression
                elif len(progression) > 1 and progression[-1] == progression[0]:
                    progLen = len(progression) -1 
                    qualify = True
                    for i in range(progLen):
                        if len(sec_chords)-1 < progLen + i: 
                            #Then this is the progression
                            chords = sec_chords
                        #check to see if this pattern repeats itself
                        elif sec_chords[i] != sec_chords[progLen + i]:
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
            if sec_chords[-1] == chords[i]:
                if i == len(chords) -1 and i != 0 and sec_chords[-2] != chords[i-1]: 
                    end = [sec_chords[-2] , sec_chords[-1]]
                    counter1 = len(chords) - 3
                    counter2 = -3
                    while sec_chords[counter2] !=chords[counter1] and counter1 > 0:
                        end = [sec_chords[counter2]]+ end
                        counter1 -= 1
                        counter2 -= 1
            else:
                end = [sec_chords[-1]]
                counter1 = len(chords) - 2
                counter2 = -1
                while sec_chords[counter2] != chords[counter1] and counter1 > 0:
                    end = [sec_chords[counter2]] + end
                    counter1 -= 1
                    counter2 -= 1
            
            #count extended chords, do not consider the 5 extension, as it is just a part of regular major/minor chord 
            extended_chords = 0
            if end != []:
                for val in end:
                    if not "5" in val and (''.join([i for i in val if i.isdigit()]) != "" or 'sus' in val or 'add' in val):
                        extended_chords += 1
                        val.replace("sus", "")
                    elif '/' in val:
                        extended_chords += 1

            for val in chords:
                if not "5" in val and (''.join([i for i in val if i.isdigit()]) != "" or 'sus' in val or 'add' in val):
                    extended_chords += 1
                    val.replace("sus", "")
                elif '/' in val:
                    extended_chords += 1
            
            #Get number of non-diatonic chords and get the chord pattern in notation
            chords, out_key_1 = diatonic_pattern(chords)
            
            #do the same for the end pattern
            end, out_key_2 = diatonic_pattern(end)
            nondiatonic_chords = out_key_1 + out_key_2
            
            if end == "":
                end = None
            if sec_data_next:
                data[sec_label]= [chords, end, len(set(sec_chords)), nondiatonic_chords, extended_chords]
                sec_data_next = False
            if sec_label in list(data.keys()) and data[sec_label] == []:
                print("EMPTY SECTION")
                del data[sec_label]
    return data

def scrape_song_chords(input_artists):
    """Will only get the data on each section of each song in the scrape_songs.csv file. 

    Args:
        input_artists (list): A list of artist names to scrape chords for
    """
    scrape_songs = pd.DataFrame(pd.read_csv("data/scrape_songs.csv"))
    done = []

    with SB(uc=True) as sb:
        for index, row in scrape_songs.iterrows():
            print("Currently on song " + row["Name"] + " by " + row['Artists'])
            if row['Artists'] in input_artists and (row["Name"], row['Artists']) not in done:
                try:
                    data = scrape_ultimate_guitar(sb, row["Name"], row['Artists'])
                except Exception as e:
                    print(f"Diverted from site with error: {e}")
                    done.append((row["Name"], row['Artists']))
                    continue
                if data == None:
                    done.append((row["Name"], row['Artists']))
                    continue
                else:
                    df = dict_to_df(data,row["Name"], row['Artists'])
                    done.append((row["Name"], row['Artists']))
                    cur = row["Name"] + "-" + row['Artists']
                    #Save the file of the song's data
                    print("Saving data for " + row["Name"] + " by " + row['Artists'])
                    df.to_csv("data/songData/{0}.csv".format(cur), encoding='utf-8')
            print("Done with " + row["Name"] + " by " + row['Artists'])
    files = [file for file in glob.glob('data/songData/*.csv')]
    try:
        final_file = pd.concat([pd.read_csv(file) for file in files])
        final_file.to_csv('data/songSections.csv')
    except:
        print("No valid tabs were found and there were no songs already saved, try searching for different songs!")



def transpose_to_C(web_driver, key, capo):
    """Transpose the current chord sheet to the Key of C major

    Args:
        web_driver (seleniumbase.webdriver): Webdriver that is currently on the page of the tab you want to transpose
        key (str): The key that the tab originally is in.
        capo (int): The fret number of the capo, if there is one. If there is no capo, should be 0.

    Returns:
        web_driver (seleniumbase.webdriver): The updated webdriver after transposing the chords
    """
    maj_keys = ['A', "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    time.sleep(5)
    print("ABOUT TO CLICK DISMISS")
    print(web_driver.find_elements(By.CSS_SELECTOR, '.GZm7j.KKBhY._8WVi7._6yJZx.wQpuI._4XUk_'))
    try:    
        dismiss = web_driver.find_elements(By.CSS_SELECTOR, '.GZm7j.KKBhY._8WVi7._6yJZx.wQpuI._4XUk_')[0]
        print("DISMISS: " + str(dismiss))
        web_driver.driver.execute_script("arguments[0].click();", dismiss)
    except Exception as e:
        print(f"Could not click out of ad with error: {e}")
    print("CLICKED DISMISS")
    time.sleep(2)
    transposes = web_driver.find_elements(By.CSS_SELECTOR, '.GZm7j.KKBhY._8WVi7._6yJZx.wQpuI._4XUk_')
    transpose_up = transposes[3]
    transpose_down = transposes[2]
    
    #Check for if the key is flat, and then turn it to its corresponding sharp key
    if "b" in key:
        flat_keys = ['A', "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]
        index = flat_keys.index(key[:2])
        new_key = maj_keys[index]
        if "m" in key or "M" in key:
            key = new_key + 'm'
        else:
            key = new_key
    #if key is minor, make it its relative major key by transposing up 3 half steps
    if "m" in key or "M" in key:
        old_key = key.replace('m', "")
        index = maj_keys.index(old_key)
        index = (index + 3)%12
        key = maj_keys[index]
    #Now the chords should be in a major key
    #If the major key is C, then quit
    if key == 'C':
        return web_driver

    #Account for the capo if it is present, then transpose to C from the resulting key
    elif capo != 0:
        print("4")
        index = (maj_keys.index(key) - capo)
        if index < 0: 
            key = maj_keys[12 + index]
        else:
            key = maj_keys[index]
        print("5")
    if key == 'C':
        return web_driver
    elif key in ["F#", "G", "G#", 'A', "A#", "B"]:
        while key != "C":
            index = (maj_keys.index(key) + 1)%12
            time.sleep(6)
            web_driver.driver.execute_script("arguments[0].click();", transpose_up)
            print("SUCCESSFUL TRANSPOSE UP!")
            key = maj_keys[index]
    elif key in ["C#", "D", "D#", "E", "F"]:
        while key != "C":
            index = (maj_keys.index(key) - 1)
            time.sleep(6)
            web_driver.driver.execute_script("arguments[0].click();", transpose_down)
            print("SUCCESSFUL TRANSPOSE DOWN!")
            key = maj_keys[index]
    time.sleep(5)
    return web_driver
        
    
def diatonic_pattern(chords):
    """Lists out the detected chord progression of the section in Roman numerals

    Args:
        chords (list): A list of chord strings

    Returns:
        tuple: A tuple containing the Roman numeral progression and the number of non-diatonic chords
    """
    c_major = ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]
    numerals = ["I", "ii", "iii", "IV", "V", "vi", "VII"]
    no_extend=[]
    non_diatonic = 0
    
    for val in chords:
        if '/' in val:
            if 'm/' in val:
                val = val[0:2]
            else:
                val = val[0]
        no_extend.append(''.join([i for i in val if not i.isdigit()]).replace("maj", "").replace("sus", "").replace('dim', "").replace('aug', "").replace('(', "").replace(')', "").replace('add',""))

    numbers = ""
    last = ""
    prog = []
    for number in no_extend:
        if number != last:
            prog.append(number)
        last = number
    for c in prog:
        #Attempts to just get the numeral associated with a chord in the key of C major
        # If the current chord is not in c_major, add the correct suffix
        try:
            numbers = numbers + "-" + numerals[c_major.index(c)]
        except:
            c_major_stripped = ["C", "D", "E", "F", "G", "A", "B"]
            non_diatonic += 1
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
                numbers = numbers + "-"+ numerals[c_major_stripped.index(c)].lower()+suffix
            else:
                numbers = numbers + "-"+ numerals[c_major_stripped.index(c)].upper()+suffix
    return numbers[1:], non_diatonic


def dict_to_df(data, song, artist):
    """Turns dictionary key value pairs into dataframe rows

    Args:
        data (dict): A dictionary containing the scraped chord data
        song (str): The name of the song that the data is from
        artist (str): The name of the artist that the data is from

    Returns:
        pandas.DataFrame: A DataFrame containing the scraped chord data in each section of the song
    """
    df = pd.DataFrame(columns = ['Name', "Artist", "Section", "Progression", "EndDifferent", "NumSectionChords", "nondiatonic_chords", "extended_chords"])
    for key, value in data.items():
        if value == []:
            continue
        df = df.append({'Name':song, "Artist":artist, "Section":key, "Progression":value[0], "EndDifferent":value[1], "NumSectionChords":value[2], "nondiatonic_chords":value[3], "extended_chords":value[4]}, ignore_index = True)
    return df


def main():
    #input_artists is the list of artists who show up in the the Artists column 
    # of 'scrape_songs.csv' AND we want to actually scrape the songs of
    input_artists =["Ed Sheeran", "Foo Fighters"] #all listed artists must be in scrape_songs.csv
    scrape_song_chords(input_artists)

if __name__ == "__main__":
    main()