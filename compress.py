import numpy as np
import heapq
import os
from collections import defaultdict
import wave
import struct
import time
import soundfile as sf


class HuffmanNode:
    def __init__(self, value=None, freq=0, left=None, right=None):
        self.value = value
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq

def calculate_frequencies(audio_data):
    freq = defaultdict(int)
    for sample in audio_data:
        freq[sample] += 1
    return freq

def build_huffman_tree(frequencies):
    heap = []
    for value, freq in frequencies.items():
        node = HuffmanNode(value=value, freq=freq)
        heapq.heappush(heap, node)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heapq.heappop(heap)

def build_codebook(root, current_code="", codebook=None):
    if codebook is None:
        codebook = {}

    if root.value is not None:
        codebook[root.value] = current_code
        return codebook

    build_codebook(root.left, current_code + "0", codebook)
    build_codebook(root.right, current_code + "1", codebook)

    return codebook

def huffman_encode(audio_data, codebook):
    encoded_bits = ""
    for sample in audio_data:
        encoded_bits += codebook[sample]

    padding = (8 - len(encoded_bits) % 8) % 8
    encoded_bits += "0" * padding

    byte_array = bytearray()
    for i in range(0, len(encoded_bits), 8):
        byte = encoded_bits[i:i+8]
        byte_array.append(int(byte, 2))

    return bytes(byte_array), padding

def huffman_decode(encoded_data, padding, root):
    bit_string = ""
    for byte in encoded_data:
        bits = bin(byte)[2:].rjust(8, '0')
        bit_string += bits

    if padding != 0:
        bit_string = bit_string[:-padding]

    decoded_data = []
    current_node = root
    for bit in bit_string:
        current_node = current_node.left if bit == '0' else current_node.right
        if current_node.value is not None:
            decoded_data.append(current_node.value)
            current_node = root

    return decoded_data

def read_wav_file(filename):
    data, samplerate = sf.read(filename, dtype='int16')  
    if len(data.shape) > 1:  # stereo/multichannel
        data = data[:, 0]  # ambil channel pertama (mono)
    params = (1, 2, samplerate, len(data), 'NONE', 'not compressed')  
    return data.tolist(), params


def write_wav_file(filename, samples, params):
    with wave.open(filename, 'wb') as wav:
        wav.setparams(params)
        frames = struct.pack(f'<{len(samples)}h', *samples)
        wav.writeframes(frames)

def compress_audio(input_file, output_file):
    start_time = time.time()  # Catat waktu mulai kompresi

    audio_samples, params = read_wav_file(input_file)

    frequencies = calculate_frequencies(audio_samples)
    huffman_tree = build_huffman_tree(frequencies)
    codebook = build_codebook(huffman_tree)

    encoded_data, padding = huffman_encode(audio_samples, codebook)

    with open(output_file, 'wb') as f:
        f.write(bytes([padding]))
        f.write(len(codebook).to_bytes(2, byteorder='little'))
        for sample, code in codebook.items():
            f.write(sample.to_bytes(2, byteorder='little', signed=True))
            f.write(len(code).to_bytes(1, byteorder='little'))
            code_bytes = int(code, 2).to_bytes((len(code) + 7) // 8, byteorder='big')
            f.write(code_bytes)
        f.write(encoded_data)

    original_size = len(audio_samples) * 2
    compressed_size = os.path.getsize(output_file)
    compression_ratio = (1 - compressed_size / original_size) * 100

    end_time = time.time()  # Catat waktu selesai kompresi
    compression_time = end_time - start_time  # Hitung waktu kompresi

    print(f"Kompresi selesai. Rasio kompresi: {compression_ratio:.2f}%")
    print(f"Ukuran asli: {original_size} bytes")
    print(f"Ukuran terkompresi: {compressed_size} bytes")
    print(f"Waktu kompresi: {compression_time:.2f} detik") 

def decompress_audio(input_file, output_file):
    with open(input_file, 'rb') as f:
        padding = int.from_bytes(f.read(1), byteorder='little')
        codebook_size = int.from_bytes(f.read(2), byteorder='little')
        codebook = {}
        for _ in range(codebook_size):
            sample = int.from_bytes(f.read(2), byteorder='little', signed=True)
            code_length = int.from_bytes(f.read(1), byteorder='little')
            code_bytes = f.read((code_length + 7) // 8)
            code = bin(int.from_bytes(code_bytes, byteorder='big'))[2:].zfill(code_length)
            codebook[code] = sample

        encoded_data = f.read()

    reverse_codebook = {v: k for k, v in codebook.items()}
    root = HuffmanNode()
    for sample, code in reverse_codebook.items():
        node = root
        for bit in code:
            if bit == '0':
                if not node.left:
                    node.left = HuffmanNode()
                node = node.left
            else:
                if not node.right:
                    node.right = HuffmanNode()
                node = node.right
        node.value = sample

    decoded_samples = huffman_decode(encoded_data, padding, root)

    params = (1, 2, 44100, 0, 'NONE', 'not compressed') 
    write_wav_file(output_file, decoded_samples, params)

    print("Dekompresi selesai. File hasil dekompresi telah dibuat.")

if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"

    input_wav = os.path.join(input_dir, "yoo.wav")
    compressed_file = os.path.join(output_dir, "compressed.bin")
    output_wav = os.path.join(output_dir, "output3.wav")

   
    os.makedirs(output_dir, exist_ok=True)


    compress_audio(input_wav, compressed_file)


    decompress_audio(compressed_file, output_wav)