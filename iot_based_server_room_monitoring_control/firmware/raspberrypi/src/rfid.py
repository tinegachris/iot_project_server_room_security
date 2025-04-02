"""
rfid.py

This module interfaces with an RFID reader connected to the Raspberry Pi.
It provides functions to initialize the reader, read and write data to RFID tags,
and handle authentication and communication with the tags.

Dependencies:
    - RPi.GPIO library (install with `pip install RPi.GPIO`) - Only on Raspberry Pi
    - spidev library (install with `pip install spidev`) - Only on Raspberry Pi
"""

import logging
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import IntEnum
import platform
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RFIDStatus(IntEnum):
    """Status codes for RFID operations."""
    OK = 0
    NO_TAG = 1
    ERROR = 2

@dataclass
class CardInfo:
    """Data class to store card information."""
    name: str
    role: str

# Authorized cards with their UIDs and information
AUTHORIZED_CARDS: Dict[Tuple[int, int, int, int, int], CardInfo] = {
    (5, 74, 28, 185, 234): CardInfo("Card A", "admin"),
    (83, 164, 247, 164, 164): CardInfo("Card B", "IT staff"),
    (20, 38, 121, 207, 132): CardInfo("Card C", "maintenance")
}

# Check if running on Raspberry Pi
try:
    IS_RASPBERRY_PI = platform.machine().startswith('arm')
    if IS_RASPBERRY_PI:
        import RPi.GPIO as GPIO
        import spidev
        logger.info("Running on Raspberry Pi with real RFID hardware")
    else:
        logger.warning("Not running on Raspberry Pi, using mock implementation")
except ImportError:
    IS_RASPBERRY_PI = False
    logger.warning("Running in mock mode - no Raspberry Pi RFID hardware detected")

class MockMFRC522:
    """Mock MFRC522 RFID reader implementation for non-Raspberry Pi systems."""
    
    # Command definitions
    PICC_REQIDL = 0x26
    PICC_REQALL = 0x52
    PICC_ANTICOLL = 0x93
    PICC_SELECTTAG = 0x93
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ = 0x30
    PICC_WRITE = 0xA0
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE = 0xC2
    PICC_TRANSFER = 0xB0
    PICC_HALT = 0x50
    
    def __init__(self, spd: int = 1000000) -> None:
        """Initialize the mock RFID reader."""
        self.spd = spd
        self._last_read_time = 0
        self._read_cooldown = 1.0  # seconds
        # Get list of authorized UIDs for random selection
        self._authorized_uids = list(AUTHORIZED_CARDS.keys())
        logger.info("Mock MFRC522 initialized")
        
    def MFRC522_Request(self, reqMode: int) -> Tuple[int, int]:
        """Mock tag request."""
        return RFIDStatus.OK, 0x10
        
    def MFRC522_Anticoll(self) -> Tuple[int, List[int]]:
        """Mock anti-collision detection."""
        # Simulate random card detection
        if random.random() < 0.3:  # 30% chance of detecting a card
            # 70% chance of detecting an authorized card, 30% chance of random card
            if random.random() < 0.8:
                # Select a random authorized card
                uid = list(random.choice(self._authorized_uids))
                logger.debug("Mock detected authorized card: %s", uid)
                return RFIDStatus.OK, uid
            else:
                # Generate a random unauthorized UID
                uid = [random.randint(0, 255) for _ in range(5)]
                logger.debug("Mock detected unauthorized card: %s", uid)
                return RFIDStatus.OK, uid
        return RFIDStatus.NO_TAG, []
        
    def MFRC522_SelectTag(self, serNum: List[int]) -> int:
        """Mock tag selection."""
        return 0x08
        
    def MFRC522_Auth(self, authMode: int, blockAddr: int, sectorKey: List[int], serNum: List[int]) -> int:
        """Mock authentication."""
        return RFIDStatus.OK
        
    def MFRC522_Read(self, blockAddr: int) -> None:
        """Mock read operation."""
        logger.debug("Mock read from block %d", blockAddr)
        
    def MFRC522_Write(self, blockAddr: int, writeData: List[int]) -> None:
        """Mock write operation."""
        logger.debug("Mock write to block %d", blockAddr)
        
    def MFRC522_Init(self) -> None:
        """Mock initialization."""
        logger.debug("Mock MFRC522 initialization")
        
    def GPIO_CLEAN(self) -> None:
        """Mock GPIO cleanup."""
        pass

