########################################################################
# ay18t2-smt203-asm-01
# team members:
# 	1.Wong Xiao Rong
# 	2.Rajiv Abraham Xavier
########################################################################

import requests
import json
import datetime, time 

########################################################################
# global variables 
########################################################################

my_token = '' # put your secret Telegram token here 
url_base = 'https://api.telegram.org/bot{}/'.format(my_token)

url_busArrival = 'http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2'
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


def get_updates(offset):
	params = {'timeout':100,'offset':offset}
	r = requests.get(url_getUpdates,params)
	r = r.json()
	return r

def send_message(chat_id,text):
	# write code here 
	params = {'chat_id':chat_id, 'text':text}
	r = requests.post(url_sendMsg, params)
	return

def send_welcome(result):
	# write code here 
	for i in result:
		if i['message']['text'] == '/start':
			params = {'chat_id':i['message']['from']['id'], 'text':'Welcome '+i['message']['from']['first_name']+'! Please type in your bus stop code to get the bus arrival times'}
			requests.post(url_sendMsg, params)
	return

def listen_and_reply(result):
	for i in result:
		if i['message']['text'] != '/start':
			if (i['message']['text']).isdigit() == True:
				get_busarrival_api(i['message']['from']['id'],i['message']['text'])

			else:
				params = {'chat_id':i['message']['from']['id'], 'text':'The Bus Stop code seems wrong, '+i['message']['from']['first_name']+' Pease check and re-enter Bus Stop Code'}
				requests.post(url_sendMsg, params)
	return None

def compute_busarrival(estimated_arrival):
	current_time = datetime.datetime.now()
	format_str = '%Y-%m-%dT%H:%M:%S+08:00'
	next_arrival_time = datetime.datetime.strptime(estimated_arrival, format_str)
	time_diff = next_arrival_time - current_time
	minutes = (time_diff.seconds//60)%60
	if minutes <= 1:
		text = "Arr"
		return text
	else:
		text = str(minutes)
		return text

def get_busarrival_api(chatid,bus_stop_code):
	params = {'BusStopCode':bus_stop_code}
	r = requests.get(url=url_busArrival, headers=headers, params=params)
	d = r.json()
	servicesdict= {}
	print(d['Services'])
	if d['Services'] != []:
		for t in d['Services']:
			servicesdict[t['ServiceNo'],d['BusStopCode']] = [t['NextBus']['EstimatedArrival'],t['NextBus2']['EstimatedArrival'],t['NextBus3']['EstimatedArrival']]
		busarrival_msg = ''
		for k,v in servicesdict.items():
			print(k,v)
			busarrival_msg ="Bus Stop Code: "+ str(k[1]) +" ServiceNo: "+ str(k[0]) + " --> "
			for i in range(0,3):
					if i == 2:
						if v[i] == '':
							busarrival_msg += "NA \n\n"
						else:
							busarrival_msg +=(compute_busarrival(v[i]) +"\n\n")
					else:
						if v[i] == '':
							busarrival_msg += "NA,"
						else:
						 busarrival_msg +=(compute_busarrival(v[i]) + ",")
		send_message(chatid,busarrival_msg)
	else:
		send_message(chatid,'The Bus Stop code seems wrong, Pease check and re-enter Bus Stop Code')
		return
	
def listen_and_reply2(chat_id):
	# write code here
	r = requests.get(url_getUpdates)
	d = r.json()
	for i in d['result']:
		bus_code = i['message']['text']
		get_busarrival_api(bus_code)
	return 

def run():
	offset = 0
	while True:
		result = get_updates(offset)
		result = result['result']
		if len(result) > 0:
			offset = result[-1]['update_id'] + 1
			print(offset)
		send_welcome(result)
		listen_and_reply(result)

run()
