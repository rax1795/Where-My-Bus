########################################################################
#Bus Search Telegram Chat BOT
########################################################################

import requests
import json
import datetime, time 
import re

########################################################################
# global variables 
########################################################################

my_token = '' # put your secret Telegram token here 
url_base = 'https://api.telegram.org/bot{}/'.format(my_token)

url_busArrival = 'http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2'
url_busRoutes = 'http://datamall2.mytransport.sg/ltaodataservice/BusRoutes'
#r = requests.get(url=url_busArrival, headers=headers, params=params)
# if you read page 6 of the LTA data mall, notice that ALL requests to the data 
# mall must include headers, for example:
headers = {
	'AccountKey': '', # enter your account key here (check your email when you sign up in LTA data mall) 
	'accept': 'application/json'
}

########################################################################
# Telegram method URLs
########################################################################

url_getUpdates = '{}getupdates'.format(url_base)
url_sendMsg = '{}sendMessage'.format(url_base)


def get_updates(offset): #function to get the latest updates from telegram via getUpdates API
	params = {'timeout':100,'offset':offset} #set timeout to 100 seconds to allow for long polling 
	r = requests.get(url_getUpdates,params)
	r = r.json()
	print(r)
	return r

def send_message(chat_id,text): #function to send message om telegram just need to input the chat_id of the person being called and the text
	# write code here 
	params = {'chat_id':chat_id, 'text':text}
	r = requests.post(url_sendMsg, params)
	return

def send_welcome(result): #function to send welcome message to user in the event user enters /start
	# write code here 
	for i in result:
		if i['message']['text'] == '/start':
			params = {'chat_id':i['message']['from']['id'], 'text':'Welcome '+i['message']['from']['first_name']+'! Please type in your bus stop code to get the all the bus arrival times for your bus stop. You can also select to find the arrival timings for a specific bus at your bus stop, to do so enter your request in the format Bus Stop Code,Bus No eg. 45399,979'}
			requests.post(url_sendMsg, params)
	return

def listen_and_reply(result): #function to listen to messages from users and reply appropriately 
	for i in result:
		if i['message']['text'] != '/start':
			if i['message']['text'].isdigit() and len(i['message']['text']) == 5:
				get_busarrival_api(i['message']['from']['id'],i['message']['text'])
			elif re.match("\d{5,5}[\w\s,.]*\d*", i['message']['text']) is not None: #checks if message matches the pattern "5 digits | any number of spaces/delimiters/random words-1 | any number of digits for bus no" (assuming bus no is evoloving and can be more than the usual 3) "
				busList = re.findall("\d{1,5}\w*", i['message']['text']) #will return a list of in the form [bus stop code, bus stop number]
				bus_stop_code = busList[0]
				busno = busList[1]
				get_busarrival_api_specificbus(i['message']['from']['id'],bus_stop_code,busno)
			else:
				params = {'chat_id':i['message']['from']['id'], 'text':'The Bus Stop code or Bus No seems wrong '+i['message']['from']['first_name']+'. If you are trying to select a specific bus, please enter your request in the format Bus Stop Code,Bus No eg. 45399,979'}
				requests.post(url_sendMsg, params)
		else:
			send_welcome(result)

	return None

def compute_busarrival(estimated_arrival): #function to compute bus arrival timings based on the estimated arrival retrieved via BusArrival Api 
	current_time = datetime.datetime.now() #set current time to the datetime at the moment
	format_str = '%Y-%m-%dT%H:%M:%S+08:00'
	next_arrival_time = datetime.datetime.strptime(estimated_arrival, format_str) #converts the estimated arrival from string to datetime
	time_diff = next_arrival_time - current_time
	minutes = int(time_diff.total_seconds()/60) #as per LTA Documentation estimated minutes should presented rounded down to the nearest minute, utilizing typecasting to integer to do this 
	if minutes <= 1: #as per LTA Documentation any arrival minutes less than 1 should be indicated as 'Arr'
		text = "Arr"
		return text
	else:
		text = str(minutes) + " min"
		return text

def get_busarrival_api(chatid,bus_stop_code): #function takes in the chatid, and bus_stop_code to provide run the LTA Bus Arrival API to retrieve the services and their estimated timings at the specified bus_stop_code
	params = {'BusStopCode':bus_stop_code}
	r = requests.get(url=url_busArrival, headers=headers, params=params)
	d = r.json()
	servicesdict= {}
	busarrival_msg = ''
	if d['Services'] != []:
		for t in d['Services']: 
			servicesdict[t['ServiceNo']] = [t['NextBus']['EstimatedArrival'],t['NextBus2']['EstimatedArrival'],t['NextBus3']['EstimatedArrival']]
		for k,v in servicesdict.items():
			busarrival_msg +="Bus: "+ str(k) + " --> "
			for i in range(0,len(v)):
					if v[i] == '':
						busarrival_msg += 'No Est, ' #in the event that the estimated arrival is blank, the message to be sent will be No Est
					else:
						busarrival_msg +=(compute_busarrival(v[i]) +", ")
			busarrival_msg = busarrival_msg[0:(len(busarrival_msg)-2)] + "\n\n"
		send_message(chatid,busarrival_msg)
		return 
	else:
		send_message(chatid,'The Bus Stop code seems wrong, Please check and re-enter Bus Stop Code')  #in the event the d['services] returns an empty list, we assume that there is an error in the bus stop code entered and thus prompt user to check the code
		return

def get_busarrival_api_specificbus(chatid,bus_stop_code,busno): #function takes in the chatid, bus stop code and busno to run the LTA Bus Arrrival API to retireve the specified service and their estimated timings at the specified bus_stop_code
	params = {'BusStopCode':bus_stop_code,'ServiceNo':busno} 
	r = requests.get(url=url_busArrival, headers=headers, params=params)
	d = r.json()
	servicesdict= {}
	busarrival_msg = ''
	if d['Services'] != []:
		for t in d['Services']:
			servicesdict[t['ServiceNo']] = [t['NextBus']['EstimatedArrival'],t['NextBus2']['EstimatedArrival'],t['NextBus3']['EstimatedArrival']]
			print(servicesdict)
		busarrival_msg +="Bus: "+ busno + " --> "
		bus = servicesdict[busno]
		for i in range(0,3):
			if bus[i] == '':
				busarrival_msg += 'No Est, ' #in the event that the estimated arrival is blank, the message to be sent will be No Est
			else:
				busarrival_msg +=(compute_busarrival(bus[i]) +", ")
		busarrival_msg = busarrival_msg[0:(len(busarrival_msg)-2)] + "\n\n"
		send_message(chatid,busarrival_msg)
		return
	else:
		send_message(chatid,'The Bus '+ str(busno) +' you are looking for may not operate at this Bus Stop code or is currently not in operation, or the bus stop code may be wrong. Pease check and re-enter Bus Stop Code and Bus No')
		#in the event the d['services] returns an empty list, we assume that there is an error in the bus stop code or bus no entered and thus prompt user to check the code and bus no
		return

def run(): #function to run the programme
	offset = 0
	while True:
		result = get_updates(offset)
		result = result['result']
		if len(result) > 0:
			offset = result[-1]['update_id'] + 1 #increases offset by the latest update_id +1 so that results will be retrived accordingly
			listen_and_reply(result)
run()
