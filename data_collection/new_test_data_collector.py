# Note: Make sure you run this file root folder of the project

import requests
import json
import requests_cache
import pandas as pd
from flatten_json import flatten
import matplotlib.pyplot as plt
import os

# Bypass SSL certificate verification
# import certifi
# change certificate settings: add myanimelist certificate chain to certificate list
# print(certifi.where())

'''
Available API requests:

Get list of anime by search term
    resp = requests.get("https://api.myanimelist.net/v2/anime?q=one&limit=2", headers=headers)

Get anime details by anime id
    resp = requests.get("https://api.myanimelist.net/v2/anime/30230?fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics", headers=headers)

Get top ranked anime by type
    resp = requests.get("https://api.myanimelist.net/v2/anime/ranking?ranking_type=all&limit=2", headers=headers)

Get anime details by season
    resp = requests.get("https://api.myanimelist.net/v2/anime/season/2023/summer?sort=anime_num_list_users&fields=id,title,start_date,end_date,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,background,related_anime,related_manga,recommendations,studios,statistics&limit=6", headers=headers)
'''

############################ GLOBAL VARIABLES ############################
# API authentication info (key, secret, header)
client_id = "6a3dc42a0c201194413f0f02733ae033"
#client_secret = "b24d9ab0be8b47325e5ff0ac8c29527553447a0e9e13e9aa7ea0b01cbcd30721"

# API query settings

# Selected fields
fields = ("&fields=id,title,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,"
        "num_scoring_users,nsfw,media_type,status,genres,num_episodes,start_season,"
        "broadcast,source,average_episode_duration,rating,background,studios,statistics")

'''
Fields options: (by default->id, main_picture, title)
    - synopsis: string of long synopsis paragraph
    - popularity: rank of popularity
    - media_type: should be tv for anime?
    - status: airing, finished, etc.
    - start_season: seaon and year that anime started
    - broadcast: what day and time of week that it broadcasts
    - source: light novel, manga, etc.
    - average_episode_duration: duration in seconds
    - background: ?
    - related_anime & related_manga: don't work for some reason?
    - studios: give name and id of studio(s)
    - statistics: ?

All fields:
fields = ("&fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,"
          "rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,"
          "status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,"
          "rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics")
'''

############################ HELPER FUNCTIONS ############################
# Function to print json obj
def json_print(json_obj):
    str = json.dumps(json_obj, sort_keys=True, indent=2)
    print(str)

# Function to save df to json file
def save_df_to_json(df, filename):
    # Write the JSON data to the file
    json_obj = df.to_json(orient='index', indent=4)
    with open(filename, 'w') as file:
        json.dump(json.loads(json_obj), file, indent=4)

# Function to plot frequency of popularity ranks and save plot
def save_popularity_histogram(df, plot_path, col_name='popularity', bins=10):
    # Plot histogram
    plt.hist(df[col_name], bins=bins, edgecolor='k')
    # Add labels and title
    plt.xlabel('Popularity Rank')
    plt.ylabel('Frequency')
    plt.title('Popularity Rank Distribution')
    # Save plot
    plt.savefig(plot_path) # Save
    # Show and close the plot
    #plt.show() # Show
    plt.close() # Close

def save_dataframe(df, file_name, file_type, root_path='./data_collection/new_test_data/',
                   index=False, index_label=None):
    # Change root path if file_type is png
    if file_type == 'png':
        root_path = './data_collection/plots/'
    file_path = f"{file_name}.{file_type}"
    file_path = os.path.join(root_path, file_path) # Get full path
    
    # Save the DataFrame
    if file_type == 'csv':
        df.to_csv(file_path, index=index, index_label=index_label) # Convert df to csv
    elif file_type == 'xlsx':
        df.to_excel(file_path, index=index, index_label=index_label) # Convert df to excel
    elif file_type == 'json':
        save_df_to_json(df, file_path) # Convert df to json
    elif file_type == 'png':
        save_popularity_histogram(df, file_path) # Save plot
    else:
        raise SyntaxError(f"Error: {file_type} is an invalid file type")
    print(f"Saved: {file_path}")