class MFRC522:
    """MFRC522 RFID reader implementation for Raspberry Pi."""

    # Pin configuration
    NRSTPD = 22
    MAX_LEN = 16

    # Register definitions
    CommandReg = 0x01
    CommIEnReg = 0x02
    CommIrqReg = 0x04
    ErrorReg = 0x06
    Status1Reg = 0x08
    Status2Reg = 0x09
    FIFODataReg = 0x0A
    FIFOLevelReg = 0x0B
    WaterLevelReg = 0x0C
    ControlReg = 0x0D
    BitFramingReg = 0x0E
    CollReg = 0x0F
    ModeReg = 0x11
    TxModeReg = 0x12
    RxModeReg = 0x13
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TxSelReg = 0x16
    RxSelReg = 0x17
    RxThresholdReg = 0x18
    DemodReg = 0x19
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegL = 0x2C
    TReloadRegH = 0x2D
    TxASKReg = 0x2E
    TxSelReg = 0x2F
    CRCResultRegM = 0x21
    CRCResultRegL = 0x22
    ModWidthReg = 0x24
    RFCfgReg = 0x26
    GsNReg = 0x27
    CWGsCfgReg = 0x28
    ModGsCfgReg = 0x29
    DivIrqReg = 0x05

    # Command definitions
    PCD_IDLE = 0x00
    PCD_AUTHENT = 0x0E
    PCD_RECEIVE = 0x08
    PCD_TRANSMIT = 0x04
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC = 0x03

    # PICC commands
    PICC_REQIDL = 0x26
    PICC_REQALL = 0x52
    PICC_ANTICOLL = 0x93
    PICC_SELECTTAG = 0x93
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ = 0x30
    PICC_WRITE = 0xA0
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE = 0xC2
    PICC_TRANSFER = 0xB0
    PICC_HALT = 0x50

    def __init__(self, spd: int = 1000000) -> None:
        """Initialize the MFRC522 RFID reader."""
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = spd
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.NRSTPD, GPIO.OUT)
            GPIO.output(self.NRSTPD, 1)
            self.MFRC522_Init()
            logger.info("MFRC522 initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize MFRC522: %s", e)
            self.GPIO_CLEAN()
            raise

    def MFRC522_Reset(self) -> None:
        """Reset the MFRC522 RFID reader."""
        self.Write_MFRC522(self.CommandReg, self.PCD_RESETPHASE)

    def Write_MFRC522(self, addr: int, val: int) -> None:
        """Write a value to a register on the MFRC522."""
        self.spi.xfer2([(addr << 1) & 0x7E, val])

    def Read_MFRC522(self, addr: int) -> int:
        """Read a value from a register on the MFRC522."""
        val = self.spi.xfer2([((addr << 1) & 0x7E) | 0x80, 0])
        return val[1]

    def SetBitMask(self, reg: int, mask: int) -> None:
        """Set bits in a register on the MFRC522."""
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp | mask)

    def ClearBitMask(self, reg: int, mask: int) -> None:
        """Clear bits in a register on the MFRC522."""
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp & (~mask))

    def AntennaOn(self) -> None:
        """Turn the antenna on."""
        temp = self.Read_MFRC522(self.TxControlReg)
        if ~(temp & 0x03):
            self.SetBitMask(self.TxControlReg, 0x03)

    def AntennaOff(self) -> None:
        """Turn the antenna off."""
        self.ClearBitMask(self.TxControlReg, 0x03)

    def MFRC522_ToCard(self, command: int, sendData: List[int]) -> Tuple[int, List[int], int]:
        """Communicate with a card."""
        backData = []
        backLen = 0
        status = RFIDStatus.ERROR
        irqEn = 0x00
        waitIRq = 0x00

        if command == self.PCD_AUTHENT:
            irqEn = 0x12
            waitIRq = 0x10
        elif command == self.PCD_TRANSCEIVE:
            irqEn = 0x77
            waitIRq = 0x30

        self.Write_MFRC522(self.CommIEnReg, irqEn | 0x80)
        self.ClearBitMask(self.CommIrqReg, 0x80)
        self.SetBitMask(self.FIFOLevelReg, 0x80)
        self.Write_MFRC522(self.CommandReg, self.PCD_IDLE)

        for data in sendData:
            self.Write_MFRC522(self.FIFODataReg, data)

        self.Write_MFRC522(self.CommandReg, command)

        if command == self.PCD_TRANSCEIVE:
            self.SetBitMask(self.BitFramingReg, 0x80)

        i = 2000
        while i:
            n = self.Read_MFRC522(self.CommIrqReg)
            i -= 1
            if n & 0x01 or n & waitIRq:
                break

        self.ClearBitMask(self.BitFramingReg, 0x80)

        if i:
            if not (self.Read_MFRC522(self.ErrorReg) & 0x1B):
                status = RFIDStatus.OK
                if n & irqEn & 0x01:
                    status = RFIDStatus.NO_TAG

                if command == self.PCD_TRANSCEIVE:
                    n = self.Read_MFRC522(self.FIFOLevelReg)
                    lastBits = self.Read_MFRC522(self.ControlReg) & 0x07
                    backLen = (n - 1) * 8 + lastBits if lastBits else n * 8
                    n = min(n, self.MAX_LEN)

                    for _ in range(n):
                        backData.append(self.Read_MFRC522(self.FIFODataReg))
            else:
                status = RFIDStatus.ERROR

        return status, backData, backLen

    def MFRC522_Request(self, reqMode: int) -> Tuple[int, int]:
        """Request a tag."""
        self.Write_MFRC522(self.BitFramingReg, 0x07)
        status, backData, backBits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [reqMode])

        if status != RFIDStatus.OK or backBits != 0x10:
            status = RFIDStatus.ERROR

        return status, backBits

    def MFRC522_Anticoll(self) -> Tuple[int, List[int]]:
        """Anti-collision detection."""
        self.Write_MFRC522(self.BitFramingReg, 0x00)
        status, backData, backBits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [self.PICC_ANTICOLL, 0x20])

        if status == RFIDStatus.OK and len(backData) == 5:
            serNumCheck = 0
            for i in range(4):
                serNumCheck ^= backData[i]
            if serNumCheck != backData[4]:
                status = RFIDStatus.ERROR

        return status, backData

    def CalculateCRC(self, data: List[int]) -> List[int]:
        """Calculate CRC."""
        self.ClearBitMask(self.DivIrqReg, 0x04)
        self.SetBitMask(self.FIFOLevelReg, 0x80)

        for byte in data:
            self.Write_MFRC522(self.FIFODataReg, byte)

        self.Write_MFRC522(self.CommandReg, self.PCD_CALCCRC)

        for _ in range(0xFF):
            n = self.Read_MFRC522(self.DivIrqReg)
            if n & 0x04:
                break

        return [self.Read_MFRC522(self.CRCResultRegL), self.Read_MFRC522(self.CRCResultRegM)]

    def MFRC522_SelectTag(self, serNum: List[int]) -> int:
        """Select a tag."""
        buf = [self.PICC_SELECTTAG, 0x70] + serNum
        buf += self.CalculateCRC(buf)
        status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)

        if status == RFIDStatus.OK and backLen == 0x18:
            logger.info("Size: %s", backData[0])
            return backData[0]
        return 0

    def MFRC522_Auth(self, authMode: int, blockAddr: int, sectorKey: List[int], serNum: List[int]) -> int:
        """Authenticate a tag."""
        buff = [authMode, blockAddr] + sectorKey + serNum
        status, backData, backLen = self.MFRC522_ToCard(self.PCD_AUTHENT, buff)

        if status != RFIDStatus.OK or not (self.Read_MFRC522(self.Status2Reg) & 0x08):
            logger.error("AUTH ERROR!!")

        return status

    def MFRC522_Read(self, blockAddr: int) -> None:
        """Read data from a block."""
        recvData = [self.PICC_READ, blockAddr] + self.CalculateCRC([self.PICC_READ, blockAddr])
        status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, recvData)

        if status == RFIDStatus.OK and len(backData) == 16:
            logger.info("Sector %s %s", blockAddr, backData)
        else:
            logger.error("Error while reading!")

    def MFRC522_Write(self, blockAddr: int, writeData: List[int]) -> None:
        """Write data to a block."""
        buff = [self.PICC_WRITE, blockAddr] + self.CalculateCRC([self.PICC_WRITE, blockAddr])
        status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buff)

        if status == RFIDStatus.OK and backLen == 4 and (backData[0] & 0x0F) == 0x0A:
            buf = writeData + self.CalculateCRC(writeData)
            status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
            if status == RFIDStatus.OK and backLen == 4 and (backData[0] & 0x0F) == 0x0A:
                logger.info("Data written")
            else:
                logger.error("Error while writing")
        else:
            logger.error("Error while writing")

    def MFRC522_Init(self) -> None:
        """Initialize the MFRC522 RFID reader."""
        GPIO.output(self.NRSTPD, 1)
        self.MFRC522_Reset()

        self.Write_MFRC522(self.TModeReg, 0x8D)
        self.Write_MFRC522(self.TPrescalerReg, 0x3E)
        self.Write_MFRC522(self.TReloadRegL, 30)
        self.Write_MFRC522(self.TReloadRegH, 0)

        self.Write_MFRC522(self.TxAutoReg, 0x40)
        self.Write_MFRC522(self.ModeReg, 0x3D)
        self.AntennaOn()

    def GPIO_CLEAN(self) -> None:
        """Clean up GPIO."""
        GPIO.cleanup()

