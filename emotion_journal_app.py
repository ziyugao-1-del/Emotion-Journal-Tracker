# -*- coding: utf-8 -*-
"""
Emotion Journal Tracker
"""

#First import all the necessary library
import tkinter as tk #tkinter is for GUI
from tkinter import ttk, messagebox, scrolledtext # some tkinter component
from datetime import datetime #datetime format data
import pandas as pd #process journal entries
import matplotlib.pyplot as plt #use to plot the visualisation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #library to embedded matplotlib to tkinter
import os

import nltk #import nltk library for sentiment analysis
# First, we download everything (only required on first try)
nltk.download('punkt') # a vader model that tokenise text (break down word by word or sentence by sentence)
nltk.download('punkt_tab') # another tokenise model 
nltk.download('vader_lexicon') # a model that map each lexicon to sentiment score
nltk.download('stopwords') # use to filter meaningless word
nltk.download('wordnet') # use for lemmatization

from nltk.sentiment.vader import SentimentIntensityAnalyzer #model for sentiment analysis
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

analyzer = SentimentIntensityAnalyzer() #initialise sentiment analysis model

#File path
CSV_FILE = "journal_entries.csv" #path to journal stored in database/individual file

journal_data = [] #initialise an empty list to store journal


#############################
# Utility Functions
#############################
# Function to preprocess the text data
def preprocess_text(text):
    tokens = word_tokenize(text.lower()) #convert all to lower case and tokenise them (break into word by word)
    filtered_tokens = [t for t in tokens if t not in stopwords.words('english')] #remove stopwords
    lemmatizer = WordNetLemmatizer() #lemmatize, to reduce the words to its root
    lemmatized = [lemmatizer.lemmatize(t) for t in filtered_tokens]
    return ' '.join(lemmatized) #join them back

# Function to group the emotion into different categories based on the compound score output
def get_emotion_category(compound):
    if compound >= 0.75: 
        return "Very Positive 😄", "Dark Green"
    elif compound >= 0.25:
        return "Positive 🙂", "Green"
    elif compound >= 0.05:
        return "Slightly Positive 😊", "Light Green"
    elif compound <= -0.75:
        return "Very Negative 😭", "Dark Red"
    elif compound <= -0.25:
        return "Negative 😔", "Red"
    elif compound <= -0.05:
        return "Slightly Negative 😕", "Orange"
    else:
        return "Neutral 😐", "Yellow"


#############################
# CSV Handling
#############################
# Function to read journal from saved file
def load_entries_from_csv():
    global journal_data
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE) #read the file into dataframe format
        # here the format is changed to dictionary because the record will be added one by one
        # by changing to dictionary, the application can map the record (journal data) and processed sentiment scores
        # then we can append it to the previous record so it is very convenience
        journal_data = df.to_dict(orient="records") 
        print(f"Loaded {len(journal_data)} entries from CSV.")
    else:
        print("No previous entries found. ")

# Function to save newly written journal to csv
def save_entries_to_csv():
    if len(journal_data) == 0:
        return
    df = pd.DataFrame(journal_data) #convert back to df so it can be saved easily to csv
    df.to_csv(CSV_FILE, index=False)
    print("💾 Entries saved to CSV.")


#############################
# Diary Function
#############################

# Function to do sentiment analysis and save them
def analyze_and_save_entry(date_str, entry_text):
    if not entry_text.strip(): # check if empty
        messagebox.showwarning("Empty Entry", "Please write something before saving!") #alert
        return

    try: # get the date of the journal
        dt = datetime.strptime(date_str, "%Y-%m-%d") #change to datetime format
    except ValueError:
        dt = datetime.now() #or if the value is an error, use current

    current_date = dt.strftime("%Y-%m-%d") #get the date in the format stated
    processed = preprocess_text(entry_text) #pre-processed the text (refer back to the method)
    scores = analyzer.polarity_scores(processed) #sentiment analysis (refer to NLTK documentation if not clear)

    # output will be four different scores but only compound score used to determine emotion
    compound = scores['compound'] #positive score = overall positive emotion, vice versa and 0 for neutral
    positive = scores['pos'] #positive score only
    negative = scores['neg'] #negative score only
    neutral = scores['neu'] #neutral score only
    emotion, color = get_emotion_category(compound)

    # Group the data into different column (to save them in csv)
    # these are the data I want to save
    entry = {
        'date': current_date,
        'entry': entry_text.strip(),
        'compound': compound,
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
        'emotion': emotion,
        'color': color
    }
    journal_data.append(entry) #add to old record
    save_entries_to_csv() #save

    messagebox.showinfo("Saved!", f"Entry saved.\nEmotion: {emotion}") #pop up
    #set to default
    entry_textbox.delete("1.0", tk.END) #Clear the input box after everything is saved
    date_entry.delete(0, tk.END) #clear the date
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) #add date (current date)
    refresh_table() #a dashboard function to show latest record in the GUI


#############################
# Dashboard Functions
#############################
def refresh_table(): # get the latest data
    for row in tree.get_children(): #use tree widget for tkinter
        tree.delete(row) #remove existing rows

    if len(journal_data) == 0: #if no data, then just return
        return

    # display all rows from the latest version of record
    # only display three data
    for entry in journal_data:
        tree.insert("", "end", values=(entry['date'], entry['emotion'], f"{entry['compound']:.2f}"))


