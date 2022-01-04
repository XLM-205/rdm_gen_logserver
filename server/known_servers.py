"""Holds a default list of known servers in case this it to be deployed without Database Support or it failed
Expected format for each server: dict{str1: tuple(str2, str3, str4) }, being:
str1: The server's URL, up to the '/';
str2: The server's desired text color (Fore Color) with the '#' (Can be left None for default);
str3: The server's desired back color with the '#' (Can be left None for default);
str4: The server's desired alias / nickname. This will appear appended to the server's URL on each entry
e.g.: known_list = {"http://localhost:5000/": (None, "#0F0F0F", "Local Host (Fallback)") }
"""
known_list = {"http://localhost:5000/": (None, "#0F0F0F", "Local Host (Fallback)"), }
