# gpu_utils.py
import logging
import platform
import re
import subprocess


class GPUDetector:
    def __init__(self):
        self.available_gpus = []
        self.nvidia_found = False
        self.amd_found = False
        self.intel_found = False

    def detect_gpus(self):
        """Detect available GPUs in the system"""
        system = platform.system().lower()
        self.available_gpus = []  # Reset list before detection

        try:
            # Check for NVIDIA GPUs
            try:
                startupinfo = None
                if system == "windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                nvidia_output = subprocess.check_output(
                    ["nvidia-smi", "-L"],
                    universal_newlines=True,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                )

                for line in nvidia_output.strip().split("\n"):
                    if line:
                        # Extract GPU name using regex
                        match = re.search(r"GPU \d+: (.+?) \(", line)
                        if match:
                            gpu_name = match.group(1)
                            gpu_info = {
                                "name": gpu_name,
                                "type": "NVIDIA",
                                "encoder": "h264_nvenc",
                            }
                            self.available_gpus.append(gpu_info)
                            self.nvidia_found = True
                            logging.info(f"Found NVIDIA GPU: {gpu_name}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.debug(f"No NVIDIA GPU detected: {str(e)}")

            # Check for AMD GPUs on Windows
            if system == "windows":
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    amd_output = subprocess.check_output(
                        [
                            "powershell",
                            "-Command",
                            "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name",
                        ],
                        text=True,
                        startupinfo=startupinfo,
                        
                    )

                    for line in amd_output.strip().split("\n")[1:]:  # Skip header
                        if "AMD" in line.upper() and line.strip():
                            gpu_info = {
                                "name": line.strip(),
                                "type": "AMD",
                                "encoder": "h264_amf",
                            }
                            self.available_gpus.append(gpu_info)
                            self.amd_found = True
                            logging.info(f"Found AMD GPU: {line.strip()}")
                except Exception as e:
                    logging.debug(f"Error detecting AMD GPU: {str(e)}")

            # Check for Intel GPUs
            if system == "windows":
                try:
                    intel_output = subprocess.check_output(
                        [
                            "powershell",
                            "-Command",
                            "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name",
                        ],
                        text=True,
                        startupinfo=startupinfo,
                    )

                    for line in intel_output.strip().split("\n")[1:]:  # Skip header
                        if "INTEL" in line.upper() and line.strip():
                            gpu_info = {
                                "name": line.strip(),
                                "type": "Intel",
                                "encoder": "h264_qsv",
                            }
                            self.available_gpus.append(gpu_info)
                            self.intel_found = True
                            logging.info(f"Found Intel GPU: {line.strip()}")
                except Exception as e:
                    logging.debug(f"Error detecting Intel GPU: {str(e)}")

        except Exception as e:
            logging.error(f"Error in GPU detection: {str(e)}")
            logging.error(f"Failed to detect AMD/Intel GPUs: {str(e)}")

        # Always add CPU as fallback option
        self.available_gpus.append(
            {"name": "CPU (Software Encoding)", "type": "CPU", "encoder": "libx264"}
        )

        return self.available_gpus

    def get_recommended_gpu(self):
        """Get the recommended GPU for video encoding"""
        # Make sure we have detected GPUs
        if not self.available_gpus:
            self.detect_gpus()

        # First preference: NVIDIA
        nvidia_gpu = next(
            (gpu for gpu in self.available_gpus if gpu["type"] == "NVIDIA"), None
        )
        if nvidia_gpu:
            return nvidia_gpu

        # Second preference: AMD
        amd_gpu = next(
            (gpu for gpu in self.available_gpus if gpu["type"] == "AMD"), None
        )
        if amd_gpu:
            return amd_gpu

        # Third preference: Intel
        intel_gpu = next(
            (gpu for gpu in self.available_gpus if gpu["type"] == "Intel"), None
        )
        if intel_gpu:
            return intel_gpu

        # Fallback to CPU
        return next((gpu for gpu in self.available_gpus if gpu["type"] == "CPU"), None)