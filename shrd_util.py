import glob
import os

# Page Info
PAGE_BYTE = 2048

def getSize(filename):
    if os.path.exists(filename) is False:
        return 0
    st = os.path.getsize(filename)
    return st

def extract_fw_version(filename):
    
    file_bytes_array = open(filename,"rb").read()
    total_size = getSize(filename)
    header_size = total_size % PAGE_BYTE
    file_bytes_array = file_bytes_array[total_size % PAGE_BYTE:]

    num_data_type = {}
    fw_version = "N/A"
    for i in range(0, int(total_size / PAGE_BYTE) ):
        datatype = file_bytes_array[i * PAGE_BYTE]
        if not datatype in num_data_type.keys():
            num_data_type[datatype] = 0

            if datatype == 200:
                fw_version = ""
                for c in file_bytes_array[i * PAGE_BYTE + 30:i * PAGE_BYTE + 44]:
                    if c == 0:
                        break
                    fw_version += (chr(c))
        num_data_type[datatype] = num_data_type[datatype] + 1

            
    return fw_version


files = glob.glob("./**/**/**/*.shrd")


###### Example code to extract FW Version

# if fw_version is N/A, AM Monitor was used to start the data collection
# Otherwise, it used either myRA or DiscoveryRA
for file in files:
    fw_version = extract_fw_version(file)
    print(f"File: {file} FW Version: {fw_version}")



###### Example code to extract files that needs file correction
#
# Add 489ms to the timestamp
for file in files:
    fw_version = extract_fw_version(file)
    if fw_version == "N/A" and "_S" in file:
        print(f"{file}")