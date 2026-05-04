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
            List of individual HL7 messages as bytes (including MLLP framing)
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
                
            # Extract the message (including MLLP framing: STX ... ETX CR)
            # Check if CR follows ETX, include it if present
            if end_pos + 1 < len(file_content) and file_content[end_pos + 1:end_pos + 2] == cls.MLLP_SUFFIX:
                message = file_content[start_pos:end_pos + 2]  # Include ETX and CR
            else:
                message = file_content[start_pos:end_pos + 1]  # Include ETX only
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
        
        # Remove MLLP end (ETX) and suffix (CR) if present
        # They may appear as ETX+CR together, or just ETX, or just CR
        if message.endswith(cls.MLLP_END + cls.MLLP_SUFFIX):
            message = message[:-2]
        elif message.endswith(cls.MLLP_END):
            message = message[:-1]
        elif message.endswith(cls.MLLP_SUFFIX):
            message = message[:-1]
        
        return message
    
    @classmethod
    def process_batch(cls, file_content: bytes) -> List[bytes]:
        """
        Process a batch file: split, filter heartbeats, and parse messages.
        
        Detects format automatically:
        - If MLLP framing (STX/ETX) found → use split_batch()
        - Otherwise, treat as plain HL7 and split by MSH segments
        
        Args:
            file_content: Raw bytes content of the batch file
            
        Returns:
            List of clean HL7 messages (without MLLP framing) as bytes
        """
        messages = cls.split_batch(file_content)
        
        # If no MLLP-framed messages found, try plain HL7 format
        if not messages:
            messages = cls._split_plain_hl7(file_content)
        
        clean_messages = []
        
        for message in messages:
            # Parse to remove MLLP framing (if any)
            clean_msg = cls.parse_message(message)
            
            # Convert to string for heartbeat detection
            try:
                msg_str = clean_msg.decode('utf-8', errors='ignore')
            except Exception:
                # If decoding fails, skip this message
                continue
            
            # Check for heartbeat: MSH-8 or MSH-9 (index 7 or 8 when split by '|') 
            # contains "ZHB^H00" or "HEARTBEAT" 
            parts = msg_str.split('|')
            if len(parts) > 8:
                msh_9 = parts[8]
                msh_8 = parts[7] if len(parts) > 7 else ""
                if "ZHB" in msh_9 or "ZHB" in msh_8 or "HEARTBEAT" in msh_9 or "HEARTBEAT" in msh_8:
                    logger.debug(f"Ignoring heartbeat message: {msh_9} / {msh_8}")
                    continue
            
            clean_messages.append(clean_msg)
        
        logger.info(f"Processed batch: {len(messages)} total messages, "
                   f"{len(clean_messages)} valid after filtering")
        return clean_messages

    @classmethod
    def _split_plain_hl7(cls, file_content: bytes) -> List[bytes]:
        """
        Split plain HL7 text by ORU^R01 patient boundaries, filtering ZHB heartbeats.
        
        Each patient structure: MSH|ORU^R01 -> PID -> OBR -> OBX (params) -> OBX|ED (images)
        ZHB heartbeats have MSH-9 = "ZHB^H00" and contain no OBX segments.
        These must be filtered out before splitting.
        
        Args:
            file_content: Raw bytes content of plain HL7 messages
            
        Returns:
            List of individual HL7 messages as bytes (without any framing)
        """
        import re
        if not file_content:
            return []

        # Quick check: if there's only one or zero MSH segments, treat as a single message
        # This prevents modification of single messages by the normalization below.
        if file_content.count(b'MSH|') <= 1:
            if b'MSH|' in file_content:
                return [file_content]
            else:
                return []
        
        # Normalize line endings to \n for consistent parsing
        content = file_content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        content_str = content.decode('utf-8', errors='replace')
        
        # Remove ZHB heartbeat messages (they have no patient data)
        # Pattern matches: line starting with MSH|^~\&|HEARTBEAT|...|ZHB^H00|...
        # Use DOTALL to match across lines until next MSH or end of content
        zhb_pattern = r'(^|\n)MSH\|\^~\\&\|HEARTBEAT\|.*?ZHB\^H00\|.*?(?=\nMSH|$)'
        content_str = re.sub(zhb_pattern, '', content_str, flags=re.MULTILINE | re.DOTALL)
        
        # Split by MSH segments that contain ORU^R01 (real patient messages)
        # Lookahead pattern: split before each MSH line that starts a patient message
        split_pattern = r'(?=^MSH\|\^~\\&\|.*?\|ORU\^R01\|)'
        raw_messages = re.split(split_pattern, content_str, flags=re.MULTILINE)
        
        # Filter: keep only non-empty ORU^R01 messages (skip any remaining non-patient content)
        messages = []
        for msg in raw_messages:

            if not msg:
                continue
            # Verify this is an ORU^R01 patient message (not ZHB or other non-patient)
            if 'ORU^R01' in msg and 'ZHB^H00' not in msg:
                messages.append(msg)
        
        logger.info(f"Split plain HL7 batch into {len(messages)} patients (filtered ZHB heartbeats)")
        return [msg.encode('utf-8') for msg in messages]
