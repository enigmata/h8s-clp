Import usb1
import libusb1

# TODO: put these into a config yaml file:
INSTEON_PLM_USB_VENDOR_ID  = 0x0403
INSTEON_PLM_USB_PRODUCT_ID = 0x6001
INSTEON_PLM_CMD_GETVERSION = '\x02\x60'

# Insteon service exceptions
class InsteonException(Exception):
    def __init__(self, msg):
        self.data = msg
class InsteonPLMConfigError(InsteonException): pass
class InsteonPLMConfigInfo(InsteonException):  pass


def init():
    plm_handle = usb1.USBContext().openByVendorIDAndProductID(INSTEON_PLM_USB_VENDOR_ID, INSTEON_PLM_USB_PRODUCT_ID)
    if plm_handle is None:
        raise InsteonPLMConfigError('Unable to find an Insteon PLM connected via USB')

    plm_device = plm_handle.getDevice()
    print plm_device

    # obtain the two in/out endpoints needed for 
    # communications with the PLM
    try:
        for config in plm_device.iterConfigurations():
            for interface in config:
                for interface_setting in interface:
                    # both the endpoints we need must
                    # be within an interface
                    plm_write_address = None
                    plm_read_address  = None
                    for endpoint in interface_setting:
                        ep = endpoint.getAddress()
                        if (ep & libusb1.USB_ENDPOINT_DIR_MASK) == libusb1.LIBUSB_ENDPOINT_IN:
                            plm_read_address = ep
                            plm_read_maxsize = endpoint.getMaxPacketSize()
                        else:
                            plm_write_address = ep
                            plm_write_maxsize = endpoint.getMaxPacketSize()
                    if plm_read_address and plm_write_address:
                        raise InsteonPLMConfigInfo('Endpoints found: in = 0x%02x, out = 0x%02x' % 
                                                   (plm_read_address, plm_write_address))

        # after searching all configurations and their interfaces
        # no pair of in/out endpoints was found
        raise InsteonPLMConfigError('PLM USB endpoints not found')

    except InsteonPLMConfigInfo as Config:
        print 'PLM Config: %s' % (Config.data)
    except InsteonPLMConfigError as Err:
        print 'PLM Configuration Error: %s' % (Err.data)
        raise Err
    except:
        raise InsteonPLMConfigError('Unknown PLM Configuration Error')

    plm_handle.claimInterface(interface_setting.getNumber())

    data = INSTEON_PLM_CMD_GETVERSION + ('\x00' * (plm_write_maxsize - len(INSTEON_PLM_CMD_GETVERSION)))
    print 'cmd len = %d, cmd = %s' % (len(data), repr(data))

    plm_handle.bulkWrite(plm_write_address, data)
    result = plm_handle.bulkRead(plm_read_address, plm_read_maxsize)
    #print 'len = %d, result = %09x %09x %09x %09x' % (len(result), bytearray(result)[0],bytearray(result)[1],bytearray(result)[2],bytearray(result)[3])
    #print 'len = %d, cmd = %s' % (len(INSTEON_PLM_CMD_GETVERSION), repr(INSTEON_PLM_CMD_GETVERSION))
    print 'len = %d, result = %s' % (len(result), repr(result))

if __name__ == '__main__':
    init()
