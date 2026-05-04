from pathlib import Path
from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto, FileDescriptorProto

BINARY = Path(r"C:\Users\amine\AppData\Local\Programs\Windsurf\resources\app\extensions\windsurf\bin\language_server_windows_x64.exe")
NEEDLES = [b"exa/api_server_pb/api_server.proto", b"api_server.proto"]


def read_varint_reverse(data: bytes, end: int, max_back: int = 10):
    for start in range(max(0, end - max_back), end):
        value = 0
        shift = 0
        pos = start
        while pos < end:
            byte = data[pos]
            value |= (byte & 0x7F) << shift
            shift += 7
            pos += 1
            if byte < 0x80:
                if pos == end:
                    return start, value
                break
    return None


def candidate_descriptors(data: bytes, needle_offset: int):
    # FileDescriptorProto starts with field 1 (name): tag 0x0a, then len, then filename.
    starts = []
    for tag_offset in range(max(0, needle_offset - 20), needle_offset):
        if data[tag_offset] != 0x0A:
            continue
        parsed = read_varint_reverse(data, needle_offset)
        # Simpler: parse forward from tag_offset + 1.
        value = 0
        shift = 0
        pos = tag_offset + 1
        while pos < needle_offset and shift < 64:
            byte = data[pos]
            value |= (byte & 0x7F) << shift
            shift += 7
            pos += 1
            if byte < 0x80:
                break
        if pos == needle_offset and value == len(data[needle_offset:needle_offset + value]):
            starts.append(tag_offset)
        elif pos == needle_offset and data[needle_offset:needle_offset + value].endswith(b"api_server.proto"):
            starts.append(tag_offset)
    # Fallback: expected tag is usually immediately before varint length.
    for tag_offset in range(max(0, needle_offset - 5), needle_offset):
        if data[tag_offset] == 0x0A:
            starts.append(tag_offset)
    return sorted(set(starts))


def decode_from(data: bytes, start: int):
    # Try increasing slices until FileDescriptorProto parses and has the expected name.
    for length in range(2_000, 260_000, 2_000):
        chunk = data[start:start + length]
        fd = FileDescriptorProto()
        try:
            fd.ParseFromString(chunk)
        except Exception:
            continue
        if fd.name and "api_server" in fd.name and fd.message_type:
            return fd, length
    return None, None


def read_varint_forward(data: bytes, start: int, limit=None):
    value = 0
    shift = 0
    pos = start
    end = len(data) if limit is None else min(len(data), limit)
    while pos < end and shift < 64:
        byte = data[pos]
        value |= (byte & 0x7F) << shift
        pos += 1
        if byte < 0x80:
            return value, pos
        shift += 7
    return None


def find_embedded_message_start(data: bytes, name_offset: int, name: str):
    name_len = len(name.encode("utf-8"))
    for tag_offset in range(max(0, name_offset - 12), name_offset):
        if data[tag_offset] != 0x0A:
            continue
        parsed = read_varint_forward(data, tag_offset + 1, name_offset)
        if not parsed:
            continue
        length, payload_offset = parsed
        if payload_offset == name_offset and length == name_len:
            return tag_offset
    return None


def decode_descriptor_proto(data: bytes, name: str):
    encoded_name = name.encode("utf-8")
    search_start = 0
    best = None

    while True:
        name_offset = data.find(encoded_name, search_start)
        if name_offset < 0:
            return best
        search_start = name_offset + 1

        start = find_embedded_message_start(data, name_offset, name)
        if start is None:
            continue

        best_for_start = None
        for length in range(8, 8192):
            chunk = data[start : start + length]
            message = DescriptorProto()
            try:
                message.ParseFromString(chunk)
            except Exception:
                continue
            if message.name != name:
                continue
            if not all(field.name for field in message.field):
                continue
            if best_for_start is None or len(message.field) > len(best_for_start[2].field):
                best_for_start = (start, length, message)

        if best_for_start is not None:
            # Stop once we have a plausible descriptor at the first real type-name
            # occurrence. Later matches are usually method names or Go symbol names.
            return best_for_start


def summarize_message(message, indent=""):
    print(f"{indent}message {message.name}")
    for field in message.field:
        label = field.Label.Name(field.label).replace("LABEL_", "").lower()
        type_name = field.type_name or field.Type.Name(field.type).replace("TYPE_", "").lower()
        print(f"{indent}  {field.number}: {label} {type_name} {field.name} json={field.json_name}")
    for nested in message.nested_type:
        summarize_message(nested, indent + "  ")


def main():
    data = BINARY.read_bytes()
    print("message-descriptor scan")
    interesting_messages = [
        "AssignArenaModelRequest",
        "ArenaModelAssignment",
        "AssignArenaModelResponse",
        "AssignModelRequest",
        "ModelAssignment",
        "AssignModelResponse",
        "GetChatMessageRequest",
        "GetChatMessageResponse",
    ]
    for message_name in interesting_messages:
        decoded = decode_descriptor_proto(data, message_name)
        if decoded:
            start, length, message = decoded
            print(f"decoded DescriptorProto start={start} length={length}")
            summarize_message(message)
        else:
            print(f"message {message_name}: not decoded")

    print("file-descriptor scan")
    seen = set()
    for needle in NEEDLES:
        offset = data.find(needle)
        print(f"needle={needle.decode()} offset={offset}")
        while offset >= 0:
            for start in candidate_descriptors(data, offset):
                if start in seen:
                    continue
                seen.add(start)
                fd, length = decode_from(data, start)
                if not fd:
                    continue
                print(f"decoded_start={start} length_probe={length} name={fd.name} package={fd.package}")
                for dep in fd.dependency:
                    print(f"dependency {dep}")
                for service in fd.service:
                    print(f"service {service.name}")
                    for method in service.method:
                        print(f"  rpc {method.name} {method.input_type} -> {method.output_type} client_stream={method.client_streaming} server_stream={method.server_streaming}")
                interesting = {"AssignModelRequest", "AssignModelResponse", "ModelAssignment", "GetChatMessageRequest", "GetChatMessageResponse", "ArenaModelAssignment", "AssignArenaModelRequest", "AssignArenaModelResponse"}
                for message in fd.message_type:
                    if message.name in interesting:
                        summarize_message(message)
                return
            offset = data.find(needle, offset + 1)


if __name__ == "__main__":
    main()
