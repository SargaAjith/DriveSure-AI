import os, requests, shutil

# Create negative sample folder
neg_dir = "data/images/train/clean"
neg_lbl = "data/labels/train/clean"
os.makedirs(neg_dir, exist_ok=True)
os.makedirs(neg_lbl, exist_ok=True)

# For each clean car image:
# - Copy image to data/images/train/clean/
# - Create EMPTY .txt label file (no annotations)
#   Empty label = "this image has NO damage"

clean_sources = [
    "clean_car.jpg",   # add all clean car images here
    "0020.jpg",        # the red Acura that fails
]

for img_file in clean_sources:
    if os.path.exists(img_file):
        # Copy image
        dst = os.path.join(neg_dir, img_file)
        shutil.copy(img_file, dst)
        # Create empty label (negative sample)
        lbl = os.path.join(neg_lbl,
              img_file.rsplit(".",1)[0] + ".txt")
        open(lbl, "w").close()
        print(f"Added negative: {img_file}")
