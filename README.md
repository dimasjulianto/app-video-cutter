# Advanced Video Cutter App

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/dimasjulianto/app-video-cutter/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A powerful desktop application for cutting and splitting videos using NVIDIA GPU acceleration. Designed for content creators, editors, and anyone needing to quickly split long videos into shorter segments.

## 🚀 Key Features

- **GPU-Accelerated Processing**: Utilizes NVIDIA GPU for faster video processing
- **Batch Processing**: Split multiple videos simultaneously
- **Multi-threading Support**: Optimized performance with multi-core processing
- **Real-time Progress**: Monitor cutting progress with detailed status updates
- **Custom Duration**: Set your desired clip length (1-30 seconds)
- **Format Support**: Works with MP4, MKV, AVI, MOV, and WMV formats
- **User-Friendly Interface**: Clean and intuitive PyQt6-based GUI
- **Automatic Quality Preservation**: Maintains original video quality

## 💻 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (64-bit)
- **Processor**: Intel Core i3/AMD Ryzen 3 or better
- **Memory**: 4GB RAM
- **Storage**: 1GB available space
- **GPU**: NVIDIA GPU with CUDA support
- **Additional**: Microsoft Visual C++ Redistributable 2019 or newer

### Recommended Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Processor**: Intel Core i5/AMD Ryzen 5 or better
- **Memory**: 8GB RAM
- **Storage**: 2GB available space
- **GPU**: NVIDIA GTX 1060 6GB or better
- **Network**: Broadband internet connection for updates

### Software Dependencies
- NVIDIA Graphics Driver (Version 450.0 or higher)
- FFmpeg (included in distribution)
- Microsoft Visual C++ Redistributable 2019

## 📋 Pre-Installation Checklist

Before installing Video Cutter, ensure:
1. Your system meets the minimum requirements
2. NVIDIA drivers are up to date
3. Microsoft Visual C++ Redistributable 2019 is installed
4. You have administrative privileges (for first-time installation)

## 🎥 Supported Video Formats

### Input Formats
- MP4 (.mp4)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)

### Output Format
- MP4 (H.264 codec)
  - Configurable bitrate
  - Quality preservation
  - Fast encoding with NVENC

## 🛠️ Technical Specifications

### Video Processing
- **Codec Support**: H.264, H.265, VP9
- **Resolution Support**: Up to 4K (3840x2160)
- **Frame Rate**: Maintains source frame rate
- **Bit Rate**: Variable (configurable)
- **Audio**: AAC codec preservation

### Performance
- **Processing Threads**: 1-16 (configurable)
- **GPU Acceleration**: NVIDIA NVENC
- **Memory Usage**: 100MB - 2GB (depending on video size)
- **Temporary Storage**: Uses system temp directory

## 🚨 Hardware Compatibility

### Compatible NVIDIA GPUs
- GeForce GTX 1000 series and newer
- Quadro P series and newer
- All RTX series cards

### Storage Requirements
- **Installation**: 1GB
- **Working Space**: 2x source video size (temporary)
- **Output**: Dependent on source video size

## 📦 What's Included

The installation package includes:
- Video Cutter executable
- FFmpeg binaries
- Required DLLs
- User documentation
- License information

## 💭 Usage Tips

For optimal performance:
1. Close resource-intensive applications
2. Ensure adequate free disk space
3. Update GPU drivers regularly
4. Use SSD for temporary files
5. Monitor GPU temperature during processing

## ⚠️ Important Notes

- Always maintain sufficient free disk space
- Regular GPU driver updates recommended
- Application requires administrative privileges for first run
- Some antivirus software may need configuration
- Internet connection required for updates

## 🔍 Version Information

Current Version: 1.0.0
- Build Date: January 17, 2025
- FFmpeg Version: Latest stable build
- CUDA Support: Version 11.x
- Interface: PyQt6

This application is actively maintained and regularly updated. Check the releases page for the latest version and improvements.