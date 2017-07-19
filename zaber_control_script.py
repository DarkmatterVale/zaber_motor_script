import sys
from Zaber import *

MAX_DEVICE_ID = 100
SAVED_SETTINGS_PATH_FILE_LOCATION = "./zaber_settings_file"
LOG_FILE_LOCATION = "./zaber_log"
DEFAULT_SETTINGS_FILE_LOCATION = "./zaber_motor_settings"
SETTINGS_FILE_LOCATION = DEFAULT_SETTINGS_FILE_LOCATION
SETTINGS_DATA = {}
STORED_POSITION_INDEX = 0
CMD_INDEX = 0

def display_help_information():
	print("")
	print("This script allows the user to execute commands for all devices connected. The IDs are locally stored on this computer.")
	print("The following commands can be executed:")
	print("- \"dcd\" : 				Displays all connected devices and their names (if defined)")
	print("- \"sd device_id name\" : 		Sets the specified device (device_id) to have a name (name)")
	print("- \"ssp \"path\"\" :			Sets the location of the settings file (path)")
	print("- \"udsp true\" :			Sets the settings file path to be the default")
	print("- \"rsf true\" :			Resets the settings file")
	print("- \"dsp\" :				Displays the location of the settings file")
	print("- \"mr device_name steps\" :		Executes a MoveRelative command")
	print("- \"ma device_name steps\" :		Executes a MoveAbsolute command")
	print("- \"tmc device_name on/off\" :	Turn manual control on/off")
	print("- \"mh device_name\" :		Move a device to its home position")
	print("- \"rcp device_name\" :		Returns the current position of a device")
	print("- \"scp device_name\" :		Set a motor's current position")
	print("- \"dl\" :				Display log")
	print("- \"cl\" :				Clear log")
	print("- \"quit\" :				Quit the application")
	print("NOTE: If manual tracking is enabled, a command must be run before shutting down the devices (any will work) for position data to be stored.")
	print("")

def set_device_name(command):
	global SETTINGS_DATA

	if len(command.split()) > 1:
		command = command.split()[1:]

		for device_name in SETTINGS_DATA:
			if int(SETTINGS_DATA[device_name]) == int(command[0]):
				del SETTINGS_DATA[device_name]
				break

		SETTINGS_DATA[command[1]] = command[0]

		save_settings_data()

		update_log("Executed sd command; set device #" + str(command[0]) + " to have name: " + command[1])
	else:
		print("ERROR : sd command was not passed the correct parameters")

def display_settings_location():
	global SETTINGS_FILE_LOCATION

	print("Settings file location: " + SETTINGS_FILE_LOCATION)

def save_settings_data():
	with open(SETTINGS_FILE_LOCATION, 'w+') as settings_file:
		encoded_data = encode_data(SETTINGS_DATA)

		settings_file.write(encoded_data)

def load_saved_settings_file():
	global SETTINGS_FILE_LOCATION

	try:
		with open(SAVED_SETTINGS_PATH_FILE_LOCATION, 'r') as saved_settings_path_file:
			SETTINGS_FILE_LOCATION = saved_settings_path_file.read()
	except:
		update_saved_settings_path_file()

def load_settings_file():
	global SETTINGS_DATA

	load_saved_settings_file()

	try:
		with open(SETTINGS_FILE_LOCATION, 'r') as settings_file:
			raw_data = settings_file.read()

			SETTINGS_DATA = decode_data(raw_data)
	except:
		pass

def decode_data(raw_data):
	loaded_data = {}
	lines = raw_data.split("\n")

	for line in lines:
		line_data_list = line.split(",")

		if len(line_data_list) > 1:
			loaded_data[line_data_list[0]] = str(line_data_list[1])

	return loaded_data

def encode_data(raw_data):
	encoded_data_string = ""

	for key in raw_data:
		line_data = key + "," + str(raw_data[key][0]) + "\n"
		encoded_data_string += line_data

	return encoded_data_string

