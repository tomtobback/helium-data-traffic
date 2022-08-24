# this script uses the csv output of the helium-data-traffic.py script
# it adds the city, country and coordinates of each hotspot
# using the API as in https://docs.helium.com/api/blockchain/introduction/
# and saves to a new csv file


#    MIT LICENSE
#    Copyright (c) 2022 Tom Tobback
#    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
#    to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#    IN THE SOFTWARE.

import requests
import urllib
import datetime
import csv

# use this particular CSV file as input
INPUT_CSV_FILE = "csv_output/20220824091415hotspots_data_packets7.csv"

RANK_CUTOFF = 2000

# Helium requires a user-agent in the HTTP header
# https://docs.helium.com/api/blockchain/introduction
this_header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}

def get_hotspot_details(address: str):
    # short response, no cursor/paging
    url = 'https://api.helium.io/v1/hotspots/' + address
    r = requests.get(url, headers=this_header)
    this_name = ''
    this_owner = ''
    this_lat = 0
    this_lng = 0
    this_loc = ''
    this_scale = 0
    this_city = ''
    this_country = ''
    # this fails sometimes when hitting the API repeatedly
    try:
        this_json = r.json()['data']
        if 'name' in this_json:
            this_name = this_json['name']     
        if 'owner' in this_json:
            this_owner = this_json['owner']     
        if 'lat' in this_json:
            this_lat = this_json['lat']     
        if 'lng' in this_json:
            this_lng = this_json['lng']     
        if 'location' in this_json:
            this_loc = this_json['location']     
        if 'reward_scale' in this_json:
            this_scale = this_json['reward_scale']     
        if 'long_city' in this_json['geocode']:
            this_city = this_json['geocode']['long_city']     
        if 'long_country' in this_json['geocode']:
            this_country = this_json['geocode']['long_country']     
    except:
        this_city = 'fail'
        this_country = 'fail'
    return [this_name, this_owner, this_lat, this_lng, this_loc, this_scale, this_city, this_country]


# START OF SCRIPT

print('===========================================================')
print('ADD DETAILS TO HOTSPOTS IN CSV FILE')
print('===========================================================')
filename_without_ext = INPUT_CSV_FILE.split('.')
output_filename = filename_without_ext[0] + '_details.csv'
print('saving output to:', output_filename)
print('===========================================================')

with open(INPUT_CSV_FILE, 'r') as input_csvfile, open(output_filename, 'w') as output_csvfile:
    csv_reader = csv.reader(input_csvfile, delimiter=',')
    csv_writer = csv.writer(output_csvfile)
    for i, row in enumerate(csv_reader):
        rank = row[0]
        address = row[1]
        count = row[2]
        full_row = []
        if i == 0:
            full_row = ['rank','hotspot address','packet count','name',
            'owner','lat','lng','location','reward scale','city','country']
        else:
            details = get_hotspot_details(address)
            print(rank, details)
            full_row = row + details
        csv_writer.writerow(full_row)
        
        # we're only interested in the first RANK_CUTOFF hotspots
        if i == RANK_CUTOFF:
            break
            
print('===========================================================')
print('saved output to:', output_filename)
print('===========================================================')    
print('END')
print('===========================================================')
    
