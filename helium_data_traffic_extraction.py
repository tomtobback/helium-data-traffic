# this script accesses the Helium API to get an idea of data packet traffic
# using the API as in https://docs.helium.com/api/blockchain/introduction/
# data packets are handled in state channels, a 'layer 2' technology that
# keeps the details of these data packets off the main Helium blockchain, only
# storing summaries of the transactions: the number of packets and DCs per hotspot
# we sum these packets and DCs per hotspot over the NUMBER_OF_DAYS
# we export this hotspot ranking to a CSV file and plot it on a graph
# we list the top hotspots with location details until we reach FRACTION_THRESHOLD



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
import matplotlib.pyplot as plt

FRACTION_THRESHOLD = 0.5    # cut the hotspot ranking when we reach this fraction 0-1
NUMBER_OF_DAYS = 7          # how many days to go back from now
USD_PER_DC = 0.00001        # https://docs.helium.com/use-the-network/console/data-credits

# Helium requires a user-agent in the HTTP header
# https://docs.helium.com/api/blockchain/introduction
this_header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}

def get_hotspot_location(address: str):
    # short response, no cursor/paging
    url = 'https://api.helium.io/v1/hotspots/' + address
    r = requests.get(url, headers=this_header)
    # this fails sometimes when hitting the API repeatedly
    try:
        this_json = r.json()['data']
        this_city = '_'
        this_country = '_'
        if 'long_city' in this_json['geocode']:
            this_city = this_json['geocode']['long_city']     
        if 'long_country' in this_json['geocode']:
            this_country = this_json['geocode']['long_country']     
        location = str(this_city) + ', ' + str(this_country)
    except:
        location = 'api call failed'
    return location

def get_statechannels(this_cursor: str):
    # the Helium API uses cursors for paging 
    # in this URL we can define our timespan   
    #url = 'https://api.helium.io/v1/state_channels?min_time=-3%20hour'  # last 3 hours
    url = 'https://api.helium.io/v1/state_channels?min_time=-' + \
        str(NUMBER_OF_DAYS) + '%20day'  
    if (this_cursor != ''):
        url += '&cursor=' + this_cursor
    print(url)
    r = requests.get(url, headers=this_header)
    # this seems to fail sometimes
    try:
        details = r.json()['data']
    except:
        print('ERROR:', r)
        details = {}
    # the last page does not return a cursor
    try:
        next_cursor = r.json()['cursor']
    except:
        next_cursor = ''
    return details, next_cursor

def get_dcburns():
    # short response, no cursor/paging
    url = 'https://api.helium.io/v1/dc_burns/sum?min_time=-' + \
        str(NUMBER_OF_DAYS) + '%20day&bucket=day'
    r = requests.get(url, headers=this_header)
    details = r.json()['data']
    sum_dcburns = sum(day['state_channel'] for day in details) 
    return sum_dcburns

def get_hotspot_count():
    # from the main blockchain stats
    url = 'https://api.helium.io/v1/stats'
    r = requests.get(url, headers=this_header)
    details = r.json()['data']
    return details['counts']['hotspots']
     
def process_statechannels_json(this_json):
    # this function deals with a json that has multiple state channels
    global cum_packets
    global cum_dcs
    global hotspot_dict
    global min_timestamp
    global max_timestamp
    print("%-25s %-10s %-25s %8s %10s %10s" % 
    ('type', 'timestamp', 'datetime', 'hotspots', 'packets', 'DCs'))
    for statechannel in this_json:
        # convert the timestamp to a datetime
        this_time = datetime.datetime.fromtimestamp(statechannel['time'])
        # keep track of min/max timestamps
        min_timestamp = min(min_timestamp, statechannel['time'])
        max_timestamp = max(max_timestamp, statechannel['time'])
        number_hotspots = len(statechannel['state_channel']['summaries'])
        # reset the counters for this state channel
        number_packets = 0
        number_dcs = 0
        # handle each hotspot in this state channel
        for summary in statechannel['state_channel']['summaries']:
            number_packets += summary['num_packets']
            number_dcs += summary['num_dcs']
            this_hotspot = summary['client']
            # look in the dict for previous number_packets, if not found, return 0
            previous_number_packets = hotspot_dict.get(this_hotspot, 0)
            hotspot_dict.update({this_hotspot: previous_number_packets + summary['num_packets']})
            # don't lookup the country here, that would make too many API calls
        # add this state channel's numbers to the cumulative total
        cum_packets += number_packets
        cum_dcs += number_dcs                
        print("%-25s %-10s %-25s %8d %10d %10d" % 
        (statechannel['type'], statechannel['time'],
        this_time.strftime("%m/%d/%Y, %H:%M:%S"), number_hotspots, number_packets, number_dcs))

