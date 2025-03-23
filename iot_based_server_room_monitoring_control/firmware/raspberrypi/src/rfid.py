#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
rfid.py

This module interfaces with an RFID reader connected to the Raspberry Pi.
It provides functions to initialize the reader, read and write data to RFID tags,
and handle authentication and communication with the tags.

Dependencies:
    - RPi.GPIO library (install with `pip install RPi.GPIO`)
    - spidev library (install with `pip install spidev`)
"""

import RPi.GPIO as GPIO
import spidev
import logging
import time
from typing import List, Tuple, Dict

logging.basicConfig(level=logging.INFO)

AUTHORIZED_CARDS: Dict[Tuple[int, int, int, int, int], Dict[str, str]] = {
        (5, 74, 28, 185, 234): {"name": "Card A", "role": "admin"},
        (83, 164, 247, 164, 164): {"name": "Card B", "role": "IT staff"},
        (20, 38, 121, 207, 132): {"name": "Card C", "role": "maintenance"}
}

class MFRC522:
        NRSTPD = 22
        MAX_LEN = 16

        PCD_IDLE = 0x00
        PCD_AUTHENT = 0x0E
        PCD_RECEIVE = 0x08
        PCD_TRANSMIT = 0x04
        PCD_TRANSCEIVE = 0x0C
        PCD_RESETPHASE = 0x0F
        PCD_CALCCRC = 0x03

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

        MI_OK = 0
        MI_NOTAGERR = 1
        MI_ERR = 2

        def __init__(self, spd: int = 1000000):
                """
                Initialize the MFRC522 RFID reader.
                """
                try:
                        self.spi = spidev.SpiDev()
                        self.spi.open(0, 0)
                        self.spi.max_speed_hz = spd
                        GPIO.setmode(GPIO.BOARD)
                        GPIO.setup(self.NRSTPD, GPIO.OUT)
                        GPIO.output(self.NRSTPD, 1)
                        self.MFRC522_Init()
                except Exception as e:
                        logging.error("Failed to initialize MFRC522: %s", e)
                        self.GPIO_CLEAN()

        def MFRC522_Reset(self) -> None:
                """
                Reset the MFRC522 RFID reader.
                """
                self.Write_MFRC522(self.CommandReg, self.PCD_RESETPHASE)

        def Write_MFRC522(self, addr: int, val: int) -> None:
                """
                Write a value to a register on the MFRC522.
                """
                self.spi.xfer2([(addr << 1) & 0x7E, val])

        def Read_MFRC522(self, addr: int) -> int:
                """
                Read a value from a register on the MFRC522.
                """
                val = self.spi.xfer2([((addr << 1) & 0x7E) | 0x80, 0])
                return val[1]

        def SetBitMask(self, reg: int, mask: int) -> None:
                """
                Set bits in a register on the MFRC522.
                """
                tmp = self.Read_MFRC522(reg)
                self.Write_MFRC522(reg, tmp | mask)

        def ClearBitMask(self, reg: int, mask: int) -> None:
                """
                Clear bits in a register on the MFRC522.
                """
                tmp = self.Read_MFRC522(reg)
                self.Write_MFRC522(reg, tmp & (~mask))

        def AntennaOn(self) -> None:
                """
                Turn the antenna on.
                """
                temp = self.Read_MFRC522(self.TxControlReg)
                if ~(temp & 0x03):
                        self.SetBitMask(self.TxControlReg, 0x03)

        def AntennaOff(self) -> None:
                """
                Turn the antenna off.
                """
                self.ClearBitMask(self.TxControlReg, 0x03)

        def MFRC522_ToCard(self, command: int, sendData: List[int]) -> Tuple[int, List[int], int]:
                """
                Communicate with a card.
                """
                backData = []
                backLen = 0
                status = self.MI_ERR
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
                                status = self.MI_OK
                                if n & irqEn & 0x01:
                                        status = self.MI_NOTAGERR

                                if command == self.PCD_TRANSCEIVE:
                                        n = self.Read_MFRC522(self.FIFOLevelReg)
                                        lastBits = self.Read_MFRC522(self.ControlReg) & 0x07
                                        backLen = (n - 1) * 8 + lastBits if lastBits else n * 8
                                        n = min(n, self.MAX_LEN)

                                        for _ in range(n):
                                                backData.append(self.Read_MFRC522(self.FIFODataReg))
                        else:
                                status = self.MI_ERR

                return status, backData, backLen

        def MFRC522_Request(self, reqMode: int) -> Tuple[int, int]:
                """
                Request a tag.
                """
                self.Write_MFRC522(self.BitFramingReg, 0x07)
                status, backData, backBits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [reqMode])

                if status != self.MI_OK or backBits != 0x10:
                        status = self.MI_ERR

                return status, backBits

        def MFRC522_Anticoll(self) -> Tuple[int, List[int]]:
                """
                Anti-collision detection.
                """
                self.Write_MFRC522(self.BitFramingReg, 0x00)
                status, backData, backBits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [self.PICC_ANTICOLL, 0x20])

                if status == self.MI_OK and len(backData) == 5:
                        serNumCheck = 0
                        for i in range(4):
                                serNumCheck ^= backData[i]
                        if serNumCheck != backData[4]:
                                status = self.MI_ERR

                return status, backData

        def CalculateCRC(self, data: List[int]) -> List[int]:
                """
                Calculate CRC.
                """
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
                """
                Select a tag.
                """
                buf = [self.PICC_SELECTTAG, 0x70] + serNum
                buf += self.CalculateCRC(buf)
                status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)

                if status == self.MI_OK and backLen == 0x18:
                        logging.info("Size: %s", backData[0])
                        return backData[0]
                return 0

        def MFRC522_Auth(self, authMode: int, blockAddr: int, sectorKey: List[int], serNum: List[int]) -> int:
                """
                Authenticate a tag.
                """
                buff = [authMode, blockAddr] + sectorKey + serNum
                status, backData, backLen = self.MFRC522_ToCard(self.PCD_AUTHENT, buff)

                if status != self.MI_OK or not (self.Read_MFRC522(self.Status2Reg) & 0x08):
                        logging.error("AUTH ERROR!!")

                return status

        def MFRC522_Read(self, blockAddr: int) -> None:
                """
                Read data from a block.
                """
                recvData = [self.PICC_READ, blockAddr] + self.CalculateCRC([self.PICC_READ, blockAddr])
                status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, recvData)

                if status == self.MI_OK and len(backData) == 16:
                        logging.info("Sector %s %s", blockAddr, backData)
                else:
                        logging.error("Error while reading!")

        def MFRC522_Write(self, blockAddr: int, writeData: List[int]) -> None:
                """
                Write data to a block.
                """
                buff = [self.PICC_WRITE, blockAddr] + self.CalculateCRC([self.PICC_WRITE, blockAddr])
                status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buff)

                if status == self.MI_OK and backLen == 4 and (backData[0] & 0x0F) == 0x0A:
                        buf = writeData + self.CalculateCRC(writeData)
                        status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
                        if status == self.MI_OK and backLen == 4 and (backData[0] & 0x0F) == 0x0A:
                                logging.info("Data written")
                        else:
                                logging.error("Error while writing")
                else:
                        logging.error("Error while writing")

        def MFRC522_Init(self) -> None:
                """
                Initialize the MFRC522 RFID reader.
                """
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
                """
                Clean up GPIO.
                """
                GPIO.cleanup()


class RFIDReader:
        def __init__(self, spd: int = 1000000):
                self.rfid = MFRC522(spd)

        def read_card(self) -> Tuple[int, List[int]]:
                """
                Read the ID of an RFID card.
                """
                status, tag_type = self.rfid.MFRC522_Request(self.rfid.PICC_REQIDL)
                if status == self.rfid.MI_OK:
                        status, uid = self.rfid.MFRC522_Anticoll()
                        if status == self.rfid.MI_OK:
                                return status, uid
                return status, []
        
        def authenticate_card(self, uid: List[int]) -> Tuple[int, str]:
                """
                Authenticate an RFID card based on its UID.
                """
                card_uid_tuple = tuple(uid)
                card_info = AUTHORIZED_CARDS.get(card_uid_tuple)
                if card_info:
                        return self.rfid.MI_OK, card_info["role"]
                return self.rfid.MI_ERR, ""

        def read_card_data(self, block_addr: int) -> None:
                """
                Read data from a block on the RFID card.
                """
                self.rfid.MFRC522_Read(block_addr)

        def write_card_data(self, block_addr: int, data: List[int]) -> None:
                """
                Write data to a block on the RFID card.
                """
                self.rfid.MFRC522_Write(block_addr, data)

        def cleanup(self) -> None:
                """
                Clean up the GPIO pins.
                """
                self.rfid.GPIO_CLEAN()

if __name__ == "__main__":
        rfid_reader = RFIDReader()
        try:
                while True:
                        status, uid = rfid_reader.read_card()
                        if status == rfid_reader.rfid.MI_OK:
                                logging.info("Card detected: %s", uid)
                                status, role = rfid_reader.authenticate_card(uid)
                                if status == rfid_reader.rfid.MI_OK:
                                        logging.info("Authenticated as: %s", role)
                                else:
                                        logging.error("Authentication failed")
                        time.sleep(1)
        except KeyboardInterrupt:
                rfid_reader.cleanup()
                logging.info("Exiting...")
