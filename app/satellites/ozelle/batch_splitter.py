"""
Batch splitter for HL7 files with MLLP framing.

This module handles splitting of HL7 batch files that contain MLLP-framed messages.
It ignores HEARTBEAT messages (MSH-9 = "ZHB^H00") and processes only valid HL7 messages.
"""

import logging
from typing import List, Tuple
import binascii

logger = logging.getLogger(__name__)


class BatchSplitter:
    """Handles splitting of HL7 batch files with MLLP framing."""
    
    MLLP_START = b'\x0b'  # Vertical Tab (VT) character
    MLLP_END = b'\x1c'      # File Separator (FS) character
    MLLP_SUFFIX = b'\x0d'   # Carriage Return (CR) character
    
    @classmethod
    def split_batch(cls, file_content: bytes) -> List[bytes]:
        """
        Split a batch file into individual HL7 messages.
        
        Args:
            file_content: Raw bytes content of the batch file
            
        Returns:
            List of individual HL7 messages as bytes
        """
        messages = []
        start_idx = 0
        
        while start_idx < len(file_content):
            # Look for MLLP start character
            start_pos = file_content.find(cls.MLLP_START, start_idx)
            if start_pos == -1:
                break
                
            # Look for MLLP end character after start
            end_pos = file_content.find(cls.MLLP_END, start_pos)
            if end_pos == -1:
                break
                
            # Extract the message (including MLLP framing)
            message = file_content[start_pos:end_pos + 1]
            messages.append(message)
            
            # Move past this message for next iteration
            start_idx = end_pos + 1
            
        return messages
    
    @classmethod
    def parse_message(cls, message: bytes) -> bytes:
        """
        Parse an individual MLLP-framed message, removing the framing characters.
        
        Args:
            message: MLLP-framed message as bytes
            
        Returns:
            Clean HL7 message as bytes
        """
        # Remove MLLP start character if present
        if message.startswith(cls.MLLP_START):
            message = message[1:]
            
        # Remove MLLP end character if present
        if message.endswith(cls.MLLP_END):
            message = message[:-1]
            
        # Remove MLLP suffix if present
        if message.endswith(cls.MLLP_SUFFIX):
            message = message[:-1]
            
        return message
    
    @classmethod
    def process_batch(cls, file_content: bytes) -> List[bytes]:
        """
        Process a batch file: split, filter heartbeats, and parse messages.
        
        Args:
            file_content: Raw bytes content of the batch file
            
        Returns:
            List of clean HL7 messages (without MLLP framing) as bytes
        """
        messages = cls.split_batch(file_content)
        clean_messages = []
        
        for message in messages:
            # Parse to remove MLLP framing
            clean_msg = cls.parse_message(message)
            
            # Convert to string for heartbeat detection
            try:
                msg_str = clean_msg.decode('utf-8', errors='ignore')
            except Exception:
                # If decoding fails, skip this message
                continue
            
            # Check for heartbeat: MSH-9 (index 8 when split by '|') 
            # contains "ZHB^H00" or "HEARTBEAT"
            parts = msg_str.split('|')
            if len(parts) > 8:
                msh_9 = parts[8]
                if "ZHB" in msh_9 or "HEARTBEAT" in msh_9:
                    logger.debug(f"Ignoring heartbeat message: {msh_9}")
                    continue
            
            clean_messages.append(clean_msg)
        
        logger.info(f"Processed batch: {len(messages)} total messages, "
                   f"{len(clean_messages)} valid after filtering")
        return clean_messages