# START OF SCRIPT

# global variables for sums
cum_packets = 0   # cumulative packets
cum_dcs = 0       # cumulative DCs
hotspot_dict = {} # dictionary with key: hotspot and value: cumulative packets
# keep track of first/last timestamps
min_timestamp = 4106401354 # initialise as a random date in 2100
max_timestamp = 0

# the Helium API uses cursors for paging
# first URL does not need cursor
cursor = ''
print('===========================================================')
print('RETRIEVE PACKETS AND DC DATA FROM THE HELIUM BLOCKCHAIN API')
print('===========================================================')
print('timespan:', NUMBER_OF_DAYS, 'day(s)')
print('first we load all the state channel data in this timespan')
print('each URL has a cursor to next batch of data')
print('===========================================================')
# loop until returned new_cursor is empty = no more pages
while (True):
    this_statechannels_json, new_cursor = get_statechannels(cursor)
    process_statechannels_json(this_statechannels_json)
    if new_cursor == '':
        break
    else:
        cursor = new_cursor

print('===========================================================')
print('overview for the last NUMBER_OF_DAYS:', NUMBER_OF_DAYS)
print('earliest timestamp:\t', datetime.datetime.fromtimestamp(min_timestamp).strftime("%m/%d/%Y, %H:%M:%S"))
print('latest timestamp:\t', datetime.datetime.fromtimestamp(max_timestamp).strftime("%m/%d/%Y, %H:%M:%S"))
print('total packets:\t', cum_packets, '\t per day:\t', round(cum_packets / NUMBER_OF_DAYS))
print('total dcs:\t', cum_dcs, '\t per day:\t', round(cum_dcs / NUMBER_OF_DAYS))
print('avg dcs/packet:\t', round(cum_dcs/cum_packets, 2))
print('value of traffic: USD', round(cum_dcs * USD_PER_DC, 2), 
    '\t per day: USD', round((cum_dcs * USD_PER_DC) / NUMBER_OF_DAYS, 2))   
hotspots_number = len(hotspot_dict)
published_hotspots_count = get_hotspot_count()
active_hotspot_pct = round(100 * (hotspots_number / published_hotspots_count),2 ) 
print('number of active hotspots:\t', hotspots_number,  
    '(' + str(active_hotspot_pct) + '% of the published number of', 
    published_hotspots_count, 'hotspots)')
# as a sanity check, retrieve the total DC burns 
dcburns_sum = get_dcburns()
dcburns_delta_pct = 100 * ((dcburns_sum - cum_dcs) / dcburns_sum)
print('sanity check: \tdcburns sum:', dcburns_sum, 'delta:', str(round(dcburns_delta_pct, 2)) + '%')
if (dcburns_delta_pct > 1):
    print("delta exceeds 1% so our dataset is incomplete (http failed because too many requests?), STOP HERE")
    quit()
print('===========================================================')

# sort the dictionary by the values, descending
hotspots_sorted = sorted(hotspot_dict.items(), key=lambda x: x[1], reverse=True)
# save this list to a csv file
now_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
this_filename = 'csv_output/' + now_string + 'hotspots_data_packets' + \
    str(NUMBER_OF_DAYS) + '.csv'
