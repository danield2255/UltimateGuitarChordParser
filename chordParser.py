import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import glob
import time
from seleniumbase import SB
from utils.helper_funcs import dict_to_df
from utils.music_logic_funcs import transpose_to_C, derive_key, derive_capo, collect_chords_from_section


def select_compatible_tab(web_driver, song, artist):
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
    time.sleep(3)

    print("Searching for " + song + " by " + artist)

    #Pick the top rated listing
    print("Picking the top rated listing")
    row_num = 1
    on_usable_tab = False
    while not on_usable_tab or row_num > 5:
        print("Trying listing number " + str(row_num))
        try:
            try:
                web_driver.click(f"/html/body/div/div[2]/main/div/div[2]/section/article/div/div[{row_num}]/div[2]/header/span/span/a")
                time.sleep(3)
            except:
                try:
                    print("Trying alternative XPath")
                    web_driver.click("/html/body/div/div[2]/main/div/div[2]/section/article/div/div[2]/div[2]/header/span/span/a")
                    time.sleep(2)
                except:
                    print("need to wait")
            #Sometimes an ad pops up after clicking the listing, so we have to check for that and wait it out if it does
            if BeautifulSoup(web_driver.driver.page_source, 'html.parser').find('title') == "Advertising Page":
                print('AD POPS UP')
                time.sleep(41)
            cur_html = web_driver.driver.page_source
            cur_soup = BeautifulSoup(cur_html, 'html.parser')
            if len(cur_soup.find_all(string="Transpose")) == 0:
                raise Exception("Not on tab")
            
            print("MADE IT TO THE TAB")
            data = scrape_chords_from_tab(web_driver)
            if data != None:
                print("Data collected successfully")
                on_usable_tab = True
            else:
                raise Exception("Not a usable tab")
        except Exception as e:
            print(f"Error with listing number {row_num} with error: {e}")
            row_num += 1
            print("Trying the next best listing")
            web_driver.uc_open_with_reconnect(search_url, 3)
            time.sleep(3)
    return data
    

def scrape_chords_from_tab(web_driver):
    """Runs when you are on the webpage you want to scrape. Scrapes the chord data of the song transposed to the key of C major

    Args:
        web_driver (selenium.webdriver): The webdriver instance

    Returns:
        dict: A dictionary containing the scraped chord data
    """
    time.sleep(3)
    html = web_driver.driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    #Get key and capo data
    for header_line in soup.find_all('div', attrs ={'class':'CCUPL'}): 
        capo = derive_capo(header_line)
        key = derive_key(header_line)

    print("KEY: " + key)
    print("CAPO: " + str(capo))
    if key == "":
        print("NOT A VALID TAB")
        return None
    
    #standardize the key to C major
    web_driver = transpose_to_C(web_driver, key, capo)

    body = BeautifulSoup(web_driver.driver.page_source, 'lxml').find("code", attrs ={'class':'QsmqP'})

    regex = "\[(.*?)\]"

    sections = re.split(regex, str(body))
    # Data will be held in a dictionary with the key being the section, and the value being a list of the progression,
    # the end (this one will be None if the end is the same as the whole thing), number of chords in the section, 
    # number of non_diatonic chords and number of extended chords 
    data = {} 
    sec_data_next=False
    sec_label = ""
    for sec in sections:
        data, sec_data_next, sec_label = collect_chords_from_section(sec, data, sec_data_next, sec_label)
    return data

def collect_song_data(input_artists):
    """Will only get the data on each section of each song in the scrape_songs.csv file. 

    Args:
        input_artists (list): A list of artist names to scrape chords for
    """
    scrape_songs = pd.DataFrame(pd.read_csv("data/scrapeSongs.csv"))
    done = []

    with SB(uc=True) as sb:
        for _, row in scrape_songs.iterrows():
            print("Currently on song " + row["Name"] + " by " + row['Artists'])
            if row['Artists'] in input_artists and (row["Name"], row['Artists']) not in done:
                try:
                    data = select_compatible_tab(sb, row["Name"], row['Artists'])
                except Exception as e:
                    print(f"Diverted from site with error: {e}")
                    done.append((row["Name"], row['Artists']))
                    continue
                if data == None:
                    print("Data was None")
                    done.append((row["Name"], row['Artists']))
                    continue
                else:
                    df = dict_to_df(data,row["Name"], row['Artists'])
                    done.append((row["Name"], row['Artists']))
                    cur = row["Name"] + "-" + row['Artists']
                    #Save the file of the song's data
                    df.to_csv("data/songData/{0}.csv".format(cur), encoding='utf-8')
            print("Done with " + row["Name"] + " by " + row['Artists'])
    files = [file for file in glob.glob('data/songData/*.csv')]
    try:
        final_file = pd.concat([pd.read_csv(file) for file in files])
        final_file.to_csv('data/songSections.csv')
    except:
        print("No valid tabs were found and there were no songs already saved, try searching for different songs!")



def main():
    # Input_artists is the list of artists who show up in the the Artists column 
    # of 'scrape_songs.csv' AND we want to actually scrape the songs of
    input_artists =["Coldplay", "Taylor Swift", "Beatles"] #all listed artists must be in scrape_songs.csv
    collect_song_data(input_artists)

if __name__ == "__main__":
    main()