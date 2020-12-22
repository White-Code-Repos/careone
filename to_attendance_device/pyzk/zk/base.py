# -*- coding: utf-8 -*-
from datetime import datetime
from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, socket, timeout
from struct import pack, unpack
import codecs
import sys

from . import const
from .attendance import Attendance
from .exception import ZKErrorResponse, ZKNetworkError, TimeoutError
from .user import User
from .finger import Finger

import logging

_logger = logging.getLogger(__name__)


def make_commkey(key, session_id, ticks=50):
    """take a password and session_id and scramble them to send to the time
    clock.
    copied from commpro.c - MakeKey"""
    key = int(key)
    session_id = int(session_id)
    k = 0
    for i in range(32):
        if (key & (1 << i)):
            k = (k << 1 | 1)
        else:
            k = k << 1
    k += session_id

    k = pack(b'I', k)
    k = unpack(b'BBBB', k)
    k = pack(
        b'BBBB',
        k[0] ^ ord('Z'),
        k[1] ^ ord('K'),
        k[2] ^ ord('S'),
        k[3] ^ ord('O'))
    k = unpack(b'HH', k)
    k = pack(b'HH', k[1], k[0])

    B = 0xff & ticks
    k = unpack(b'BBBB', k)
    k = pack(
        b'BBBB',
        k[0] ^ B,
        k[1] ^ B,
        B,
        k[3] ^ B)
    return k


class ZK_helper(object):
    """ helper class to check connection and protocol"""

    def __init__(self, ip, port=4370):
        self.address = (ip, port)
        self.ip = ip
        self.port = port
        # self.timeout = timeout
        # self.password = password # passint
        # self.firmware = int(firmware) #TODO check minor version?
        # self.tcp = tcp

    def test_ping(self):
        """
        Returns True if host responds to a ping request
        """
        import subprocess, platform
        # Ping parameters as function of OS
        ping_str = "-n 1" if  platform.system().lower() == "windows" else "-c 1 -W 5"
        args = "ping " + " " + ping_str + " " + self.ip
        need_sh = False if  platform.system().lower() == "windows" else True
        # Ping
        return subprocess.call(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=need_sh) == 0

    def test_tcp(self):
        self.client = socket(AF_INET, SOCK_STREAM)
        self.client.settimeout(10)  # fixed test
        res = self.client.connect_ex(self.address)
        self.client.close()
        return res

    def test_udp(self):  # WIP:
        self.client = socket(AF_INET, SOCK_DGRAM)
        self.client.settimeout(10)  # fixed test


