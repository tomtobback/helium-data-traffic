# Helium Data Traffic Analysis
## Background
[Helium](https://www.helium.com/) is a LoRaWAN network built on a blockchain, to provide incentives to run a 'hotspot' that provides network coverage for IoT devices using LoRaWAN radio technology. It has been growing extremely fast, adding over 80,000 hotspots per month, with at the start of 2022 more than half a million already installed and providing coverage (except for the ones run by scammers; location spoofing is a big problem for the Helium network).

Of course the assumption is that more and more people will start using this network to send real IoT device data. Sending data over the network is very cheap, and uses [Data Credits (DC)](https://docs.helium.com/use-the-network/console/data-credits). 

**The question we are trying to answer here is, nevermind the hype, how much real data traffic does the Helium network currently see?**

[Web3Index](https://web3index.org/helium) does an excellent job showing the trend of DC related to data traffic, but here we want to dig a bit deeper to check data packet numbers vs hotspots: how many hotspots are actually doing real work?

## Example script output

This plot is based on 7 days of traffic data (9-16 Feb 2022).

![](plot_output/20220216145329hotspots_data_packets7.png)

The script tells us (see [sample_output.txt](sample_output.txt)):

- Total number of data packets was 82,130,820 or 11,732,974 per day
- Total number of active hotspots was 122,258
- The average DC per data packet was 1.63
- The average DC value of the total traffic per day was USD 191
- The most active hotspot saw 1.38% of total data packets. Its location has not been set, but searching it up on [Explorer](https://explorer.helium.com/hotspots/11npZsFTPjND7bZZfnk2mcQfryaQJDRYWcr2nwiy584bdvc6pAY) shows that its owner has 33 hotspots in Taiwan. Taiwan dominates the list of most active hotspots.
- Only 54 hotspots account for 20% of all data traffic in this period
- Half of the active hotspots saw less than 10 packets over a week

With 'active hotspot' I mean a hotspot that sees real data traffic, not only the Proof-of-Coverage exchanges.

## Preliminary interpretation
(this is based on the above 7 day period, results may change over time)

- Only around 20% of the published Helium hotspots (574,000+) are involved in data traffic, the other 80% (450,000+) hotspots are not seeing any data traffic.
- At least 10% of data traffic is seen by a dozen hotspots in Taiwan, probably for stress testing devices/gateways. Germany also has some extremely busy hotspots.
- Around 90% of data traffic is seen by around 7,000 hotspots; in other words, 90% of traffic is handled by 1.2% of total installed hotspots.
- When running the analysis for the last 24 hours only, the number of active hotspots can go down to 10%, but the ratio of 90% of traffic seen by 7,000 hotspots seems to hold.

Note that although I hope this is interesting, data packet traffic is not a reliable metric to evaluate the actual use of the Helium network, as it can easily be inflated by people who have an interest to do so; that would be cheap both in terms of hardware and DC required. 

## Methodology

The details of data traffic transactions happen in **state channels**, a 'layer 2' technology to keep the huge number of transactions off the main 'layer 1' blockchain. Only the summaries of these DC transactions become part of the Helium blockchain. Helium allows us to access the blockchain via an [API](https://docs.helium.com/api/blockchain/introduction).

The python script [helium_data_traffic_analysis.py](helium_data_traffic_analysis.py) uses this API to analyse the data traffic:

- for a given NUMBER_OF_DAYS we retrieve all the state channels
- sum the data packets and DCs
- keep track of the data packets per hotspot
- rank this list to find the most active hotspots
- save this list as CSV, plot a graph and save as PNG
- list the most active hotspots with their location, until a given FRACTION_THRESHOLD is reached
- rank the countries of the most active hotspots

It would be interesting to retrieve the location for all hotspots but that requires an API call per hotspot and would take rather long.

## Running the script
Clone this repo, or just copy the main script (in that case you may need to manually create the `csv_output` and `plot_output` directories).

The only configuration parameters are at the top of the script:
```
FRACTION_THRESHOLD = 0.2    # cut the hotspot ranking when we reach this fraction 0-1
NUMBER_OF_DAYS = 3          # how many days to go back from now
```

Increasing `FRACTION_THRESHOLD` slows down the completion of the script, as it will make an API call for each hotspot to retrieve its location.

A sample output can be found [here](sample_output.txt), with the related [CSV file](csv_output/20220216145329hotspots_data_packets7.csv) and [plot](plot_output/20220216145329hotspots_data_packets7.png).

Details of each hotspot can be found by searching the [Helium Explorer](https://explorer.helium.com) with the hotspot address.

## To do

- Map the 7,000 hotspots that cover 90% of the data traffic
- Compare the overall HNT rewards of these 7,000 most active hotspots to the network average to see to what extent Proof-of-Coverage correlates with data traffic intensity
- ...

## Disclaimer

It is very well possible that mistakes were made in the script and in the above interpretation, I am open to corrections and suggestions.

I got interested in Helium when I saw dozens of hotspots appearing in my area, which all turned out to be fake. I am trying to contribute to [mapping](https://cassiopeia.hk/finding-real-helium-hotspots-in-hong-kong) of real Helium network coverage in Hong Kong, and I remain a big fan of The Things Network.



 


