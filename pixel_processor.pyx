# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True

import numpy as np
cimport numpy as np
cimport cython

def process_pixels(unsigned char[:, :, :] image_array,
                  const unsigned char[:] blue_channel,
                  const unsigned char[:] green_channel,
                  const unsigned char[:] red_channel,
                  int width,
                  int block_y,
                  int max_y,
                  int channel_count):
    cdef:
        int x, y, c, idx
        int block_y_shift
        unsigned char b, g, r
        unsigned short[4] prev_pixel
        unsigned short value
    
    for y in range(block_y, max_y):
        block_y_shift = (y - block_y) * width
        for i in range(4):
            prev_pixel[i] = 0

        for x in range(width):
            idx = block_y_shift + x
            
            # Get pixel data and apply filters
            b = (blue_channel[idx] + green_channel[idx]) & 0xFF
            g = green_channel[idx]
            r = (red_channel[idx] + g) & 0xFF
            
            # Store in RGB order (not BGR)
            prev_pixel[0] = (prev_pixel[0] + r) & 0xFF  # R
            prev_pixel[1] = (prev_pixel[1] + g) & 0xFF  # G
            prev_pixel[2] = (prev_pixel[2] + b) & 0xFF  # B
            
            for c in range(channel_count):
                value = prev_pixel[c]
                if y > 0:
                    value = (value + image_array[y-1, x, c]) & 0xFF
                image_array[y, x, c] = value
            
            image_array[y, x, 3] = 255