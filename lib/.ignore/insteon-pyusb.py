import usb.core
import usb.util


def init():

    # find our device
    dev = usb.core.find(idVendor=0x0403, idProduct=0x6001)
    
    # was it found?
    if dev is None:
        raise ValueError('PLM was not found')
        return
    
    # set the active configuration. With no arguments, the first
    # configuration will be the active one and the PLM has
    # only one configuration
    try:
        dev.set_configuration()
    except usb.core.USBError as Err:
        print( 'PLM USB config erro: %s, errno=%d' % ( Err.strerror, Err.errno ) )
        return
    
    # get an endpoint instance for outbound PLM requests and
    # and endpoint instance for inbound PLM responses
    cfg = dev.get_active_configuration()
    intf = cfg[(0,0)]
    
    epOUT = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = lambda e:
            usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
    )
    assert epOUT is not None
    
    epIN = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = lambda e:
            usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
    )
    assert epIN is not None
    
    # ask the PLM what version it is
    bytesWritten = epOUT.write('02 60')
    if bytesWritten < 4 : print( 'error: did not send complete command' )
    
    response = epIN.read( 64 )
    print( 'Response: ', response )

    # at this point, we deem the PLM to active and healthy
    # and our USB communications fully established to the PLM

if __name__ == '__main__':
    init()