class RFIDReader:
    """High-level interface for RFID operations."""

    def __init__(self, spd: int = 1000000) -> None:
        """Initialize the RFID reader."""
        if IS_RASPBERRY_PI:
            self.rfid = MFRC522(spd)
        else:
            self.rfid = MockMFRC522(spd)

    def read_card(self) -> Tuple[int, List[int]]:
        """Read the ID of an RFID card."""
        try:
            status, tag_type = self.rfid.MFRC522_Request(self.rfid.PICC_REQIDL)
            if status == RFIDStatus.OK:
                status, uid = self.rfid.MFRC522_Anticoll()
                if status == RFIDStatus.OK:
                    return status, uid
            return status, []
        except Exception as e:
            logger.error("Error reading card: %s", e)
            return RFIDStatus.ERROR, []

    def authenticate_card(self, uid: List[int]) -> Tuple[int, Optional[str]]:
        """Authenticate an RFID card based on its UID."""
        try:
            if len(uid) != 5:
                logger.warning("Invalid UID length: %d", len(uid))
                return RFIDStatus.ERROR, None

            card_uid_tuple: Tuple[int, int, int, int, int] = (uid[0], uid[1], uid[2], uid[3], uid[4])
            card_info = AUTHORIZED_CARDS.get(card_uid_tuple)

            if card_info:
                logger.info("Card authenticated: %s (%s)", card_info.name, card_info.role)
                return RFIDStatus.OK, card_info.role

            logger.warning("Unauthorized card detected")
            return RFIDStatus.ERROR, None
        except Exception as e:
            logger.error("Error authenticating card: %s", e)
            return RFIDStatus.ERROR, None

    def read_card_data(self, block_addr: int) -> bool:
        """Read data from a block on the RFID card."""
        try:
            self.rfid.MFRC522_Read(block_addr)
            return True
        except Exception as e:
            logger.error("Error reading card data: %s", e)
            return False

    def write_card_data(self, block_addr: int, data: List[int]) -> bool:
        """Write data to a block on the RFID card."""
        try:
            self.rfid.MFRC522_Write(block_addr, data)
            return True
        except Exception as e:
            logger.error("Error writing card data: %s", e)
            return False

    def cleanup(self) -> None:
        """Clean up the GPIO pins."""
        try:
            self.rfid.GPIO_CLEAN()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error("Error during GPIO cleanup: %s", e)

if __name__ == "__main__":
    rfid_reader = RFIDReader()
    try:
        while True:
            status, uid = rfid_reader.read_card()
            if status == RFIDStatus.OK:
                logger.info("Card detected: %s", uid)
                status, role = rfid_reader.authenticate_card(uid)
                if status == RFIDStatus.OK:
                    logger.info("Authenticated as: %s", role)
                else:
                    logger.error("Authentication failed")
            time.sleep(1)
    except KeyboardInterrupt:
        rfid_reader.cleanup()
        logger.info("Exiting...")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        rfid_reader.cleanup()
