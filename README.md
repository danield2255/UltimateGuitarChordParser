# UltimateGuitarChordParser
Selenium/Beautiful Soup web scraper based chord parser of Ultimate-Guitar.com.


Ultimate-Guitar.com(https://www.ultimate-guitar.com/) is a forum based site for posting guitar tabs, and can be considered a great source for learning many songs on guitar or piano. Getting data on the chords which make up a song is often a challenge, but this repository's program serves as a possible solution using ultimate-guitar!

The program chordParser.py requires a csv file which can be created in chordCreator.py where songs are chosen to be scraped. The user inputs the song names and artists of these songs to this program and a file is created. This file is called upon in the main program and the user specifies which of the artists in the file just created will they want the song data of. 

The program has the requirement that there is a "key" datafield in the tab because it wanted to be able to standardize the key of the song to C major using the tool built into the website. If there is not key data for a tab, it is considered invalid. 

The data returned is data on each section of the songs scraped. For all valid songs with valid tabs, the following data is returned:

- Name: Song's name
- Artist: Artist name
- Section: Section of the song
- Progression: the chord progression of the section roman numerials(scale degrees) when the song is standardized to the key of C. This is to show how the progressions between songs are different. 
- EndDifferent: None if the end of the section's progression was not different than how it was for the entirty of the section. If it is, the part different from the pattern will be shown. 
- NumSectionChords: Total number of unique chords in the section
- nonDiatonicChords: Total number of non-diatonic chords in the section
- extendedChords: Total number of extended chords in the section

Disclaimer: There are so many ways in which people express data in the tabs, that some songs have complications getting parsed when they should be able to. Also the program only looks for the site's key data, so many songs will be unparsable because this tag is not present. ** However: Searching for more modern songs with guitar or piano instrumentation will likely increase the chance of a successful parse of the data. ** 
Finally, one issue experienced with this is that the site seems to have changed its previously set html tags which the program depends on staying consistent. If they continue to do this, this will require program maintenance. 
