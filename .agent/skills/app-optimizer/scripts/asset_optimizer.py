import os
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Pillow is required. Run: pip install Pillow")
    sys.exit(1)

def optimize_images(directory, quality=80):
    """
    Finds all PNG and JPG images in the directory and converts them to WebP.
    """
    print(f"--- 🖼️ Surgical Asset Pipeline: Transcoding to WebP ---")
    target_exts = {'.png', '.jpg', '.jpeg'}
    
    optimized_count = 0
    saved_bytes = 0
    
    for root, _, files in os.walk(directory):
        if 'node_modules' in root or '.git' in root or '.venv' in root:
            continue
            
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in target_exts:
                file_path = os.path.join(root, file)
                original_size = os.path.getsize(file_path)
                
                webp_path = os.path.splitext(file_path)[0] + '.webp'
                
                try:
                    img = Image.open(file_path)
                    img.save(webp_path, 'webp', quality=quality)
                    
                    new_size = os.path.getsize(webp_path)
                    savings = original_size - new_size
                    
                    if savings > 0:
                        saved_bytes += savings
                        optimized_count += 1
                        print(f"✅ Converted: {file} -> .webp (Saved {savings / 1024:.2f} KB)")
                        os.remove(file_path) # Remove original to prune size
                    else:
                        # If webp is larger, keep original
                        os.remove(webp_path)
                        print(f"⏭️ Skipped: {file} (WebP was larger)")
                except Exception as e:
                    print(f"❌ Error converting {file}: {e}")

    print("\n--- 🏁 Transcoding Complete ---")
    print(f"Images Optimized: {optimized_count}")
    print(f"Total Space Saved: {saved_bytes / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-convert images to WebP")
    parser.add_argument("dir", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("--quality", type=int, default=80, help="WebP Quality (0-100)")
    args = parser.parse_args()
    
    optimize_images(args.dir, args.quality)