def is_device_connected(device_index):
	try:
		port_facade.GetConversation(device_index)

		return True
	except:
		return False

def display_all_connected_devices():
	print("")
	for device_index in range(1, MAX_DEVICE_ID):
		if is_device_connected(device_index):
			device_name = get_device_name(device_index)
			device_position = 0
			try:
				device_position = get_current_position_with_id(device_index).Data
			except:
				pass
			print("Device #" + str(device_index) + " - Status : CONNECTED/OK - Name : " + device_name + " - Current Position: " + str(device_position))
	print("")

def set_settings_file_path(command):
	global SETTINGS_FILE_LOCATION

	if len(command.split("\"")) > 1:
		cleaned_command = command.split("\"")[1]
		SETTINGS_FILE_LOCATION = cleaned_command

		update_saved_settings_path_file()
		save_settings_data()
	else:
		print("ERROR : ssp command was not passed the correct parameters")

def update_saved_settings_path_file():
	with open(SAVED_SETTINGS_PATH_FILE_LOCATION, 'w+') as saved_settings_path_file:
		saved_settings_path_file.write(SETTINGS_FILE_LOCATION)

def move_absolute(command):
	global SETTINGS_DATA

	if len(command.split()) > 2:
		device_name = command.split()[1]
		steps = command.split()[2]

		response = run_command(device_name, Command.MoveAbsolute, steps)
		print("Command responded with: " + str(response.Data))
		update_log("Executed ma command; moved device " + str(device_name) + " by " + str(steps))
	else:
		print("ERROR : ma command was not passed the correct parameters")

def move_relative(command):
	global SETTINGS_DATA

	if len(command.split()) > 2:
		device_name = command.split()[1]
		steps = command.split()[2]

		response = run_command(device_name, Command.MoveRelative, steps)
		print("Command responded with: " + str(response.Data))
		update_log("Executed mr command; moved device " + str(device_name) + " by " + str(steps))
	else:
		print("ERROR : mr command was not passed the correct parameters")

def move_device_to_home_position(command):
	global SETTINGS_DATA

	if len(command.split()) > 1:
		device_name = command.split()[1]

		response = run_command(device_name, Command.Home, 0)
		print("Command responded with: " + str(response.Data))
		update_log("Executed mh command; moved device " + str(device_name) + " to position 0")
	else:
		print("ERROR : mh command was not passed the correct parameters")

def toggle_manual_control(command):
	if len(command.split()) > 2:
		device_name = command.split()[1]
		status = -1
		if "on" in command.split()[2].lower():
			status = 0
		elif "off" in command.split()[2].lower():
			status = 8

		if status != -1:
			try:
				response = run_command(device_name, Command.SetDeviceMode, status)
				print("Command responded with: " + str(response.Data))
				update_log("Executed tmc command; set " + str(device_name) + " to have manual control " + command.split()[2].lower())
			except:
				print(str(device_name) + " is not compatible with manual control commands")
		else:
			print("Toggle Manual Control command was not passed a valid status...Please retry")
	else:
		print("ERROR : tmc command was not passed valid parameters")

def set_current_position(command):
	global SETTINGS_DATA

	if len(command.split()) > 2:
		device_name = command.split()[1]
		current_position = command.split()[2]

		response = run_command(device_name, Command.SetCurrentPosition, current_position)
		print("Command responded with: " + str(response.Data))
		update_log("Executed scp command; set device " + str(device_name) + " to have a position " + str(current_position))
	else:
		print("ERROR : scp command was not passed valid parameters")

def display_current_position(command):
	if len(command.split()) > 1:
		device_name = command.split()[1]

		response = get_current_position(device_name)
		print("Current Position: " + str(response.Data))
	else:
		print("ERROR : rcp command was not passed valid parameters")

def get_current_position(device_name):
	return run_command(device_name, Command.ReturnCurrentPosition, 0)

def get_current_position_with_id(device_id):
	return run_command_with_id(device_id, Command.ReturnCurrentPosition, 0)

