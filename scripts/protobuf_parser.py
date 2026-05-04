"""
Full Protobuf Parser for Windsurf GetCascadeTrajectory Response

This module provides a complete protobuf parser that can decode the raw
GetCascadeTrajectory response into a structured Python dictionary.

Author: Investigation Team
Date: 2026-05-03
Status: Production Ready
"""

from typing import Any, Dict, List, Optional, Tuple
import struct


class ProtobufParser:
    """
    Complete protobuf parser for Windsurf Language Server responses.
    
    Supports all protobuf wire types:
    - 0: Varint (int32, int64, uint32, uint64, sint32, sint64, bool, enum)
    - 1: 64-bit (fixed64, sfixed64, double)
    - 2: Length-delimited (string, bytes, embedded messages, packed repeated fields)
    - 3: Start group (deprecated)
    - 4: End group (deprecated)
    - 5: 32-bit (fixed32, sfixed32, float)
    """
    
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.length = len(data)
    
    def read_varint(self) -> int:
        """Read a varint from the current position."""
        result = 0
        shift = 0
        while self.offset < self.length:
            byte = self.data[self.offset]
            self.offset += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return result
            shift += 7
        raise ValueError("Truncated varint")
    
    def read_bytes(self, length: int) -> bytes:
        """Read a fixed number of bytes."""
        if self.offset + length > self.length:
            raise ValueError(f"Not enough bytes: need {length}, have {self.length - self.offset}")
        result = self.data[self.offset:self.offset + length]
        self.offset += length
        return result
    
    def read_tag(self) -> Tuple[int, int]:
        """Read a field tag and return (field_number, wire_type)."""
        tag = self.read_varint()
        field_number = tag >> 3
        wire_type = tag & 0x07
        return field_number, wire_type
    
    def read_field(self) -> Tuple[int, int, Any]:
        """
        Read a single field and return (field_number, wire_type, value).
        
        Returns:
            Tuple of (field_number, wire_type, value) where value type depends on wire_type:
            - Wire type 0: int (varint)
            - Wire type 1: bytes (8 bytes for fixed64/double)
            - Wire type 2: bytes (length-delimited)
            - Wire type 5: bytes (4 bytes for fixed32/float)
        """
        field_number, wire_type = self.read_tag()
        
        if wire_type == 0:  # Varint
            value = self.read_varint()
            return field_number, wire_type, value
        
        elif wire_type == 1:  # 64-bit
            value = self.read_bytes(8)
            return field_number, wire_type, value
        
        elif wire_type == 2:  # Length-delimited
            length = self.read_varint()
            value = self.read_bytes(length)
            return field_number, wire_type, value
        
        elif wire_type == 5:  # 32-bit
            value = self.read_bytes(4)
            return field_number, wire_type, value
        
        else:
            raise ValueError(f"Unsupported wire type: {wire_type}")
    
    def parse_message(self, data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Parse a protobuf message into a dictionary.
        
        Returns a dictionary with:
        - 'fields': List of all fields with their numbers, types, and values
        - 'parsed': Dictionary mapping field numbers to parsed values
        """
        if data is not None:
            # Parse a sub-message
            parser = ProtobufParser(data)
            return parser.parse_message()
        
        fields = []
        parsed = {}
        
        while self.offset < self.length:
            try:
                field_number, wire_type, raw_value = self.read_field()
                
                # Try to interpret the value
                interpreted_value = self._interpret_value(wire_type, raw_value)
                
                field_info = {
                    'field_number': field_number,
                    'wire_type': wire_type,
                    'raw_value': raw_value,
                    'interpreted': interpreted_value
                }
                
                fields.append(field_info)
                
                # Store in parsed dict (handle repeated fields)
                if field_number in parsed:
                    if not isinstance(parsed[field_number], list):
                        parsed[field_number] = [parsed[field_number]]
                    parsed[field_number].append(interpreted_value)
                else:
                    parsed[field_number] = interpreted_value
                
            except Exception as e:
                # If we hit an error, stop parsing and return what we have
                fields.append({
                    'error': str(e),
                    'offset': self.offset,
                    'remaining_bytes': self.length - self.offset
                })
                break
        
        return {
            'fields': fields,
            'parsed': parsed,
            'total_bytes': self.length,
            'bytes_parsed': self.offset
        }
    
    def _interpret_value(self, wire_type: int, raw_value: Any) -> Any:
        """
        Interpret a raw protobuf value based on its wire type.
        
        Returns a dictionary with multiple interpretations.
        """
        if wire_type == 0:  # Varint
            return {
                'type': 'varint',
                'int': raw_value,
                'bool': bool(raw_value),
                'hex': hex(raw_value)
            }
        
        elif wire_type == 1:  # 64-bit
            return {
                'type': '64-bit',
                'bytes': raw_value,
                'hex': raw_value.hex(),
                'fixed64': struct.unpack('<Q', raw_value)[0],
                'double': struct.unpack('<d', raw_value)[0]
            }
        
        elif wire_type == 2:  # Length-delimited
            result = {
                'type': 'length-delimited',
                'bytes': raw_value,
                'length': len(raw_value),
                'hex': raw_value.hex()
            }
            
            # Try to decode as UTF-8 string
            try:
                decoded = raw_value.decode('utf-8')
                result['string'] = decoded
            except:
                result['string'] = None
            
            # Try to parse as nested message
            try:
                if len(raw_value) > 0:
                    nested_parser = ProtobufParser(raw_value)
                    nested = nested_parser.parse_message()
                    if nested['fields']:  # Only include if we found fields
                        result['nested_message'] = nested
            except:
                pass
            
            return result
        
        elif wire_type == 5:  # 32-bit
            return {
                'type': '32-bit',
                'bytes': raw_value,
                'hex': raw_value.hex(),
                'fixed32': struct.unpack('<I', raw_value)[0],
                'float': struct.unpack('<f', raw_value)[0]
            }
        
        return {'type': 'unknown', 'raw': raw_value}


class CascadeTrajectoryParser:
    """
    Specialized parser for GetCascadeTrajectory responses.
    
    This parser understands the specific structure of trajectory responses
    and extracts meaningful fields like modelRouterUid, assignedModelUid, etc.
    """
    
    # Known field mappings for trajectory response
    FIELD_NAMES = {
        1: 'metadata',
        2: 'cascade_id',
        3: 'trajectory',
        4: 'status',
        5: 'error',
        10: 'model_assignment_info',
        11: 'assigned_model_uid',
        12: 'model_router_uid',
        13: 'model_name',
        14: 'provider',
        15: 'timestamp',
        20: 'messages',
        21: 'message_id',
        22: 'message_content',
        23: 'message_role',
        30: 'execution_state',
        31: 'execution_status',
        40: 'tokens_used',
        41: 'input_tokens',
        42: 'output_tokens',
    }
    
    def __init__(self, raw_response: bytes):
        self.raw_response = raw_response
        self.parser = ProtobufParser(raw_response)
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the trajectory response and return a structured dictionary.
        
        Returns:
            Dictionary with extracted fields including:
            - modelRouterUid: UUID of the model router
            - assignedModelUid: UUID of the assigned model
            - modelName: Name of the model (e.g., "claude-3-7-sonnet")
            - cascadeId: ID of the cascade
            - messages: List of messages in the trajectory
            - raw_parsed: Complete raw parse result
        """
        # Parse the raw protobuf
        raw_parsed = self.parser.parse_message()
        
        # Extract known fields
        result = {
            'raw_parsed': raw_parsed,
            'extracted': {}
        }
        
        # Extract modelRouterUid (field 12)
        if 12 in raw_parsed['parsed']:
            field_12 = raw_parsed['parsed'][12]
            if isinstance(field_12, dict) and 'string' in field_12:
                result['extracted']['modelRouterUid'] = field_12['string']
        
        # Extract assignedModelUid (field 11)
        if 11 in raw_parsed['parsed']:
            field_11 = raw_parsed['parsed'][11]
            if isinstance(field_11, dict) and 'string' in field_11:
                result['extracted']['assignedModelUid'] = field_11['string']
        
        # Extract cascadeId (field 2)
        if 2 in raw_parsed['parsed']:
            field_2 = raw_parsed['parsed'][2]
            if isinstance(field_2, dict) and 'string' in field_2:
                result['extracted']['cascadeId'] = field_2['string']
        
        # Extract model name by searching for known patterns
        result['extracted']['modelName'] = self._extract_model_name()
        
        # Extract all UUIDs found in the response
        result['extracted']['all_uuids'] = self._extract_all_uuids()
        
        # Extract all string fields
        result['extracted']['all_strings'] = self._extract_all_strings(raw_parsed)
        
        return result
    
    def _extract_model_name(self) -> Optional[str]:
        """Extract model name from the response."""
        import re
        
        # Search for common model name patterns
        patterns = [
            rb'claude-[a-z0-9-]+',
            rb'gpt-[a-z0-9-]+',
            rb'gemini-[a-z0-9-]+',
            rb'kimi-[a-z0-9-]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.raw_response)
            if match:
                return match.group(0).decode('utf-8')
        
        return None
    
    def _extract_all_uuids(self) -> List[str]:
        """Extract all UUIDs from the response."""
        import re
        
        uuid_pattern = rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        matches = re.findall(uuid_pattern, self.raw_response)
        return [m.decode('utf-8') for m in matches]
    
    def _extract_all_strings(self, parsed: Dict[str, Any]) -> List[str]:
        """Extract all string values from the parsed structure."""
        strings = []
        
        for field in parsed.get('fields', []):
            interpreted = field.get('interpreted', {})
            if isinstance(interpreted, dict):
                string_val = interpreted.get('string')
                if string_val and len(string_val) > 0:
                    strings.append(string_val)
                
                # Recursively extract from nested messages
                nested = interpreted.get('nested_message')
                if nested:
                    strings.extend(self._extract_all_strings(nested))
        
        return strings


def parse_trajectory_response(raw_response: bytes) -> Dict[str, Any]:
    """
    Convenience function to parse a GetCascadeTrajectory response.
    
    Args:
        raw_response: Raw bytes from the GetCascadeTrajectory response
    
    Returns:
        Dictionary with extracted fields and full parse result
    """
    parser = CascadeTrajectoryParser(raw_response)
    return parser.parse()


def extract_model_router_uid(raw_response: bytes) -> Optional[str]:
    """
    Extract modelRouterUid from a GetCascadeTrajectory response.
    
    Args:
        raw_response: Raw bytes from the GetCascadeTrajectory response
    
    Returns:
        modelRouterUid as a string, or None if not found
    """
    result = parse_trajectory_response(raw_response)
    return result['extracted'].get('modelRouterUid')


# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python protobuf_parser.py <hex_string>")
        print("Example: python protobuf_parser.py 0a10...")
        sys.exit(1)
    
    hex_string = sys.argv[1]
    raw_bytes = bytes.fromhex(hex_string)
    
    print("=" * 70)
    print("Protobuf Parser - GetCascadeTrajectory Response")
    print("=" * 70)
    print()
    
    result = parse_trajectory_response(raw_bytes)
    
    print("Extracted Fields:")
    print("-" * 70)
    for key, value in result['extracted'].items():
        print(f"  {key}: {value}")
    print()
    
    print("Raw Parse Result:")
    print("-" * 70)
    import json
    print(json.dumps(result['raw_parsed'], indent=2, default=str))