class ZK(object):

    is_connect = False

    __data_recv = None
    __sesion_id = 0
    __reply_id = 0
    __timeout = 0
    max_uid = 0

    def __init__(self, ip, port=4370, timeout=60, password=0, force_udp=False, ommit_ping=False, verbose=False, encoding='UTF-8'):
        self.__timeout = timeout
        self.is_connect = False
        self.is_enabled = True  # let's asume
        self.helper = ZK_helper(ip, port)
        self.__address = (ip, port)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.settimeout(self.__timeout)
        self.__password = password  # passint
        self.force_udp = force_udp
        self.ommit_ping = ommit_ping
        self.verbose = verbose
        self.encoding = encoding
        self.tcp = False
        self.users = 0
        self.records = 0
        self.user_packet_size = 28  # default zk6
        self.end_live_capture = False
        self.__session_id = 0
        self.__reply_id = const.USHRT_MAX - 1
        self.__data_recv = None
        self.__data = None

    def __create_socket(self):
        """ based on self.tcp"""
        if self.tcp:
            self.__sock = socket(AF_INET, SOCK_STREAM)
            self.__sock.settimeout(self.__timeout)
            self.__sock.connect_ex(self.__address)
        else:
            self.__sock = socket(AF_INET, SOCK_DGRAM)
            self.__sock.settimeout(self.__timeout)

    def __create_tcp_top(self, packet):
        """ witch the complete packet set top header """
        length = len(packet)
        top = pack('<HHI', const.MACHINE_PREPARE_DATA_1, const.MACHINE_PREPARE_DATA_2, length)
        return top + packet

    def __create_header(self, command, command_string, session_id, reply_id):
        '''
        Puts a the parts that make up a packet together and packs them into a byte string

        MODIFIED now, without initial checksum
        '''
        # checksum = 0 always? for calculating
        buf = pack('<4H', command, 0, session_id, reply_id) + command_string
        buf = unpack('8B' + '%sB' % len(command_string), buf)
        checksum = unpack('H', self.__create_checksum(buf))[0]
        reply_id += 1
        if reply_id >= const.USHRT_MAX:
            reply_id -= const.USHRT_MAX

        buf = pack('<4H', command, checksum, session_id, reply_id)
        return buf + command_string

    def __create_checksum(self, p):
        '''
        Calculates the checksum of the packet to be sent to the time clock
        Copied from zkemsdk.c
        '''
        l = len(p)
        checksum = 0
        while l > 1:
            checksum += unpack('H', pack('BB', p[0], p[1]))[0]
            p = p[2:]
            if checksum > const.USHRT_MAX:
                checksum -= const.USHRT_MAX
            l -= 2
        if l:
            checksum = checksum + p[-1]

        while checksum > const.USHRT_MAX:
            checksum -= const.USHRT_MAX

        checksum = ~checksum

        while checksum < 0:
            checksum += const.USHRT_MAX

        return pack('H', checksum)

    def __test_tcp_top(self, packet):
        """ return size!"""
        if len(packet) <= 8:
            return 0  # invalid packet
        tcp_header = unpack('<HHI', packet[:8])
        if tcp_header[0] == const.MACHINE_PREPARE_DATA_1 and tcp_header[1] == const.MACHINE_PREPARE_DATA_2:
            return tcp_header[2]
        return 0  # never everis 0!

    def __send_command(self, command, command_string=b'', response_size=8):
        '''
        send command to the terminal
        '''
        buf = self.__create_header(command, command_string, self.__session_id, self.__reply_id)
        try:
            if self.tcp:
                top = self.__create_tcp_top(buf)
                self.__sock.send(top)
                self.__tcp_data_recv = self.__sock.recv(response_size + 8)
                self.__tcp_length = self.__test_tcp_top(self.__tcp_data_recv)
                if self.__tcp_length == 0:
                    raise ZKNetworkError("TCP packet invalid")
                self.__header = unpack('<4H', self.__tcp_data_recv[8:16])
                self.__data_recv = self.__tcp_data_recv[8:]  # dirty hack
            else:
                self.__sock.sendto(buf, self.__address)
                self.__data_recv = self.__sock.recv(response_size)
                self.__header = unpack('<4H', self.__data_recv[:8])
        except timeout as e:
            raise TimeoutError("Timeout!")
        except Exception as e:
            raise ZKNetworkError(str(e))

        self.__response = self.__header[0]
        self.__reply_id = self.__header[3]
        self.__data = self.__data_recv[8:]  # could be empty
        if self.__response in [const.CMD_ACK_OK, const.CMD_PREPARE_DATA, const.CMD_DATA]:
            return {
                'status': True,
                'code': self.__response
            }
        return {
            'status': False,
            'code': self.__response
        }

    def __get_data_size(self):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        response = self.__response
        if response == const.CMD_PREPARE_DATA:
            size = unpack('I', self.__data[:4])[0]
            return size
        else:
            return 0

    def __reverse_hex(self, hex):
        data = ''
        for i in reversed(range(int(len(hex) / 2))):
            data += hex[i * 2:(i * 2) + 2]
        return data

    def __decode_time(self, t):
        """Decode a timestamp retrieved from the timeclock

        copied from zkemsdk.c - DecodeTime"""
        """
        t = t.encode('hex')
        t = int(self.__reverse_hex(t), 16)
        if self.verbose: print ("decode from  %s "% format(t, '04x'))
        """
        t = unpack("<I", t)[0]
        second = t % 60
        t = t // 60

        minute = t % 60
        t = t // 60

        hour = t % 24
        t = t // 24

        day = t % 31 + 1
        t = t // 31

        month = t % 12 + 1
        t = t // 12

        year = t + 2000

        d = datetime(year, month, day, hour, minute, second)

        return d

    def __decode_timehex(self, timehex):
        """timehex string of six bytes"""
        year, month, day, hour, minute, second = unpack("6B", timehex)
        year += 2000
        d = datetime(year, month, day, hour, minute, second)
        return d

    def __encode_time(self, t):
        """Encode a timestamp so that it can be read on the timeclock
        """
        # formula taken from zkemsdk.c - EncodeTime
        # can also be found in the technical manual
        d = (
            ((t.year % 100) * 12 * 31 + ((t.month - 1) * 31) + t.day - 1) *
            (24 * 60 * 60) + (t.hour * 60 + t.minute) * 60 + t.second
        )
        return d

    def connect(self):
        '''
        connect to the device
        '''
        self.end_live_capture = False  # jic
        if not self.ommit_ping and not self.helper.test_ping():
            raise ZKNetworkError("can't reach device (ping %s)" % self.__address[0])
        if not self.force_udp and self.helper.test_tcp() == 0:  # ok
            self.tcp = True
            self.user_packet_size = 72  # default zk8
        self.__create_socket()  # tcp based
        self.__session_id = 0
        self.__reply_id = const.USHRT_MAX - 1
        try:
            cmd_response = self.__send_command(const.CMD_CONNECT)
            self.__session_id = self.__header[2]
            if cmd_response.get('code') == const.CMD_ACK_UNAUTH:
                _logger.debug("Trying authentication...")
                command_string = make_commkey(self.__password, self.__session_id)
                cmd_response = self.__send_command(const.CMD_AUTH, command_string)
        except TimeoutError as e:
            msg = "Could not connect to the device at {} via port {} due to timeout!".format(self.__address[0], self.__address[1])
            _logger.error(msg)
            raise TimeoutError(msg)

        if cmd_response.get('status'):
            self.is_connect = True
            # set the session id
            return self
        else:
            if cmd_response["code"] == const.CMD_ACK_UNAUTH:
                raise ZKErrorResponse("Unauthenticated")

            _logger.error("ZK Connect err response {} ".format(cmd_response["code"]))
            raise ZKErrorResponse("Invalid response: Can't connect")

    def disconnect(self):
        '''
        diconnect from the connected device
        '''
        self.is_connect = False
        cmd_response = self.__send_command(const.CMD_EXIT)
        if cmd_response.get('status'):
            if self.__sock:
                self.__sock.close()  # leave to GC
            return True
        else:
            raise ZKErrorResponse("can't disconnect")

    def disable_device(self):
        '''
        disable (lock) device, ensure no activity when process run
        '''
        cmd_response = self.__send_command(const.CMD_DISABLEDEVICE)
        if cmd_response.get('status'):
            self.is_enabled = False
            return True
        else:
            raise ZKErrorResponse("Can't Disable")

    def enable_device(self):
        '''
        re-enable the connected device
        '''
        cmd_response = self.__send_command(const.CMD_ENABLEDEVICE)
        if cmd_response.get('status'):
            self.is_enabled = True
            return True
        else:
            raise ZKErrorResponse("Can't enable device")

    def get_firmware_version(self):
        '''
        return the firmware version
        '''
        cmd_response = self.__send_command(const.CMD_GET_VERSION, b'', 1024)
        if cmd_response.get('status'):
            firmware_version = self.__data.split(b'\x00')[0]
            return firmware_version.decode()
        else:
            raise ZKErrorResponse("Can't read frimware version")

    def _get_options_rrq(self, command_string):
        '''
        common method for others to extend which want const.CMD_OPTIONS_RRQ
        '''
        '''
        return the serial number
        '''
        command = const.CMD_OPTIONS_RRQ
        response_size = 1024
        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            serialnumber = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            return serialnumber
        else:
            raise ZKErrorResponse("Invalid response")

    def get_serialnumber(self):
        '''
        return the serial number
        '''
        command_string = b'~SerialNumber'
        return self._get_options_rrq(command_string).replace(b'=', b'').decode()

    def get_oem_vendor(self):
        '''
        return the OEM Vendor of the device
        '''
        command_string = b'~OEMVendor'
        return self._get_options_rrq(command_string).decode()

    def get_fingerprint_algorithm(self):
        '''
        return the Fingerprint Algorithm (aka ZKFPVersion) of the device
        '''
        command_string = b'~ZKFPVersion'
        return self._get_options_rrq(command_string).decode()

    def get_platform(self):
        '''
        return the platform on which the device is based, e.g. ZMM100_TFT
        '''
        command_string = b'~Platform'
        return self._get_options_rrq(command_string).replace(b'=', b'').decode()

    def get_device_name(self):
        '''
        return the name of the device, e.g. B3-C
        '''
        command_string = b'~DeviceName'
        return self._get_options_rrq(command_string).decode()

    def get_workcode(self):
        '''
        return the work code
        '''
        command_string = b'~WCFO'
        return self._get_options_rrq(command_string).decode()

    def restart(self):
        '''
        restart the device
        '''
        command = const.CMD_RESTART
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't restart device")

    def poweroff(self):
        '''
        shutdown the device
        '''
        command = const.CMD_POWEROFF
        command_string = b''
        response_size = 1032
        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't poweroff")

    def refresh_data(self):
        '''
        shutdown the device
        '''
        command = const.CMD_REFRESHDATA
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't refresh data")

    def test_voice(self, index=0):
        '''
        play test voice
         0 acceso correcto / acceso correcto
         1 password incorrecto / clave incorrecta
         2 la memoria del terminal está llena / acceso denegado
         3 usuario invalido /codigo no valido
         4 intente de nuevo  por favor / intente de nuevo por favor *
         5 reintroduszca codigo de usuario /reintroduszca codigo
         6 memoria del terminal llena /-
         7 memoria de alm fich llena /-
         8 huella duplicada / huella duplicada
         9 acceso denegado / ya ha sido registrado
         10 *beep* / beep kuko
         11 el sistema vuelve al modo de verificacion / beep siren
         12 por favor coloque su dedo  o acerque tarjeta  /-
         13 acerca su tarjeta de nuevo  /beep bell
         14 excedido tiempo p esta operacion  /-
         15 coloque su dedo de nuevo  /-
         16 coloque su dedo por ultima vez  /-
         17 ATN numero de tarjeta está repetida  /-
         18 proceso de registro correcto *  /-
         19 borrado correcto /-
         20 Numero de usuario / ponga la caja de ojos
         21 ATN se ha llegado al max num usuarios /-
         22 verificacion de usuarios /-
         23 usuario no registrado /-
         24 ATN se ha llegado al num max de registros /-
         25 ATN la puerta no esta cerrada /-
         26 registro de usuarios /-
         27 borrado de usuarios /-
         28 coloque su dedo  /-
         29 registre la tarjeta de administrador /-
         30 0 /-
         31 1 /-
         32 2 /-
         33 3 /-
         34 4 /-
         35 5 /-
         36 6 /-
         37 7 /-
         38 8 /-
         39 9 /-
         40 PFV seleccione numero de usuario /-
         41 registrar /-
         42 operacion correcta /-
         43 PFV acerque su tarjeta /-
         43 la tarjeta ha sido registrada /-
         45 error en operacion /-
         46 PFV acerque tarjeta de administracion, p confirmacion /-
         47 descarga de fichajes /-
         48 descarga de usuarios /-
         49 carga de usuarios /-
         50 actualizan de firmware /-
         51 ejeuctar ficheros de configuracion /-
         52 confirmación de clave de acceso correcta /-
         53 error en operacion de tclado /-
         54 borrar todos los usuarios /-
         55 restaurar terminal con configuracion por defecto /-
         56 introduzca numero de usuario /-
         57 teclado bloqueado /-
         58 error en la gestión de la tarjeta  /-
         59 establezca una clave de acceso /-
         60 pulse el teclado  /-
         61 zona de accceso invalida /-
         62 acceso combinado invĺlido /-
         63 verificación multiusuario /-
         64 modo de verificación inválido /-
         65 - /-

        '''
        command = const.CMD_TESTVOICE
        command_string = pack("I", index)
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            return False  # some devices doesn't support sound
            # raise ZKErrorResponse("can't test voice")

    def set_user(self, uid, name, privilege=0, password='', group_id='', user_id='', card=0):
        '''
        create or update user by uid
        '''
        command = const.CMD_USER_WRQ
        if not user_id:
            user_id = str(uid)  # ZK6 needs uid2 == uid
        # uid = chr(uid % 256) + chr(uid >> 8)
        if privilege not in [const.USER_DEFAULT, const.USER_ADMIN]:
            privilege = const.USER_DEFAULT
        privilege = int(privilege)
        if self.user_packet_size == 28:  # self.firmware == 6:
            if not group_id:
                group_id = 0
            try:
                command_string = pack('HB5s8sIxBHI', uid, privilege, password.encode(self.encoding, errors='ignore'), name.encode(self.encoding, errors='ignore'), card, int(group_id), 0, int(user_id))
            except Exception as e:
                _logger.error("s_h Error pack: %s", e)
                _logger.error("Error pack: %s", sys.exc_info()[0])
                raise ZKErrorResponse("Can't pack user")
        else:
            name_pad = name.encode(self.encoding, errors='ignore').ljust(24, b'\x00')[:24]
            card_str = pack('i', int(card))[:4]
            if isinstance(group_id, int):
                group_id = str(group_id)
            command_string = pack('HB8s24s4sx7sx24s', uid, privilege, password.encode(self.encoding, errors='ignore'), name_pad, card_str, group_id.encode(), user_id.encode())
        response_size = 1024  # TODO check response?
        cmd_response = self.__send_command(command, command_string, response_size)
        if not cmd_response.get('status'):
            _logger.error("Could not Set User: name_pad: %s, uid: %s, user_id: %s", name_pad, uid, user_id)
            raise ZKErrorResponse("Can't set user")
        _logger.debug("Set User: name_pad: %s, uid: %s, user_id: %s", name_pad, uid, user_id)
        self.max_uid = int(uid)
        self.refresh_data()

    def get_max_uid(self):
        """
        This method will get the max uid either from the device of object cache (if any)
        """
        if not self.max_uid:
            # call get_users to get self.max_uid set
            self.get_users()
        return self.max_uid

    def delete_user(self, uid=0, user_id=''):
        '''
        delete specific user by uid, user_id
        '''
        if self.tcp:
            if  not user_id:
                # we need user_id (uid2)
                users = self.get_users()
                if len(users) == 1:
                    user_id = users[0].user_id
                else:
                    return False
            command = 133  # const.CMD_DELETE_USER_2
            command_string = pack('24s', str(user_id).encode(encoding=self.encoding, errors='ignore'))
        else:
            if not uid:
                users = self.get_users()
                users = list(filter(lambda x: x.user_id == str(user_id), users))
                if not users:
                    return False
                uid = users[0].uid
            command = const.CMD_DELETE_USER
            command_string = pack('h', uid)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't delete user")
        self._decrease_max_uid()
        self.refresh_data()

    def _decrease_max_uid(self):
        """
        This method will decrease self.max_uid by 1 if it is set in the object cache
        """
        if self.max_uid > 0:
            self.max_uid -= 1

    def __recieve_tcp_data(self, data_recv, size):
        """ data_recv, raw tcp packet
         must analyze tcp_length

         must return data, broken
         """
        data = []
        tcp_length = self.__test_tcp_top(data_recv)  # tcp header
        _logger.debug("tcp_length {}, size {}".format(tcp_length, size))
        if tcp_length <= 0:
            _logger.error("Incorrect tcp packet")
            return None, b""
        if (tcp_length - 8) < size:  # broken on smaller DATAs
            _logger.debug("tcp length too small... retrying")
            resp, bh = self.__recieve_tcp_data(data_recv, tcp_length - 8)
            data.append(resp)
            size -= len(resp)
            _logger.debug("new tcp DATA packet to fill misssing {}".format(size))
            data_recv = bh + self.__sock.recv(size)  # ideal limit?
            resp, bh = self.__recieve_tcp_data(data_recv, size)
            data.append(resp)
            _logger.debug("for misssing {} recieved {} with extra {}".format(size, len(resp), len(bh)))
            return b''.join(data), bh
        recieved = len(data_recv)
        _logger.debug("recieved {}, size {}".format(recieved, size))
        # if (tcp_length - 16) > (recieved - 16): #broken first DATA
        #    #reparse as more data packets?
        #    if self.verbose: print ("trying".format(recieved, size))
        #    _data, bh = self.__recieve_tcp_data(data_recv, tcp_length-16)
        # analize first response
        response = unpack('HHHH', data_recv[8:16])[0]
        if recieved >= (size + 32):  # complete with ACK_OK included
            if response == const.CMD_DATA:
                resp = data_recv[16 : size + 16]  # no ack?
                _logger.debug("resp complete len {}".format(len(resp)))
                return resp, data_recv[size + 16:]
            else:
                _logger.error("incorrect response!!! {}".format(response))
                return None, b""  # broken
        else:  # response DATA incomplete (or missing ACK_OK)
            _logger.debug("try DATA incomplete (actual valid {})".format(recieved - 16))
            data.append(data_recv[16 : size + 16 ])  # w/o DATA tcp and header
            size -= recieved - 16  # w/o DATA tcp and header
            broken_header = b""
            if size < 0:  # broken ack header?
                broken_header = data_recv[size:]
                _logger.error("broken header", (broken_header).encode('hex'))  # TODO python3
            if size > 0:  # need raw data to complete
                data_recv = self.__recieve_raw_data(size)
                data.append(data_recv)  # w/o tcp and header
            return b''.join(data), broken_header
            # get cmd_ack_ok on __rchunk

    def __recieve_raw_data(self, size):
        """ partial data ? """
        data = []
        _logger.debug("expecting {} bytes raw data".format(size))
        while size > 0:
            data_recv = self.__sock.recv(size)  # ideal limit?
            recieved = len(data_recv)
            _logger.debug("partial recv {}".format(recieved))
            data.append(data_recv)  # w/o tcp and header
            size -= recieved
            _logger.debug("still need {}".format(size))
        return b''.join(data)

    def __recieve_chunk(self):
        """ recieve a chunk """
        if self.__response == const.CMD_DATA:  # less than 1024!!!
            if self.tcp:  # MUST CHECK TCP SIZE
                _logger.debug("_rc_DATA! is {} bytes, tcp length is {}".format(len(self.__data), self.__tcp_length))
                if len(self.__data) < (self.__tcp_length - 8):
                    need = (self.__tcp_length - 8) - len(self.__data)
                    _logger.debug("need more data: {}".format(need))
                    more_data = self.__recieve_raw_data(need)
                    return b''.join([self.__data, more_data])
                else:  # enough data
                    _logger.debug("Enough data")
                    return self.__data
            else:  # UDP
                _logger.debug("_rc len is {}".format(len(self.__data)))
                return self.__data  # without headers
        elif self.__response == const.CMD_PREPARE_DATA:
            data = []
            size = self.__get_data_size()
            _logger.debug("recieve chunk: prepare data size is {}".format(size))
            if self.tcp:
                if len(self.__data) >= (8 + size):  # prepare data with actual data! should be 8+size+32
                    data_recv = self.__data[8:]  # test, maybe -32
                else:
                    data_recv = self.__sock.recv(size + 32)  # could have two commands
                resp, broken_header = self.__recieve_tcp_data(data_recv, size)
                data.append(resp)
                # get CMD_ACK_OK
                if len(broken_header) < 16:
                    data_recv = broken_header + self.__sock.recv(16)
                else:
                    data_recv = broken_header
                # could be broken
                if len(data_recv) < 16:
                    _logger.debug("trying to complete broken ACK %s /16" % len(data_recv))
                    _logger.debug(data_recv.encode('hex'))  # todo python3
                    data_recv += self.__sock.recv(16 - len(data_recv))  # TODO: CHECK HERE_!
                if not self.__test_tcp_top(data_recv):
                    _logger.error("invalid chunk tcp ACK OK")
                    return None  # b''.join(data) # incomplete?
                response = unpack('HHHH', data_recv[8:16])[0]
                if response == const.CMD_ACK_OK:
                    _logger.debug("chunk tcp ACK OK!")
                    return b''.join(data)
                _logger.error("bad response %s" % data_recv)
                _logger.error(codecs.encode(data, 'hex'))
                return None

                return resp
            # else udp
            while True:  # limitado por respuesta no por tamaño
                data_recv = self.__sock.recv(1024 + 8)
                response = unpack('<4H', data_recv[:8])[0]
                _logger.debug("# packet response is: {}".format(response))
                if response == const.CMD_DATA:
                    data.append(data_recv[8:])  # header turncated
                    size -= 1024  # UDP
                elif response == const.CMD_ACK_OK:
                    break  # without problem.
                else:
                    # truncado! continuar?
                    _logger.error("broken!")
                    break
                _logger.debug("still needs %s" % size)
            return b''.join(data)
        else:
            _logger.error("invalid response %s" % self.__response)
            return None  # ("can't get user template")

    def __read_chunk(self, start, size):
        """ read a chunk from buffer """
        for _retries in range(3):
            command = 1504  # CMD_READ_BUFFER
            command_string = pack('<ii', start, size)
            if self.tcp:
                response_size = size + 32
            else:
                response_size = 1024 + 8
            cmd_response = self.__send_command(command, command_string, response_size)
            data = self.__recieve_chunk()
            if data is not None:
                return data
        else:
            raise ZKErrorResponse("can't read chunk %i:[%i]" % (start, size))

    def read_with_buffer(self, command, fct=0 , ext=0):
        """ Test read info with buffered command (ZK6: 1503) """
        if self.tcp:
            MAX_CHUNK = 0xFFc0  # arbitrary, below 0x10008
        else:
            MAX_CHUNK = 16 * 1024
        command_string = pack('<bhii', 1, command, fct, ext)
        _logger.debug("rwb cs %s", command_string)
        response_size = 1024
        data = []
        start = 0
        cmd_response = self.__send_command(1503, command_string, response_size)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("RWB Not supported")
        if cmd_response['code'] == const.CMD_DATA:
            #direct!!! small!!!
            if self.tcp:  # MUST CHECK TCP SIZE
                _logger.debug("DATA! is {} bytes, tcp length is {}".format(len(self.__data), self.__tcp_length))
                if len(self.__data) < (self.__tcp_length - 8):
                    need = (self.__tcp_length - 8) - len(self.__data)
                    _logger.debug("need more data: {}".format(need))
                    more_data = self.__recieve_raw_data(need)
                    return b''.join([self.__data, more_data]), len(self.__data) + len(more_data)
                else:  # enough data
                    _logger.debug("Enough data")
                    size = len(self.__data)
                    return self.__data, size
            else:  # udp is direct
                size = len(self.__data)
                return self.__data, size
        # else ACK_OK with size
        size = unpack('I', self.__data[1:5])[0]  # extra info???
        _logger.debug("size fill be %i" % size)
        remain = size % MAX_CHUNK
        packets = (size - remain) // MAX_CHUNK  # should be size /16k
        _logger.debug("rwb: #{} packets of max {} bytes, and extra {} bytes remain".format(packets, MAX_CHUNK, remain))
        for _wlk in range(packets):
            data.append(self.__read_chunk(start, MAX_CHUNK))
            start += MAX_CHUNK
        if remain:
            data.append(self.__read_chunk(start, remain))
            start += remain  # Debug
        self.free_data()
        _logger.debug("_read w/chunk %i bytes" % start)
        return b''.join(data), start

    def free_data(self):
        """ clear buffer"""
        command = const.CMD_FREE_DATA
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't free data")

    def read_sizes(self):
        """ read sizes """
        command = const.CMD_GET_FREE_SIZES
        response_size = 1024
        cmd_response = self.__send_command(command, b'', response_size)
        if cmd_response.get('status'):
            _logger.debug(codecs.encode(self.__data, 'hex'))
            if len(self.__data) >= 80:
                fields = unpack('20i', self.__data[:80])
                self.users = fields[4]
                self.records = fields[8]
                self.__data = self.__data[80:]
            return True
        else:
            raise ZKErrorResponse("can't read sizes")

    def get_users(self):  # ALWAYS CALL TO GET correct user_packet_size
        """ return all user """
        self.read_sizes()  # last update
        if self.users == 0:  # lazy
            return []
        users = []
        max_uid = 0
        userdata, size = self.read_with_buffer(const.CMD_USERTEMP_RRQ, const.FCT_USER)
        _logger.debug("user size {} (= {})".format(size, len(userdata)))
        if size <= 4:
            _logger.debug("WRN: missing user data") # debug
            return []
        total_size = unpack("I", userdata[:4])[0]
        self.user_packet_size = total_size / self.users
        if not self.user_packet_size in [28, 72]:
            _logger.debug("WRN packet size would be  %i" % self.user_packet_size)
        userdata = userdata[4:]
        if self.user_packet_size == 28:  # self.firmware == 6:
            while len(userdata) >= 28:
                uid, privilege, password, name, card, group_id, timezone, user_id = unpack('<HB5s8sIxBhI', userdata.ljust(28, b'\x00')[:28])
                if uid > max_uid: max_uid = uid
                password = (password.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                name = (name.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                # card = unpack('I', card)[0] #or hex value?
                group_id = str(group_id)
                user_id = str(user_id)
                # TODO: check card value and find in ver8
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id, card)
                users.append(user)
                _logger.debug("[6]user:", uid, privilege, password, name, card, group_id, timezone, user_id)
                userdata = userdata[28:]
        else:
            while len(userdata) >= 72:
                uid, privilege, password, name, card, group_id, user_id = unpack('<HB8s24sIx7sx24s', userdata.ljust(72, b'\x00')[:72])
                # u1 = int(uid[0].encode("hex"), 16)
                # u2 = int(uid[1].encode("hex"), 16)
                # uid = u1 + (u2 * 256)
                # privilege = int(privilege.encode("hex"), 16)
                password = (password.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                name = (name.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                group_id = (group_id.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                user_id = (user_id.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                if uid > max_uid: max_uid = uid
                # card = int(unpack('I', separator)[0])
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id, card)
                users.append(user)
                userdata = userdata[72:]

            # set max_uid for the object
            self.max_uid = max_uid
        return users

    def cancel_capture(self):
        '''
        cancel capturing finger
        '''

        command = const.CMD_CANCELCAPTURE
        cmd_response = self.__send_command(command=command)
    def verify_user(self):
        '''
        verify finger
        '''

        command = const.CMD_STARTVERIFY
        # uid = chr(uid % 256) + chr(uid >> 8)
        cmd_response = self.__send_command(command=command)

    def enroll_user(self, uid):
        '''
        start enroll user
        '''

        command = const.CMD_STARTENROLL
        uid = chr(uid % 256) + chr(uid >> 8)
        command_string = pack('2s', uid)
        cmd_response = self.__send_command(command=command, command_string=command_string)
    def clear_data(self, clear_type=5):  # FCT_USER
        '''
        clear all data (include: user, attendance report, finger database )
        2 = FCT_FINGERTMP
        '''
        command = const.CMD_CLEAR_DATA
        command_string = pack("B", clear_type)
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't clear data")

    def get_attendance(self):
        """ return attendance record """
        self.read_sizes()
        if self.records == 0:  # lazy
            return []
        users = self.get_users()
        for user in users:
            _logger.debug("Users: %s", user)

        _logger.debug("Total Records: %s", self.records)
        attendances = []
        attendance_data, size = self.read_with_buffer(const.CMD_ATTLOG_RRQ)
        if size < 4:
            _logger.debug("WRN: no attendance data")  # debug
            return []
        total_size = unpack("I", attendance_data[:4])[0]
        record_size = total_size / self.records
        _logger.debug("record_size is %s", record_size)
        attendance_data = attendance_data[4:]  # total size not used
        if record_size == 8 :  # ultra old format
            while len(attendance_data) >= 8:  #TODO RETEST ZK6!!!
                uid, status, timestamp, punch = unpack('HB4sB', attendance_data.ljust(8, b'\x00')[:8])
                _logger.debug(codecs.encode(attendance_data[:8], 'hex'))
                attendance_data = attendance_data[8:]
                tuser = list(filter(lambda x: x.uid == uid, users))
                if not tuser:
                    user_id = str(uid)  # TODO revisar pq
                else:
                    user_id = tuser[0].user_id
                timestamp = self.__decode_time(timestamp)
                attendance = Attendance(user_id, timestamp, status, punch, uid)  # punch?
                attendances.append(attendance)
        elif record_size == 16:  # extended
            while len(attendance_data) >= 16:  # TODO RETEST ZK6
                user_id, timestamp, status, punch, reserved, workcode = unpack('<I4sBB2sI', attendance_data.ljust(16, b'\x00')[:16])
                user_id = str(user_id)
                _logger.debug(codecs.encode(attendance_data[:16], 'hex'))
                attendance_data = attendance_data[16:]
                tuser = list(filter(lambda x: x.user_id == user_id, users))
                if not tuser:
                    _logger.debug("no uid {}", user_id)
                    uid = str(user_id)
                    tuser = list(filter(lambda x: x.uid == user_id, users))  # refix
                    if not tuser:
                        uid = str(user_id)  # TODO revisar pq
                    else:
                        uid = tuser[0].uid
                        user_id = tuser[0].user_id
                else:
                    uid = tuser[0].uid
                timestamp = self.__decode_time(timestamp)
                attendance = Attendance(user_id, timestamp, status, punch, uid)
                attendances.append(attendance)
        else:
            while len(attendance_data) >= 40:
                uid, user_id, status, timestamp, punch, space = unpack('<H24sB4sB8s', attendance_data.ljust(40, b'\x00')[:40])
                _logger.debug(codecs.encode(attendance_data[:40], 'hex'))
                user_id = (user_id.split(b'\x00')[0]).decode(errors='ignore')
                timestamp = self.__decode_time(timestamp)
                # status = int(status.encode("hex"), 16)

                attendance = Attendance(user_id, timestamp, status, punch, uid)
                _logger.debug(attendance)
                attendances.append(attendance)
                attendance_data = attendance_data[40:]
        return attendances

    def clear_attendance(self):
        '''
        clear all attendance record
        '''
        command = const.CMD_CLEAR_ATTLOG
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't clear response")

    def _send_with_buffer(self, buffer):
        MAX_CHUNK = 1024
        size = len(buffer)
        # free_Data
        self.free_data()
        # send prepare_data
        command = const.CMD_PREPARE_DATA
        command_string = pack('I', size)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't prepare data")
        remain = size % MAX_CHUNK
        packets = (size - remain) // MAX_CHUNK
        start = 0
        for _wlk in range(packets):
            self.__send_chunk(buffer[start:start + MAX_CHUNK])
            start += MAX_CHUNK
        if remain:
            self.__send_chunk(buffer[start:start + remain])

    def __send_chunk(self, command_string):
        command = const.CMD_DATA
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True  # refres_data (1013)?
        else:
            raise ZKErrorResponse("Can't send chunk")


    def save_user_template(self, uid, name, privilege, password, group_id, user_id, fingers=[]):
        """ save user and template """
        user = User(uid, name.encode(encoding=self.encoding, errors='ignore'), privilege, password.encode(encoding=self.encoding, errors='ignore'), group_id.encode(encoding=self.encoding, errors='ignore'), user_id.encode(encoding=self.encoding, errors='ignore'))
        new_fingers = []
        for finger in fingers:
            new_fingers.append(Finger(finger['uid'], finger['fid'], finger['valid'], finger['template']))

        fpack = ""
        table = ""
        table = table.encode(encoding=self.encoding, errors='ignore')
        fpack = fpack.encode(encoding=self.encoding, errors='ignore')
        fnum = 0x10  # possibly flag
        tstart = 0
        for finger in new_fingers:
            tfp = finger.repack_only()
            table += pack("<bHbI", 2, user.uid, fnum + finger.fid, tstart)
            tstart += len(tfp)
            fpack += tfp
        if self.user_packet_size == 28:  # self.firmware == 6:
            upack = user.repack29()
        else:  # 72
            upack = user.repack73()
        head = pack("III", len(upack), len(table), len(fpack))
        packet = head + upack + table + fpack
        self._send_with_buffer(packet)
        command = 110  # Unknown
        command_string = pack('<IHH', 12, 0, 8)  # ??? write? WRQ user data?
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't save utemp")
        self.refresh_data()

    def delete_user_template(self, uid=0, temp_id=0, user_id=''):
        """
        Delete specific template
        for tcp via user_id:
        """
        if self.tcp and user_id:
            command = 134  # unknown?
            command_string = pack('<24sB', str(user_id).encode(encoding=self.encoding, errors='ignore'), temp_id)
            cmd_response = self.__send_command(command, command_string)
            #        users = list(filter(lambda x: x.uid==uid, users))
            if cmd_response.get('status'):
                return True  # refres_data (1013)?
            else:
                return False  # probably empty!
        if not uid:
            users = self.get_users()
            users = list(filter(lambda x: x.user_id == str(user_id), users))
            if not users:
                return False
            uid = users[0].uid
        command = const.CMD_DELETE_USERTEMP
        command_string = pack('hb', uid, temp_id)
        cmd_response = self.__send_command(command, command_string)
        #        users = list(filter(lambda x: x.uid==uid, users))
        if cmd_response.get('status'):
            return True  # refres_data (1013)?
        else:
            return False  # probably empty!

    def get_templates(self):
        """ return array of all fingers """
        templates = []
        templatedata, size = self.read_with_buffer(const.CMD_DB_RRQ, const.FCT_FINGERTMP)
        if size < 4:
            _logger.debug("WRN: no user data") # debug
            return []
        total_size = unpack('i', templatedata[0:4])[0]
        _logger.debug("get template total size {}, size {} len {}".format(total_size, size, len(templatedata)))
        templatedata = templatedata[4:]  # total size not used
        # ZKFinger VX10.0 the only finger firmware tested
        while total_size:
            size, uid, fid, valid = unpack('HHbb', templatedata[:6])
            template = unpack("%is" % (size - 6), templatedata[6:size])[0]
            finger = Finger(uid, fid, valid, template)
            if self.verbose: print(finger)  # test
            templates.append(finger)
            templatedata = templatedata[size:]
            total_size -= size
        return templates
