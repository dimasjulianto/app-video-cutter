import atexit
import gc
import json
import logging
import os
import signal
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import psutil

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cleanup_resources():
    """Comprehensive cleanup of system resources"""
    try:
        # Kill any remaining ffmpeg processes
        if os.name == "nt":  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.run(
                ["taskkill", "/F", "/IM", "ffmpeg.exe"],
                capture_output=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:  # Linux/Mac
            subprocess.run(["pkill", "-f", "ffmpeg"], capture_output=True)

        # Clear system cache on Linux
        if os.name != "nt":
            try:
                subprocess.run(["sync"], check=True)  # Sync filesystem buffers
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("3")
            except:
                pass

        # GPU cleanup using nvidia-smi command directly
        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.run(
                ["nvidia-smi", "-r"],
                capture_output=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except:
            pass

        # Clear Python's memory
        gc.collect()

        # Get the current process
        process = psutil.Process(os.getpid())

        # Release memory (Windows and Linux)
        if os.name == "nt":
            import ctypes

            ctypes.windll.psapi.EmptyWorkingSet(process.pid)
        else:
            process.memory_full_info()

        logger.info("System resources cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Register cleanup function to run on program exit
atexit.register(cleanup_resources)

# Register cleanup for system signals
signal.signal(signal.SIGINT, lambda x, y: (cleanup_resources(), exit(0)))
signal.signal(signal.SIGTERM, lambda x, y: (cleanup_resources(), exit(0)))


def get_video_info(input_path):
    """Get video duration and audio info using ffprobe"""
    # Create startupinfo object to hide console window
    startupinfo = None
    if os.name == "nt":  # Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        input_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            startupinfo=startupinfo,  # Use startupinfo to hide console
            creationflags=(
                subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            ),  # Additional for Windows
        )
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])

        # Check if video has audio
        has_audio = any(stream["codec_type"] == "audio" for stream in data["streams"])

        return duration, has_audio
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting video info: {e}")
        raise


def process_clip(args):
    """Process a single clip with audio"""
    input_path, output_path, start_time, clip_duration, encoder = args
    process = None

    try:
        # Create startupinfo object to hide console window
        startupinfo = None
        if os.name == "nt":  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        cmd = [
            "ffmpeg",
            "-ss",
            start_time,
            "-t",
            str(clip_duration),
            "-i",
            input_path,
            "-c:v",
            encoder,  # Use selected encoder
            "-preset",
            (
                "p1" if encoder == "h264_nvenc" else "medium"
            ),  # Adjust preset based on encoder
            "-b:v",
            "5M",  # Video bitrate
            "-c:a",
            "aac",  # Audio codec
            "-b:a",
            "192k",  # Audio bitrate
            "-y",  # Overwrite output files
            "-threads",
            "4",  # Use 4 threads for processing
            "-loglevel",
            "error",  # Minimize ffmpeg output
            output_path,
        ]

        # Add encoder-specific options
        if encoder == "h264_nvenc":
            cmd.extend(["-tune", "hq"])
        elif encoder == "h264_amf":
            cmd.extend(["-quality", "quality"])
        elif encoder == "h264_qsv":
            cmd.extend(["-global_quality", "23"])

        process = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if process.returncode == 0:
            logger.info(f"Successfully created {os.path.basename(output_path)}")
            return True
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Error creating {os.path.basename(output_path)}: {e.stderr.decode()}"
        )
        return False
    finally:
        # Ensure process is properly terminated
        if process:
            try:
                process.terminate()
            except:
                pass


# Update cut_video function in cutting_video.py
def cut_video(
    input_path,
    output_folder,
    max_workers=4,
    clip_duration=3,
    skip_duration=10,
    encoder="h264_nvenc",
    progress_callback=None,
):
    """Main function to cut video into clips"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    duration, has_audio = get_video_info(input_path)
    current_time = 0
    clip_tasks = []

    while current_time < duration:
        remaining_time = duration - current_time
        current_clip_duration = min(clip_duration, remaining_time)

        start_time = str(timedelta(seconds=current_time))
        if "." not in start_time:
            start_time += ".000"

        output_path = os.path.join(output_folder, f"clip_{len(clip_tasks)+1:03d}.mp4")
        # Include encoder in clip task parameters
        clip_tasks.append(
            (input_path, output_path, start_time, current_clip_duration, encoder)
        )

        current_time += current_clip_duration + skip_duration

    total_clips = len(clip_tasks)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            successful_clips = 0
            for index, result in enumerate(
                executor.map(process_clip, clip_tasks), start=1
            ):
                if result:
                    successful_clips += 1
                if progress_callback:
                    progress_callback(
                        index, total_clips, f"Processing clip {index}/{total_clips}"
                    )

            if progress_callback:
                progress_callback(
                    total_clips,
                    total_clips,
                    f"Completed processing {successful_clips} clips",
                )

        return successful_clips == total_clips
    finally:
        cleanup_resources()
