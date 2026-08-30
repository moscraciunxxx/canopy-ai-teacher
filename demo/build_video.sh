#!/bin/zsh
set -euo pipefail

capture_dir="${1:-demo/captures}"
output_path="${2:-demo/output/canopy-devpost-demo.mp4}"
narration_path="demo/renders/canopy-narration.wav"
filter_path="demo/video-filter.txt"

mkdir -p "${output_path:h}"

required_files=(
  "$capture_dir/01-hero.jpg"
  "$capture_dir/02-language-ro.jpg"
  "$capture_dir/02-language-ar.jpg"
  "$capture_dir/03-physics.jpg"
  "$capture_dir/04-biology.jpg"
  "$capture_dir/05-history.jpg"
  "$capture_dir/05-civics.jpg"
  "$capture_dir/06-ethics.jpg"
  "$capture_dir/06-coach.jpg"
  "$capture_dir/07-graph.jpg"
  "$capture_dir/08-learn.jpg"
  "$capture_dir/08-remix.jpg"
  "$capture_dir/08-apply.jpg"
  "$capture_dir/08-outro.jpg"
  "$narration_path"
  "$filter_path"
  "demo/captions.srt"
)

for required_file in "${required_files[@]}"; do
  if [[ ! -f "$required_file" ]]; then
    print -u2 "Missing required demo asset: $required_file"
    exit 1
  fi
done

ffmpeg -y \
  -loop 1 -framerate 30 -t 10.860 -i "$capture_dir/01-hero.jpg" \
  -loop 1 -framerate 30 -t 5.550 -i "$capture_dir/02-language-ro.jpg" \
  -loop 1 -framerate 30 -t 5.550 -i "$capture_dir/02-language-ar.jpg" \
  -loop 1 -framerate 30 -t 12.883208 -i "$capture_dir/03-physics.jpg" \
  -loop 1 -framerate 30 -t 9.740 -i "$capture_dir/04-biology.jpg" \
  -loop 1 -framerate 30 -t 7.481604 -i "$capture_dir/05-history.jpg" \
  -loop 1 -framerate 30 -t 7.481604 -i "$capture_dir/05-civics.jpg" \
  -loop 1 -framerate 30 -t 5.740 -i "$capture_dir/06-ethics.jpg" \
  -loop 1 -framerate 30 -t 5.740 -i "$capture_dir/06-coach.jpg" \
  -loop 1 -framerate 30 -t 13.380 -i "$capture_dir/07-graph.jpg" \
  -loop 1 -framerate 30 -t 4.000 -i "$capture_dir/08-learn.jpg" \
  -loop 1 -framerate 30 -t 4.000 -i "$capture_dir/08-remix.jpg" \
  -loop 1 -framerate 30 -t 4.000 -i "$capture_dir/08-apply.jpg" \
  -loop 1 -framerate 30 -t 4.900 -i "$capture_dir/08-outro.jpg" \
  -i "$narration_path" \
  -filter_complex_script "$filter_path" \
  -map '[video]' -map 14:a:0 \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 \
  -t 100.730 -movflags +faststart "$output_path"

print "Built $output_path"
