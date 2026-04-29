#!/usr/bin/env python3

import sys
import argparse
import re

HEADING_RE = re.compile(r"^#+ ")

HEADING=""
def specialchars(x):
    return {
        0x0D : 0,    # skip newline handling
        0x0A : 0,
        0x02 : 0x2A, #bold
        0x04 : 0x2A, #double strike->bold
        0x0F : 0x20, #binding space
        0x13 : 0x2A, #underline->italic
        0x19 : 0x2A, #italic
        0x14 : 0x5E, #superscript
        0x16 : 0x7E, #subscript
        0x18 : 0x7E, #strikethrough
        0x1E : 0,    #inactive soft hyphen: strip
        0x1F : 0x2D  #active soft hyphen
    }.get(x,0)

def process_dotline(buf):
    """Emit markdown for a buffered dot command line (buf includes the leading dot)."""
    cmd = bytes(buf[1:3]).upper() if len(buf) >= 3 else b''
    if cmd in (b'PA', b'CP'):
        return b'\n---\n'
    return b''

def handleblock(block):
    # block[0] is the length of the block (int)
    # block[2] is the command type
    if block[2] == 0x03: # footnote
        notedata = converttext(block[20:]).replace(b'\n',b'')
        return b'^['+notedata+b']'
    elif block[2] == 0x04: # endnote
        notedata = converttext(block[20:]).replace(b'\n',b'')
        return b'^['+notedata+b']'
    elif block[2] == 0x05: # annotation
        annotdata = converttext(block[20:]).replace(b'\n',b'')
        return b'<!-- '+annotdata+b' -->'
    elif block[2] == 0x06: # comment: strip
        return b''
    elif block[2] == 0x09: # TAB
        return b'    '
    elif block[2] == 0x0B: # end of page
        return b'\n---\n'
    elif block[2] == 0x0E: # index item: strip
        return b''
    elif block[2] == 0x11: # paragraph style
        if block[3] == 0x02: # header
            return b'## '
        elif block[3] == 0x03: # subheading
            return b'### '
        elif block[3] == 0x05: # title
            return b'# '
    return b''

def converttext(data):
    counter=-1
    newline = False
    linetype = 0
    dotline_buf = bytearray()
    outdata=bytearray()
    global HEADING
    while counter<len(data)-1:
        counter+=1
        # End of file character
        if data[counter] == 0x1A:
            break
        # Extended character
        elif data[counter]==0x1B:
            outdata.append(data[counter+1])
            counter += 2
        # Symmetrical sequence: 1Dh special character
        elif data[counter]==0x1D:
            jump=int.from_bytes(data[counter+1:counter+2],byteorder='little')
            if not args.textmode:
                outdata += (handleblock(data[counter+1:counter+jump]))
                if len(outdata) > 2:
                   HEADING=outdata.decode("cp437").split(" ",1)[-1]
            counter += jump+2
        elif data[counter]<0x20:    # special formatting characters
            if data[counter] == 0x0D and not newline:
                if linetype == 0:
                    outdata += b'\x0A\x0A'
                elif linetype == 1 and not args.textmode:
                    outdata += process_dotline(dotline_buf)
                    dotline_buf = bytearray()
                newline = True
                linetype = 0
            elif data[counter] == 0x0C and not args.textmode: # form feed -> horizontal rule
                outdata += b'\n---\n'
            if not args.textmode:   # handle formatting for markdown
                c=specialchars(data[counter])
                if not c == 0:
                    outdata.append(c)
                if data[counter] in (0x02, 0x04, 0x18):
                    outdata.append(c)   # duplicating ** and ~~

        elif data[counter]<0x80:    # other characters
            if newline:
                newline = False
                if data[counter] == 0x2E: # dotline
                    linetype = 1
                    dotline_buf = bytearray()
                #if data[counter] == 0x2D: # special line (list)
                #    outdata.pop()
            if linetype == 1:
                dotline_buf.append(data[counter])
            else:
                outdata.append(data[counter])
        elif data[counter] == 0x8D: # soft return (word-wrap line break)
            outdata.append(0x0A)
        elif data[counter]<0xFF:
            outdata.append(data[counter] - 0x80)
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
    outputfile=args.ws_file[0:pp]+extension

#Read file
print("Reading "+args.ws_file)
with open(args.ws_file,"rb") as infile:
    data=infile.read()

# Let's go through the file for some cleanup...
print("Converting...");
outdata = converttext(data)

if HEADING and not args.output:
   outputfile=f"{HEADING.strip()}.md"
# Now decode the extended ascii data...
outstring=outdata.decode("cp437")
with open(outputfile,"wt", newline='\n') as outfile:
    outfile.write(outstring.replace("\x0D",""))
print("Conversion ready, "+outputfile+" written!")
