# this script uses the csv output of the helium-hotspots_csv_details.py script
# which has the 7000 most active hotspots with their location details
# it groups the data traffic per country
# using the API as in https://docs.helium.com/api/blockchain/introduction/


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

import csv
import pandas as pd

# use this particular CSV file as input
INPUT_CSV_FILE = "csv_output/20220325103345hotspots_data_packets3_details.csv"


# START OF SCRIPT

print('===========================================================')
print('GROUP DATA TRAFFIC PER COUNTRY')
print('===========================================================')
print('based on input file:', INPUT_CSV_FILE)
print('===========================================================')

with open(INPUT_CSV_FILE, 'r') as input_csvfile:
    # use pandas to read, groupby and sum
    hotspot_list = pd.read_csv(INPUT_CSV_FILE)
    # create pandas dataframe with sums of each column to get sum of packets per country
    country_sums = hotspot_list.groupby('country').sum()
    # create pandas dataframe with count of hotspots per country
    country_counts = hotspot_list.groupby('country').count()

# calculate the total packet count sum
packets_total = hotspot_list['packet count'].sum()

# drop unneeded columns from both dataframes
country_sums.drop(['rank', 'lat', 'lng', 'reward scale'], axis=1, inplace=True)
country_counts.drop(['hotspot address', 'owner', 'packet count', 'rank', 'lat', 'lng', 
    'reward scale', 'location', 'city'], axis=1, inplace=True)
# rename the column of the counts
country_counts.columns = ['hotspot count']

# sort countries descending by packets
countries_sorted = country_sums.sort_values('packet count', ascending=False)
# add a column with the share of packets
countries_sorted['share of traffic'] = countries_sorted['packet count'] / packets_total

# join both dataframes to add the hotspot count to the sorted by packet count
countries_sorted_with_count = countries_sorted.join(country_counts)

# add a column with the average packets per hotspot
countries_sorted_with_count['avg packets per hotspot'] = \
    countries_sorted_with_count['packet count'] / countries_sorted_with_count['hotspot count']

print(countries_sorted_with_count.to_string(formatters=
    {'share of traffic': '{:.2%}'.format, 
    'packet count': '{:,}'.format,
    'hotspot count': '{:,}'.format,
    'avg packets per hotspot': '{:,.0f}'.format}))
print('[sanity check]')
print('sum of shares:', str(round(100 * countries_sorted_with_count['share of traffic'].sum(), 2)) + '%')
print('sum of packets:', countries_sorted_with_count['packet count'].sum())
print('sum of hotspots:', countries_sorted_with_count['hotspot count'].sum())
print('===========================================================')    
# try to output in a markdown friendly format; to_markdown() does not work with to_string()
print('|', countries_sorted_with_count.to_string(formatters=
    {'share of traffic': '|{:.2%}'.format, 
    'packet count': '|{:,}'.format,
    'hotspot count': '|{:,}'.format,
    'avg packets per hotspot': '|{:,.0f}|'.format}))
print('===========================================================')    
print('END')
print('===========================================================')
    