with open(this_filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['rank', 'hotspot address', 'number of packets'])
    rank = 0
    for hotspot in hotspots_sorted:
        rank += 1
        csvwriter.writerow([rank, hotspot[0], hotspot[1]])
print('saved sorted hotspot list to', this_filename)
print('===========================================================')
print('plot packets for Helium hotspot ranked (over this timespan)')
this_filename = 'plot_output/' + now_string + 'hotspots_data_packets' + \
    str(NUMBER_OF_DAYS) + '.png'
print('save plot image to', this_filename)
ys = [hotspot[1] for hotspot in hotspots_sorted]
xs = [x for x in range(len(ys))]
plt.figure(num=this_filename)
plt.plot(xs, ys)
plt.title('packets per Helium hotspot ranked (over ' + str(NUMBER_OF_DAYS) + ' days)')
plt.ylabel('packets')
plt.yscale('log')
plt.xlim(0, len(xs))
plt.grid()
plt.savefig(this_filename)
print('close the plot window to continue..')
plt.show()
print('===========================================================')

# we use fractions here 0-1, but display percentages later 0-100%
cum_fraction_packets = 0    # reset cumulative fraction of packets
index = 0                   # rank of hotspot
country_dict = {}           # dictionary with key: country and value: cumulative packets

print('RANK HOTSPOTS BY RECEIVED PACKETS')
print("%6s %-55s %7s %7s %7s %s" % 
    ('rank','hotspot','packets','share','cumul','location'))
for hotspot in hotspots_sorted:
    index += 1
    this_fraction_packets = hotspot[1]/cum_packets
    cum_fraction_packets += this_fraction_packets
    this_location = get_hotspot_location(hotspot[0]) # this does an API call
    print("%6d %-55s %7d %6.2f%% %6.2f%% %s" % 
    (index, hotspot[0], hotspot[1], 
    this_fraction_packets * 100, cum_fraction_packets * 100, this_location))
    # extract the country from this_location, but get_hotspot_location sometimes fails
    try:
        this_country = this_location.split(', ')[1]
    except:
        this_country = 'n/a'
    # look in the dict for previous number_packets, if not found, return 0
    previous_number_packets = country_dict.get(this_country, 0)
    country_dict.update({this_country: previous_number_packets + hotspot[1]})

    if cum_fraction_packets > FRACTION_THRESHOLD: 
        break # when we reach the threshold, stop listing hotspots

print('===========================================================')
print(index, 'hotspots are receiving', str(FRACTION_THRESHOLD * 100) + '% of the packets')
print('===========================================================')

print('SHOW PACKETS PER HOTSPOTS IN STEPS OF 1000 HOTSPOTS')
print("%6s %-55s %7s %7s %7s" % 
    ('rank','hotspot','packets','share','cumul'))
rank = 0
cum_fraction_packets = 0
for hotspot in hotspots_sorted:
    rank += 1
    this_fraction_packets = hotspot[1]/cum_packets
    cum_fraction_packets += this_fraction_packets
    if (rank % 1000 == 0):
        print("%6d %-55s %7d %6.2f%% %6.2f%%" % 
        (rank, hotspot[0], hotspot[1], 
        this_fraction_packets * 100, cum_fraction_packets * 100))
print('total active hotspots:', hotspots_number)
print('===========================================================')

# sort the dictionary by the values, descending
countries_sorted = sorted(country_dict.items(), key=lambda x: x[1], reverse=True)    

print('RANK COUNTRIES BY RECEIVED PACKETS (only based on', index, 'hotspots listed above)')
# looking up the country for all hotspots would require a lot of API calls
print("%4s %-30s %7s %7s" % 
    ('rank','country','packets','share'))
for rank, country in enumerate(countries_sorted):
    print("%4d %-30s %7d %6.2f%%" % 
    (rank + 1, country[0], country[1], round(100 * country[1]/cum_packets, 2)))
print('===========================================================')    
print('END')
print('===========================================================')
    