# Error check for get request
def get_request_and_check(query, headers={'X-MAL-CLIENT-ID': client_id}):
    # Check for exceptions
    try:
        resp = requests.get(query, headers=headers)
        resp.raise_for_status() # Check for exceptions
    # Resolving exceptions
    except requests.exceptions.HTTPError as err:
        print("HTTPError")
        print(err.response.text)
        raise SystemExit(err)
    except requests.exceptions.ConnectionError as err:
        print("ConnectionError:\n")
        print(err.response.text)
        raise SystemExit(err)
    except requests.exceptions.Timeout as err:
        print("Timeout:\n")
        print(err.response.text)
        raise SystemExit(err)
    except requests.exceptions.TooManyRedirects as err:
        print("TooManyRedirects:\n")
        print(err.response.text)
        raise SystemExit(err)
    except requests.exceptions.RequestException as err:
        print("Oops, something else:\n")
        print (err.response.text)
        raise SystemExit(err)
    return resp

# Convert get response to dataframe
def convert_resp_to_df(resp, animes_df):
    # Convert response to json
    resp_json = resp.json() # Convert response to json
    #json_print(resp_json) # Print json (for debugging)
    for animes in resp_json['data']: # Iterate through all animes in resp
        # Data cleaning
        anime = animes['node']
        if anime['media_type'] != 'tv': # Check if it is an anime
            continue                     
        if anime['status'] == 'finished_airing': # Check if anime has NOT finished airing
            continue
        if anime['synopsis'] == '': # Remove anime that has no synopsis
            continue
        if anime['studios'] == []: # Check if anime has no studio
            anime['studios'] = [{'id': -1, 'name': 'unknown'}] # Set studio to unknown
        # Data cleaning done
        flat_json = flatten(anime) # Flatten json
        cur_anime_df = pd.DataFrame(flat_json, index=[0]) # Flatten json, then convert it to dataframe
        
        # If dj_json has not been created, create it and set var to True
        if animes_df.empty:
            animes_df = cur_anime_df
        # If df_json alr created, then just append to it
        else:
            animes_df = pd.concat([animes_df, cur_anime_df], ignore_index=True)
    # Done converting response to df
    return animes_df

# Calling the API
def collect_new_test_data(year=2023, season="fall", sort="anime_num_list_users", limit=500, nsfw=True):
    print(f"\nCollecting data...")
    # Install local cache to cache API calls (to avoid repeated calls)
    requests_cache.install_cache('./data_collection/mal_new_test_api_cache')
    animes_df = pd.DataFrame() # Var to store df of all animes (initialize as empty df) 
    # Collect data by season
    query = ("https://api.myanimelist.net/v2/anime/"
                f"season/{year}/{season}?sort={sort}&limit={limit}&fields={fields}&nsfw={nsfw}")
    print(f"Collecting from season {year} {season}...")
    resp = get_request_and_check(query)
    animes_df = convert_resp_to_df(resp, animes_df) # Convert response to df
    return animes_df

############################ MAIN FUNCTION ############################
# Run this file in the root folder of the project
if __name__ == '__main__':
    # Call collect_data() to get df of anime data
    new_test_animes_df = collect_new_test_data() # Start collecting data

    # Convert and save df to csv, excel, json, and png (plot of popularity distribution)
    print("\nConverting data to csv, excel, json, png files...")
    save_dataframe(new_test_animes_df, "new_test_animes_data", 'csv')
    save_dataframe(new_test_animes_df, "new_test_animes_data", 'xlsx')
    save_dataframe(new_test_animes_df, "new_test_animes_data", 'json')
    save_dataframe(new_test_animes_df, "new_test_pop_rank_plot", 'png')
    
    print("\nSuccessfully collected data into csv, excel, and json files!")
    exit(0)