def show_visualization(): #function to show visualisation
    if len(journal_data) == 0: # if empty
        messagebox.showwarning("No Data", "Add some entries first!") # warning message
        return

    df = pd.DataFrame(journal_data) # get existing data, create df to better process it
    df['date'] = pd.to_datetime(df['date'], errors='coerce') # convert to datetime
    df = df.dropna(subset=['date', 'compound']) #drop na

    today = datetime.now().date() #get the date today as the visualisation is for past 7 or 30 days from now

    #Past 7 Days for Trend
    week_start = today - pd.Timedelta(days=6) #get the weekly data
    df_week = df[df['date'].dt.date.between(week_start, today)] #filter
    df_daily = df_week.groupby(df['date'].dt.date)['compound'].mean().reset_index() #get mean

    # Fill missing days with NaN
    all_dates = pd.date_range(week_start, today) # we get the date range of past 7 days
    df_daily = df_daily.set_index('date').reindex(all_dates).reset_index() # get the date that match 
    df_daily.columns = ['Date', 'Compound'] #rename the data so we are getting date and the compound scores

    #Past 30 Days for Emotion Counts
    month_start = today - pd.Timedelta(days=29) # get past 30 days
    df_month = df[df['date'].dt.date.between(month_start, today)] #get the date that match this range
    emotion_counts = df_month['emotion'].value_counts() #count how many counts we have for emotions

    #Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6))

    #Trend Line (Past 7 Days)
    #Set up the plot
    #The code are all related to styling the plot
    # x = date, y = compound scores
    ax1.plot(df_daily['Date'], df_daily['Compound'], marker='o', color='teal', linewidth=2)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title("Mood Trend (Past 7 Days)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Compound Sentiment")
    ax1.set_xticks(df_daily['Date'])
    # get only month and date
    ax1.set_xticklabels([d.strftime("%b %d") for d in df_daily['Date']], rotation=45)
    # the compound score is ranging from -1 to 1
    ax1.set_ylim(-1, 1)
    ax1.grid(True, alpha=0.3)

    #Emotion Distribution (Past 30 Days)
    #Map each emotion into different colour
    colors_map = {
        'Very Positive 😄': '#006400',
        'Positive 🙂': '#228B22',
        'Slightly Positive 😊': '#90EE90',
        'Neutral 😐': '#FFD700',
        'Slightly Negative 😕': '#FF8C00',
        'Negative 😔': '#DC143C',
        'Very Negative 😭': '#8B0000'
    }

    # Plot a bar plot
    # The code are all related to styling the plot
    bar_colors = [] # first initialise the colour of the bar
    for emotion in emotion_counts.index: # check if it is defined in the colour map
        if emotion in colors_map:
            bar_colors.append(colors_map[emotion]) # yes, we get the colour
        else:
            bar_colors.append('gray') #no, use grey colour
    # set up the bars, first emotions count is the height, then the value name, colour
    ax2.bar(emotion_counts.index, emotion_counts.values, color=bar_colors)
    ax2.set_title("Emotion Distribution (Past 30 Days)", fontsize=12, fontweight='bold')
    # rotate so it is clearer
    ax2.set_xticklabels(emotion_counts.index, rotation=45, ha='right')
    ax2.set_ylabel("Count")
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    #Show in Tkinter Window
    vis_window = tk.Toplevel(root)
    vis_window.title("Emotion Visualization") # the title

    # Get widget
    canvas = FigureCanvasTkAgg(fig, master=vis_window) # add it in the canvas
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


#############################
# GUI Setup
#############################
root = tk.Tk() #start a tkinter window
root.title("Emotion Journal Tracker 📝")
root.geometry("700x600")

notebook = ttk.Notebook(root) #use to create different tabs
notebook.pack(fill='both', expand=True)

# Tab 1: Journal Entry
journal_frame = ttk.Frame(notebook) 
notebook.add(journal_frame, text="New Entry") #name it new entry

# set up date widget
tk.Label(journal_frame, text="Date (YYYY-MM-DD):", font=("Arial", 12)).pack(pady=5)
date_entry = tk.Entry(journal_frame, font=("Arial", 12), width=15)
date_entry.pack()
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

# set up journal widget (textbox)
tk.Label(journal_frame, text="Write your journal entry:", font=("Arial", 12)).pack(pady=5)
entry_textbox = scrolledtext.ScrolledText(journal_frame, wrap=tk.WORD, width=70, height=15, font=("Arial", 11))
entry_textbox.pack(pady=5)

# save button 
save_button = ttk.Button(journal_frame, text="Save Entry", command=lambda: analyze_and_save_entry(date_entry.get(), entry_textbox.get("1.0", tk.END)))
save_button.pack(pady=10)

ttk.Button(journal_frame, text="Go to Dashboard →", command=lambda: notebook.select(dashboard_frame)).pack(pady=5)

# Tab 2: Dashboard
dashboard_frame = ttk.Frame(notebook)
notebook.add(dashboard_frame, text="Dashboard") #name it dashboard

# Set up the table
columns = ("Date", "Emotion", "Compound")
tree = ttk.Treeview(dashboard_frame, columns=columns, show="headings", height=15) #treeview = table
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=200)
tree.pack(pady=10, fill=tk.BOTH, expand=True)

# Set up button for back and show viz
btn_frame = ttk.Frame(dashboard_frame)
btn_frame.pack(pady=10)
ttk.Button(btn_frame, text="← Back to Journal", command=lambda: notebook.select(journal_frame)).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Show Visualization", command=show_visualization).grid(row=0, column=1, padx=10)

# Load entries on startup
load_entries_from_csv()
refresh_table()

root.mainloop()