def load_log_file():
	log = ""
	try:
		with open(LOG_FILE_LOCATION, 'r') as log_file:
			log = log_file.read()
	except:
		pass

	return log

def update_log(data):
	log = load_log_file()
	log += str(CMD_INDEX) + ") " + data + "\n"

	with open(LOG_FILE_LOCATION, 'w+') as log_file:
		log_file.write(log)

def display_log():
	print(load_log_file())

def reset_settings_file():
	global SETTINGS_DATA

	SETTINGS_DATA = {}
	save_settings_data()

def get_device_name(device_id):
	for name in SETTINGS_DATA:
		if int(SETTINGS_DATA[name]) == int(device_id):
			return name

	return "Null"

def clear_log():
	with open(LOG_FILE_LOCATION, 'w+') as log_file:
		log_file.write("")

def run_command(device_name, command, command_data):
	device_conversation = port_facade.GetConversation(int(SETTINGS_DATA[device_name]))
	response = device_conversation.Request(command, int(command_data))

	return response

def run_command_with_id(device_id, command, command_data):
	device_conversation = port_facade.GetConversation(int(device_id))
	response = device_conversation.Request(command, int(command_data))

	return response

def initialize_motors():
	global SETTINGS_DATA

	for device_index in range(1, MAX_DEVICE_ID):
		if is_device_connected(device_index):
			run_command_with_id(device_index, Command.SetCurrentPosition, 0)

	for i in range(2):
		updated_settings_data = {}
		for device_name in SETTINGS_DATA:
			try:
				device_position = run_command(device_name, Command.ReturnStoredPosition, STORED_POSITION_INDEX).Data
				run_command(device_name, Command.SetCurrentPosition, int(device_position))
				print("Set " + device_name + " to saved position value: " + str(device_position))
				updated_settings_data[device_name] = SETTINGS_DATA[device_name]
			except:
				pass

		SETTINGS_DATA = updated_settings_data

def save_all_device_positions():
	for device_name in SETTINGS_DATA:
		try:
			run_command(device_name, Command.StoreCurrentPosition, STORED_POSITION_INDEX)
		except:
			print("Error could not store current position for " + device_name)

def manage_devices():
	global CMD_INDEX

	if CMD_INDEX == 0:
		initialize_motors()
		CMD_INDEX += 1

def use_default_settings_file():
	global SETTINGS_FILE_LOCATION

	SETTINGS_FILE_LOCATION = DEFAULT_SETTINGS_FILE_LOCATION
	update_saved_settings_path_file()

while True:
	load_settings_file()
	manage_devices()
	command = raw_input("Please enter a command (type \"help\" for a list of commands) ")

	if "help" in command.lower().split()[0]:
		display_help_information()
	elif "dcd" in command.lower().split()[0]:
		display_all_connected_devices()
	elif "ssp" in command.lower().split()[0]:
		set_settings_file_path(command)
	elif "udsp true" in command.lower().split()[0]:
		use_default_settings_file()
	elif "dsp" in command.lower().split()[0]:
		display_settings_location()
	elif "sd" in command.lower().split()[0]:
		set_device_name(command)
	elif "mh" in command.lower().split()[0]:
		move_device_to_home_position(command)
	elif "mr" in command.lower().split()[0]:
		move_relative(command)
	elif "ma" in command.lower().split()[0]:
		move_absolute(command)
	elif "tmc" in command.lower().split()[0]:
		toggle_manual_control(command)
	elif "scp" in command.lower().split()[0]:
		set_current_position(command)
	elif "rcp" in command.lower().split()[0]:
		display_current_position(command)
	elif "dl" in command.lower().split()[0]:
		display_log()
	elif "rsf true" in command.lower():
		reset_settings_file()
	elif "cl" in command.lower().split()[0]:
		clear_log()
	elif "quit" in command.lower().split()[0]:
		sys.exit(0)
	else:
		print("Could not process command: \"" + command + "\"")
		CMD_INDEX -= 1

	CMD_INDEX += 1
	save_settings_data()
	save_all_device_positions()
