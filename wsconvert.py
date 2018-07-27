#!/usr/bin/python3

import sys
import argparse

def specialchars(x):
    return {
        0x0D : 0x0A, #New line
        0x19 : 0x2A, #italic
        0x13 : 0x2A, #underline->italic
        0x02 : 0x2A, #bold
        0x14 : 0x5E, #superscript
        0x16 : 0x7E, #subscript
        0x18 : 0x7E  #strikethrough
    }.get(x,0)

def handleblock(block):
    # implement here the handling of the blocks
    # block[0] is the length of the block (int)
    # block[2] is the command
    if block[2]==0x03:
        footerdata = converttext(block[20:]).replace(b'\n',b'')
        return b'^['+footerdata+b']' 
    return b''

def converttext(data):
    counter=-1
    newline = False
    dotline = False
    outdata=bytearray()
    while counter<len(data)-1:
        counter+=1
        # Extended character
        if data[counter]==0x1B:
            outdata.append(data[counter+1])
            counter += 2
        # Symmetrical sequence: 1Dh special character
        elif data[counter]==0x1D:
            jump=int.from_bytes(data[counter+1:counter+2],byteorder='little')
            if not args.textmode:
                outdata += (handleblock(data[counter+1:counter+jump]))
            counter += jump+2
        elif data[counter]<0x20:    # special formatting characters
            if not args.textmode:
                c=specialchars(data[counter])
                if not c==0:
                    outdata.append(c)
                if data[counter]==0x02 or data[counter]==0x18:
                    outdata.append(c)   # duplicating some characters
            if data[counter]==0x0D: # handle newline to check dot commands
                outdata.append(0x0A)
                newline = True
                dotline = False
        elif data[counter]<0x80:    # other characters
            if newline:
                newline = False
                if data[counter]==0x2E:
                    dotline = True
            if not dotline:
                outdata.append(data[counter])
    return outdata

print("Basic WordStar to Markdown converter")
print("====================================")
# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("ws_file",help="the WordStar file to convert")
parser.add_argument("-o","--output", help="output file name")
parser.add_argument("-t","--textmode", help="output to unformatted (text) file",
                    action="store_true")
args = parser.parse_args()

if args.output:
    outputfile = args.output
else:
    extension = ".txt" if args.textmode else ".md"
    pp=args.ws_file.find('.')
    outfilename=args.ws_file[0:pp]+extension

#Read file
print("Reading "+args.ws_file)
with open(args.ws_file,"rb") as infile:
    data=infile.read()

# Let's go through the file for some cleanup...
print("Converting...");
outdata = converttext(data)

# Now decode the extended ascii data...
outstring=outdata.decode("cp437")
with open(outfilename,"wt") as outfile:
    outfile.write(outstring)
print("Conversion ready, "+outfilename+" written!")
