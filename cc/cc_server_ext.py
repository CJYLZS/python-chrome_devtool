import sys
import json
import struct

def getMessage():
    '''
    # Python 3.x version
    # Read a message from stdin and decode it.
    '''
    rawLength = sys.stdin.buffer.read(4)
    if len(rawLength) == 0:
        sys.exit(0)
    messageLength = struct.unpack('@I', rawLength)[0]
    message = sys.stdin.buffer.read(messageLength)
    return message


def encodeMessage(messageContent):
    '''
    # Encode a message for transmission,
    # given its content.
    '''
    encodedContent = json.dumps(messageContent).encode('utf-8')
    encodedLength = struct.pack('@I', len(encodedContent))
    return {'length': encodedLength, 'content': encodedContent}


def sendMessage(encodedMessage):
    '''
    # Send an encoded message to stdout
    '''
    sys.stdout.buffer.write(encodedMessage['length'])
    sys.stdout.buffer.write(encodedMessage['content'])
    sys.stdout.buffer.flush()



