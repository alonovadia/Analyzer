Instructions: 

A Open Claude at https://claude.ai/new
B Add Screenshots of your Wargame (Most optimal are 10 screenshots per upload)
C Enter This as PROMPT to Claude: 

------

" Create a single markdown table from the following data.

Required Columns (in this exact order):
- Guild
- Player
- Defeats
- Assists
- Damage Dealt
- Damage Taken
- Amount Healed

Instructions:
1.  **Extract Data**: From the raw data provided below, accurately identify the 'Guild', 'Player', 'Defeats', 'Assists', 'Damage Dealt', 'Damage Taken', and 'Amount Healed' for each entry.
2.  **Cross-Reference**: Ensure the data for all columns is an exact match to the source.
3.  **Filter**: Ignore all icons and emojis.
4.  **Remove Duplicates**: If a player appears more than once, only include their first entry to avoid duplicates.
5.  **Constraint**: Confirm that no single Guild has more than 48 players in the final table.
6.  **Output**: Provide only the markdown table, with no additional text, explanation, or conversation.
"

 -------

 The structure: 

 App
  data\
  templates\
   _navbar.html
   base.html
   player_analysis.html
   player_details.html
   player_upload.html
  venv
  app.py
  ew.md

--- Install needed dependencies (as shows in app.py)


D Copy the Markdown from Claude into the App. 

 D2. Upload Player Data - Shows you all of the extracted info (includuing rivals guild) 
 D3. Clicking on a player -> should show the averages too if more than 1 data point was entered (checks for duplicates too)

It also creates a csv file inside "data" folder containing all of that info in Excel-like form. (need to install Excel extention)

E. Inside "Upload Player Data" you can also delete all of the stored csv's. 
   You may adjust the code further to add "Guild" to the csv's name to be able to delete/remove unwanted files.

Things that needed to be run:
.\venv\Scripts\activate  <- starts the virtual environment

python app.py  <- running the app
