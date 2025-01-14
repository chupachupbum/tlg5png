class LzssDecompressor:
    def __init__(self):
        self.dictionary = bytearray(4096)
        self.offset = 0

    def init_dictionary(self, dictionary: bytes):
        for i in range(4096):
            self.dictionary[i] = dictionary[i]

    def decompress(self, input_data: bytes, output_size: int) -> bytes:
        output = bytearray(output_size)
        input_ptr = 0
        output_ptr = 0
        
        flags = 0
        while input_ptr < len(input_data):
            flags >>= 1
            if (flags & 0x100) != 0x100:
                if input_ptr >= len(input_data):
                    return bytes(output)
                flags = input_data[input_ptr] | 0xFF00
                input_ptr += 1

            if (flags & 1) == 1:
                if input_ptr + 1 >= len(input_data):
                    return bytes(output)
                
                x0 = input_data[input_ptr]
                x1 = input_data[input_ptr + 1]
                input_ptr += 2
                
                position = x0 | ((x1 & 0xF) << 8)
                size = 3 + ((x1 & 0xF0) >> 4)
                
                if size == 18:
                    if input_ptr >= len(input_data):
                        return bytes(output)
                    size += input_data[input_ptr]
                    input_ptr += 1

                for _ in range(size):
                    c = self.dictionary[position]
                    if output_ptr >= output_size:
                        return bytes(output)
                    
                    output[output_ptr] = c
                    output_ptr += 1
                    
                    self.dictionary[self.offset] = c
                    self.offset = (self.offset + 1) & 0xFFF
                    position = (position + 1) & 0xFFF
            else:
                if input_ptr >= len(input_data):
                    return bytes(output)
                
                c = input_data[input_ptr]
                input_ptr += 1
                
                if output_ptr >= output_size:
                    return bytes(output)
                
                output[output_ptr] = c
                output_ptr += 1
                
                self.dictionary[self.offset] = c
                self.offset = (self.offset + 1) & 0xFFF

        return bytes(output)