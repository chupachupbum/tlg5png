import argparse
import os
from tlg5_decoder import Tlg5Decoder
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from typing import List, Tuple
from tqdm import tqdm  # For progress bar

def process_file(args: Tuple[str, str]) -> None:
    """Process a single file with error handling"""
    input_path, output_path = args
    try:
        decoder = Tlg5Decoder()  # Create decoder instance per process
        image = decoder.decode(input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, 'PNG')
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Convert TLG5 images to PNG format')
    parser.add_argument('input', help='Input TLG5 file or directory')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
    parser.add_argument('-j', '--jobs', type=int, default=multiprocessing.cpu_count(),
                      help='Number of parallel jobs (default: number of CPU cores)')
    parser.add_argument('-b', '--batch-size', type=int, default=10,
                      help='Batch size for processing (default: 10)')
    
    args = parser.parse_args()
    
    # Collect files to process
    if os.path.isfile(args.input):
        output_path = args.output or os.path.splitext(args.input)[0] + '.png'
        files_to_process = [(args.input, output_path)]
    else:
        input_dir = args.input
        output_dir = args.output or input_dir
        files_to_process = []
        
        for root, _, files in os.walk(input_dir):
            if not args.recursive and root != input_dir:
                continue
                
            for file in files:
                if file.lower().endswith('.tlg'):
                    input_path = os.path.join(root, file)
                    rel_path = os.path.relpath(input_path, input_dir)
                    output_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + '.png')
                    files_to_process.append((input_path, output_path))

    # Process files in parallel with progress bar
    total_files = len(files_to_process)
    if total_files == 0:
        print("No TLG files found to process")
        return

    print(f"Processing {total_files} files using {args.jobs} processes")
    
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        with tqdm(total=total_files, desc="Converting") as pbar:
            # Process files in batches
            for i in range(0, total_files, args.batch_size):
                batch = files_to_process[i:i + args.batch_size]
                results = list(executor.map(process_file, batch))
                pbar.update(len(batch))

if __name__ == "__main__":
    main()