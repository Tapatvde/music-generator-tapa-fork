import ctypes
version=ctypes.c_int()
try:
    dll=ctypes.WinDLL('nvcuda.dll');status=dll.cuDriverGetVersion(ctypes.byref(version))
except OSError as error:raise RuntimeError('NVIDIA driver DLL missing. Install/update the driver first.') from error
if status or version.value<13000:raise RuntimeError('The verified ACE binary requires a CUDA 13 compatible NVIDIA driver (R580 or newer). Update the driver first.')
if dll.cuInit(0):raise RuntimeError('NVIDIA CUDA initialization failed.')
count=ctypes.c_int()
if dll.cuDeviceGetCount(ctypes.byref(count)) or count.value<1:raise RuntimeError('No CUDA GPU found.')
major,minor=ctypes.c_int(),ctypes.c_int()
if dll.cuDeviceGetAttribute(ctypes.byref(major),75,0) or dll.cuDeviceGetAttribute(ctypes.byref(minor),76,0):raise RuntimeError('Could not query NVIDIA GPU compatibility.')
if (major.value,minor.value)<(7,5):raise RuntimeError('This CUDA 13 music runtime requires compute capability 7.5 or newer. Older NVIDIA GPUs are not supported by this package.')
print('NVIDIA driver CUDA API verified:',version.value,'; GPU capability:',str(major.value)+'.'+str(minor.value))
