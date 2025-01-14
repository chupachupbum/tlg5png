import struct
from dataclasses import dataclass
from typing import List
from PIL import Image
import numpy as np
from lzss_decompressor import LzssDecompressor
from pixel_processor import process_pixels

@dataclass
class Header:
    channel_count: int
    image_width: int
    image_height: int
    block_height: int

class BlockInfo:
    def __init__(self, input_stream):
        self.mark = input_stream.read(1)[0] > 0
        self.block_size = struct.unpack('<I', input_stream.read(4))[0]
        self.data = input_stream.read(self.block_size)

    def decompress(self, decompressor, header):
        output_size = header.image_width * header.block_height
        self.data = decompressor.decompress(self.data, output_size)

class Tlg5Decoder:
    def __init__(self):
        # Pre-allocate buffers
        self.temp_buffer = bytearray(1024 * 1024)  # 1MB buffer
        self.decompressor = LzssDecompressor()

    def decode(self, file_path: str) -> Image.Image:
        with open(file_path, 'rb') as f:
            header = self._read_header(f)
            image_array = self._decode_image(f, header)
        return Image.fromarray(image_array, 'RGBA')

    def _read_header(self, f) -> Header:
        # Verify TLG0.0 header
        if f.read(7) != b'TLG0.0\0':
            raise ValueError("Invalid TLG file format (Expected TLG0.0)")
        
        # Skip metadata section
        if f.read(4) != b'sds\x1a':
            raise ValueError("Invalid metadata marker")
        metadata_size = struct.unpack('<I', f.read(4))[0]
        
        # Find TLG5.0 header
        while True:
            if f.read(1) == b'T':
                possible_header = b'T' + f.read(6)
                if possible_header == b'TLG5.0\0':
                    break
                f.seek(-6, 1)

        # Read raw marker
        raw_magic = f.read(4)
        if raw_magic != b'raw\x1a':
            raise ValueError(f"Invalid raw marker, got: {raw_magic}")

        # Read image information
        f.read(1)[0]  # Skip channel byte
        width = int.from_bytes(f.read(4), byteorder='little')
        height = int.from_bytes(f.read(4), byteorder='little')
        block_height = int.from_bytes(f.read(4), byteorder='little')

        return Header(
            channel_count=3,  # TLG5 always uses 3 channels (RGB)
            image_width=width,
            image_height=height,
            block_height=block_height
        )

    def _decode_image(self, f, header) -> np.ndarray:
        image_array = np.zeros((header.image_height, header.image_width, 4), dtype=np.uint8)
        
        # Skip block sizes
        block_count = (header.image_height - 1) // header.block_height + 1
        f.seek(4 * block_count, 1)

        decompressor = LzssDecompressor()
        
        # Process blocks
        for y in range(0, header.image_height, header.block_height):
            channel_data = []
            for _ in range(header.channel_count):
                block_info = BlockInfo(f)
                if not block_info.mark:
                    block_info.decompress(decompressor, header)
                channel_data.append(block_info)
            
            self._load_pixel_block_row(image_array, channel_data, header, y)

        return image_array

    def _load_pixel_block_row(self, image_array, channel_data, header, block_y):
        max_y = min(block_y + header.block_height, header.image_height)
        
        # Convert channel data to numpy arrays
        # Note: TLG stores in BGR order, but we process to RGB
        channel_arrays = [
            np.frombuffer(cd.data, dtype=np.uint8).copy()
            for cd in channel_data
        ]
        
        # Process pixels (B,G,R -> R,G,B)
        process_pixels(
            image_array, 
            channel_arrays[0],  # Blue channel
            channel_arrays[1],  # Green channel
            channel_arrays[2],  # Red channel
            header.image_width,
            block_y,
            max_y,
            header.channel_count
        )
        