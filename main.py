from pylablib.devices.Thorlabs import MFF

device_id = '37008483'
flipper = MFF(device_id)  # create instance

# Check current position
current = flipper.get_state()
print("Current position:", current)

# Move to the other position
new_position = 1 - current
flipper.move_to_state(new_position)
print("Moved to position:", new_position)

# Optional: close the device when done
flipper.close()
