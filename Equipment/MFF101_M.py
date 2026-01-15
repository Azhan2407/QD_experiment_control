from pylablib.devices.Thorlabs import MFF

device_id = '37008483'
flipper = MFF(device_id)  # create instance


if __name__=="__main__":
    # Check current position
    current = flipper.get_state()
    print("Current position:", current)

    # Move to the other position
    new_position = 1 - current
    flipper.move_to_state(new_position)
    print("Moved to position:", new_position)

    # Optional: close the device when done
    flipper.close()



#Requires

# CDM2123620_Setup (1).zip
# From https://ftdichip.com

# and 

# Thorlabs_XA_Setup_26500_x64.exe
# From https://www.thorlabs.com