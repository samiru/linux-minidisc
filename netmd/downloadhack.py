#!/usr/bin/python
import os
import sys
import getopt
import usb1
import libnetmd
from Crypto.Cipher import DES

# USAGE
#######
# first: create an uncompressed 16-bit stereo PCM:
# ffmpeg -i $audiofile -f s16be test.raw
#######
# plug in your NetMD using USB and use this script accordingly (title is optional):
# sudo python downloadhack.py --filename ~/music/test.raw --title songtitle

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-b', '--bus')
parser.add_option('-d', '--device')
parser.add_option('-f', '--filename')
parser.add_option('-t', '--title')
(options, args) = parser.parse_args()
assert len(args) < 4
filename=options.filename
if options.title != None:
    title=options.title
else:
    title="no title"

def main(bus=None, device_address=None):
    context = usb1.LibUSBContext()
    for md in libnetmd.iterdevices(context, bus=bus,
                                   device_address=device_address):
        md_iface = libnetmd.NetMDInterface(md)
        DownloadHack(md_iface)

class EKBopensource:
    def getRootKey(self):
        return "\x12\x34\x56\x78\x9a\xbc\xde\xf0\x0f\xed\xcb\xa9\x87\x65\x43\x21"

    def getEKBID(self):
        return 0x26422642

    def getEKBDataForLeafId(self,leaf_id):
        return (["\x25\x45\x06\x4d\xea\xca\x14\xf9\x96\xbd\xc8\xa4\x06\xc2\x2b\x81",
                 "\xfb\x60\xbd\xdd\x0d\xbc\xab\x84\x8a\x00\x5e\x03\x19\x4d\x3e\xda"], 9, \
                "\x8f\x2b\xc3\x52\xe8\x6c\x5e\xd3\x06\xdc\xae\x18\xd2\xf3\x8c\x7f\x89\xb5\xe1\x85\x55\xa1\x05\xea")

framecount=int(os.path.getsize(filename)/2048)

class MDTrack:
    def getTitle(self):
        return title

    def getFramecount(self):
        return framecount

    def getDataFormat(self):
        return libnetmd.WIREFORMAT_PCM

    def getContentID(self):
        # value probably doesn't matter
        return "\x01\x0F\x50\0\0\4\0\0\0" "\x48\xA2\x8D\x3E\x1A\x3B\x0C\x44\xAF\x2f\xa0"

    def getKEK(self):
        # value does not matter
        return "\x14\xe3\x83\x4e\xe2\xd3\xcc\xa5"

    def getPacketcount(self):
        return 1

    def getPackets(self):
        # values do not matter at all
        datakey = "\x96\x03\xc7\xc0\x53\x37\xd2\xf0"
        firstiv = "\x08\xd9\xcb\xd4\xc1\x5e\xc0\xff"
        keycrypter = DES.new(self.getKEK(), DES.MODE_ECB)
        key = keycrypter.encrypt(datakey)
        datacrypter = DES.new(key, DES.MODE_CBC, firstiv)
        file = open(filename)
        file.read(60)
        data = file.read(framecount*2048)
        return [(datakey,firstiv,datacrypter.encrypt(data))]

def DownloadHack(md_iface):
    try:
        md_iface.sessionKeyForget()
        md_iface.leaveSecureSession()
    except:
        None
    try:
        md_iface.disableNewTrackProtection(1)
    except libnetmd.NetMDNotImplemented:
        print "Can't set device to non-protecting"
    trk = MDTrack()
    md_session = libnetmd.MDSession(md_iface, EKBopensource())

    (track, uuid, ccid) = md_session.downloadtrack(trk)

    print 'Track:', track
    print "UUID:",''.join(["%02x"%ord(i) for i in uuid])
    print "Confirmed Content ID:",''.join(["%02x"%ord(i) for i in ccid])
    md_session.close()

if __name__ == '__main__':
    main(bus=options.bus, device_address=options.device)

