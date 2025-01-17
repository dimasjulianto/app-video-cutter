# Video Cutter Application

Video Cutter is a powerful tool for splitting long videos into shorter clips using NVIDIA GPU acceleration.

## Features

- Split videos into equal-length clips
- NVIDIA GPU acceleration support
- Real-time progress monitoring
- Customizable clip duration
- Multi-threaded processing
- Support for multiple video formats

## System Requirements

- Windows 10 or later
- NVIDIA GPU with updated drivers
- Minimum 4GB RAM
- 1GB free disk space
- FFmpeg (included in distribution)

## Installation

1. Download the latest release from the releases page
2. Extract all files to your desired location
3. Run `VideoCutter.exe`

## Usage Guide

1. Launch the application
2. Select input video using "Select Input Video" button
3. Choose output folder for the clips
4. Enter a title for the output folder
5. Adjust settings if needed:
   - Processing Threads (1-16)
   - Clip Duration (1-30 seconds)
6. Click "Start Cutting" to begin processing

## Supported Formats

Input formats:
- MP4 (.mp4)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)

Output format:
- MP4 (H.264 codec)

## Troubleshooting

### Common Issues

1. Application won't start
   - Install Microsoft Visual C++ Redistributable
   - Check antivirus settings

2. NVIDIA GPU not detected
   - Update NVIDIA drivers
   - Verify GPU compatibility

3. FFmpeg errors
   - Ensure antivirus isn't blocking FFmpeg
   - Check write permissions in output folder

### Error Messages

- "NVIDIA GPU not found": Update or install NVIDIA drivers
- "Unable to access output folder": Check folder permissions
- "FFmpeg not found": Reinstall application

## Support

For bug reports or feature requests, please open an issue on our GitHub repository.

## License

Copyright (c) 2025. All rights reserved.

## Version History

- v1.0.0 (2025-01-17)
  - Initial release
  - Basic video cutting functionality
  - NVIDIA GPU support
  - Real-time progress monitoring

## Credits

- FFmpeg for video processing capabilities
- PyQt6 for the graphical interface
- NVIDIA for GPU acceleration support
- AUTHOR by Dimas Julianto (facebook/dimasjulianto.id)